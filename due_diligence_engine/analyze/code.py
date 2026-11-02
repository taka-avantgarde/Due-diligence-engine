"""AST-based code analysis for detecting API wrappers and real implementation."""

from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path

from due_diligence_engine.ingest.secure_loader import SecureLoader
from due_diligence_engine.models import CodeAnalysisResult, RedFlag, Severity

# Patterns that suggest thin API wrapping rather than real implementation
API_WRAPPER_PATTERNS = [
    r"openai\.",
    r"anthropic\.",
    r"requests\.(get|post|put|delete)\(",
    r"httpx\.(get|post|put|delete)\(",
    r"fetch\(",
    r"axios\.(get|post|put|delete)\(",
    r"\.completions\.create\(",
    r"\.chat\.completions\.",
    r"\.generate\(",
]

# Patterns indicating real algorithmic implementation
REAL_IMPL_PATTERNS = [
    r"class\s+\w+Model",
    r"def\s+(forward|backward|train_step|predict)\(",
    r"torch\.",
    r"tensorflow\.",
    r"numpy\.",
    r"sklearn\.",
    r"def\s+\w+algorithm\(",
]


class _SinglePassMetricsVisitor(ast.NodeVisitor):
    """Single-pass AST visitor computing function count, class count, and branch complexity."""

    def __init__(self) -> None:
        self.functions: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, int]] = []
        self.classes: list[ast.ClassDef] = []
        self._func_stack: list[int] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node)
        enclosing = self._func_stack
        self._func_stack = []
        try:
            self.generic_visit(node)
        finally:
            self._func_stack = enclosing

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_func(node)

    def _enter_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._func_stack.append(0)
        self.generic_visit(node)
        branches = self._func_stack.pop()
        self.functions.append((node, branches))

    def _branch_node(self, node: ast.AST) -> None:
        if self._func_stack:
            self._func_stack[-1] += 1
        self.generic_visit(node)

    visit_If = _branch_node
    visit_For = _branch_node
    visit_AsyncFor = _branch_node
    visit_While = _branch_node
    visit_ExceptHandler = _branch_node
    visit_With = _branch_node
    visit_AsyncWith = _branch_node
    visit_IfExp = _branch_node
    visit_match_case = _branch_node

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if self._func_stack:
            self._func_stack[-1] += len(node.values) - 1
        self.generic_visit(node)


class CodeAnalyzer:
    """Analyzes source code for quality, originality, and red flags."""

    def __init__(self, loader: SecureLoader) -> None:
        self._loader = loader

    def analyze(self) -> CodeAnalysisResult:
        """Run full code analysis across all code files.

        Returns:
            CodeAnalysisResult with metrics, findings, and red flags.
        """
        result = CodeAnalysisResult()
        code_files = self._loader.get_code_files()
        result.total_files = len(code_files)
        # Consistency checks need deployment configs as well as source files.
        result.complexity_metrics["files"] = [{"path": e["path"]} for e in self._loader.manifest]

        api_call_files = 0
        real_impl_files = 0

        for entry in code_files:
            path = entry["path"]
            suffix = Path(path).suffix
            result.languages[suffix] = result.languages.get(suffix, 0) + 1

            try:
                content = self._loader.read_file(path)
            except (FileNotFoundError, UnicodeDecodeError):
                continue

            lines = content.splitlines()
            result.total_lines += len(lines)

            # Check for API wrapper patterns
            has_api_calls = any(
                re.search(pattern, content) for pattern in API_WRAPPER_PATTERNS
            )
            has_real_impl = any(
                re.search(pattern, content) for pattern in REAL_IMPL_PATTERNS
            )

            if has_api_calls:
                api_call_files += 1
            if has_real_impl:
                real_impl_files += 1

            # Python-specific AST analysis
            if suffix == ".py":
                self._analyze_python_ast(path, content, result)

            # Check for test files
            if self._check_tests(path):
                result.has_tests = True

        # Pre-index manifest files for fast lookups
        manifest_paths = [e["path"].replace("\\", "/").lower() for e in self._loader.manifest]

        # Compute API wrapper ratio
        if result.total_files > 0:
            result.api_wrapper_ratio = api_call_files / result.total_files

        # Check for CI/CD
        result.has_ci_cd = self._check_ci_cd(manifest_paths=manifest_paths)

        # Check for documentation
        result.has_documentation = self._check_documentation()

        # Dependency analysis
        result.dependency_count = self._count_dependencies()

        # Generate red flags
        self._generate_red_flags(result, api_call_files, real_impl_files)

        return result

    def _analyze_python_ast(
        self, path: str, content: str, result: CodeAnalysisResult
    ) -> None:
        """Perform AST analysis on Python files using a single-pass visitor."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            result.findings.append(f"Syntax error in {path}")
            return

        visitor = _SinglePassMetricsVisitor()
        visitor.visit(tree)

        # Check function complexity (count branches) & thin wrappers
        for func, branch_count in visitor.functions:
            if branch_count > 15:
                result.findings.append(
                    f"High complexity ({branch_count} branches) in {path}:{func.name}"
                )
            if len(func.body) <= 3:
                source_segment = ast.get_source_segment(content, func)
                if source_segment and any(
                    re.search(p, source_segment) for p in API_WRAPPER_PATTERNS
                ):
                    result.findings.append(
                        f"Thin API wrapper: {func.name} in {path}"
                    )

        # Check for empty classes (possible stubs)
        exception_names = {"Exception", "BaseException", "Error"}
        exception_names.update(name for name in dir(__import__("builtins"))
                               if name.endswith(("Error", "Exception")))
        # Include project exception subclasses even if declared later in the file.
        while True:
            derived = {cls.name for cls in visitor.classes if any(
                (base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else "")
                in exception_names for base in cls.bases)}
            if derived <= exception_names:
                break
            exception_names.update(derived)
        for cls in visitor.classes:
            if cls.name in exception_names:
                continue
            body_stmts = [
                s for s in cls.body
                if not isinstance(s, (ast.Pass, ast.Expr))
                or (isinstance(s, ast.Expr) and not isinstance(s.value, ast.Constant))
            ]
            if len(body_stmts) == 0:
                result.findings.append(f"Empty class {cls.name} in {path} (possible stub)")

    @staticmethod
    def _check_tests(path: str) -> bool:
        parts = path.replace("\\", "/").lower().split("/")
        name = parts[-1]
        return (
            any(part in {"test", "tests", "__tests__", "spec", "specs"} for part in parts[:-1])
            or (name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py")))
            or bool(re.search(r"\.(?:test|spec)\.", name))
        )

    def _check_ci_cd(self, manifest_paths: list[str] | None = None) -> bool:
        """Check if CI/CD configuration exists."""
        ci_indicators = [
            ".github/workflows",
            ".gitlab-ci.yml",
            "jenkinsfile",
            ".circleci/config.yml",
            "azure-pipelines.yml",
            ".travis.yml",
        ]
        paths = manifest_paths if manifest_paths is not None else [
            e["path"].replace("\\", "/").lower() for e in self._loader.manifest
        ]
        for path_norm in paths:
            for indicator in ci_indicators:
                if indicator in path_norm:
                    return True
        return False

    def _check_documentation(self) -> bool:
        """Check if meaningful documentation exists."""
        doc_files = self._loader.get_doc_files()
        has_readme = any("readme" in f["path"].lower() for f in doc_files)
        has_docs_dir = any("docs/" in f["path"].lower() for f in doc_files)
        return has_readme or has_docs_dir

    def _count_dependencies(self) -> int:
        """Count project dependencies from manifest files."""
        dep_count = 0
        dep_files = [
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "Gemfile",
        ]
        for entry in self._loader.manifest:
            name = Path(entry["path"]).name
            if name in dep_files:
                try:
                    content = self._loader.read_file(entry["path"])
                except (FileNotFoundError, UnicodeDecodeError):
                    continue
                try:
                    if name == "package.json":
                        package = json.loads(content)
                        if isinstance(package, dict):
                            for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                                dependencies = package.get(section, {})
                                if isinstance(dependencies, dict):
                                    dep_count += len(dependencies)
                        continue
                    if name == "pyproject.toml":
                        project_config = tomllib.loads(content)
                        project = project_config.get("project", {})
                        if isinstance(project, dict):
                            dependencies = project.get("dependencies", [])
                            if isinstance(dependencies, list):
                                dep_count += sum(isinstance(dep, str) for dep in dependencies)
                            optional = project.get("optional-dependencies", {})
                            if isinstance(optional, dict):
                                dep_count += sum(
                                    sum(isinstance(dep, str) for dep in group)
                                    for group in optional.values() if isinstance(group, list)
                                )
                        tool = project_config.get("tool", {})
                        poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
                        dependencies = poetry.get("dependencies", {}) if isinstance(poetry, dict) else {}
                        if isinstance(dependencies, dict):
                            # Poetry's Python version constraint is not a package dependency.
                            dep_count += sum(name != "python" for name in dependencies)
                        continue
                except (json.JSONDecodeError, tomllib.TOMLDecodeError):
                    # Malformed manifests retain the legacy best-effort estimate.
                    pass
                dep_count += sum(
                    1
                    for line in content.splitlines()
                    if line.strip()
                    and not line.strip().startswith(("#", "//"))
                )
        return dep_count

    def _generate_red_flags(
        self,
        result: CodeAnalysisResult,
        api_call_files: int,
        real_impl_files: int,
    ) -> None:
        """Generate red flags based on analysis findings."""
        # High API wrapper ratio
        if result.api_wrapper_ratio > 0.5 and result.total_files > 5:
            result.red_flags.append(
                RedFlag(
                    category="code_originality",
                    title="High API wrapper ratio",
                    description=(
                        f"{result.api_wrapper_ratio:.0%} of code files contain API "
                        f"calls with minimal custom logic. This suggests the product "
                        f"may be a thin wrapper around third-party APIs."
                    ),
                    severity=Severity.HIGH,
                    evidence=[
                        f"{api_call_files} files with API calls",
                        f"{real_impl_files} files with real implementation patterns",
                    ],
                )
            )

        # No tests
        if not result.has_tests and result.total_files > 10:
            result.red_flags.append(
                RedFlag(
                    category="code_quality",
                    title="No test suite detected",
                    description="No test files found in the repository.",
                    severity=Severity.MEDIUM,
                )
            )

        # No CI/CD
        if not result.has_ci_cd and result.total_files > 10:
            result.red_flags.append(
                RedFlag(
                    category="engineering_maturity",
                    title="No CI/CD pipeline",
                    description="No continuous integration configuration detected.",
                    severity=Severity.MEDIUM,
                )
            )

        # Very small codebase claiming to be a full product
        if result.total_lines < 500 and result.total_files > 0:
            result.red_flags.append(
                RedFlag(
                    category="code_substance",
                    title="Minimal codebase",
                    description=(
                        f"Only {result.total_lines} lines across {result.total_files} files. "
                        f"This is unusually small for a production product."
                    ),
                    severity=Severity.HIGH,
                )
            )
