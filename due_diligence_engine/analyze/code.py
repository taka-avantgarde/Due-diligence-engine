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

# Frontier & production-grade cryptographic primitive signals (Task 1)
CRYPTO_SIGNAL_PATTERNS: dict[str, str] = {
    "ML-KEM / Kyber (FIPS 203)": r"\b(?:ml[-_]?kem|kyber(?:768|1024)?)\b",
    "PQXDH Post-Quantum Handshake": r"\bpqxdh\b",
    "ML-DSA / Dilithium (FIPS 204)": r"\b(?:ml[-_]?dsa|dilithium)\b",
    "Signal Protocol / Double Ratchet": r"\b(?:libsignal|double_ratchet|x3dh)\b",
    "MLS (RFC 9420)": r"\b(?:openmls|mls_group|rfc\s*9420)\b",
    "Authenticated Encryption (AES-GCM / ChaCha20-Poly1305 / Fernet)": r"\b(?:aesgcm|aes[-_]?256[-_]?gcm|chacha20poly1305|Fernet)\b",
    "Elliptic-Curve Signatures (ECDSA P-256 / Ed25519 / X25519)": r"\b(?:SECP256R1|Ed25519|X25519|ec\.generate_private_key)\b",
    "Memory-Hard KDF (Argon2 / Scrypt / PBKDF2)": r"\b(?:argon2|scrypt|PBKDF2HMAC)\b",
}

# Viral copyleft licenses that pose M&A contamination risks (Task 3)
COPYLEFT_LICENSE_PATTERNS: dict[str, str] = {
    "AGPL-3.0": r"\b(?:GNU\s+Affero\s+General\s+Public\s+License|AGPL[-_v]?3(?:\.0)?)\b",
    "GPL-3.0": r"\b(?:GNU\s+General\s+Public\s+License\s+v(?:ersion\s*)?3|GPL[-_v]?3(?:\.0)?)\b",
    "SSPL-1.0": r"\b(?:Server\s+Side\s+Public\s+License|SSPL[-_v]?1(?:\.0)?)\b",
}

LOCKFILE_NAMES = {
    "uv.lock",
    "poetry.lock",
    "pipfile.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "cargo.lock",
    "go.sum",
    "gemfile.lock",
}


def _call_dotted_name(node: ast.AST) -> str:
    """Resolve an AST call target into a dotted identifier string if possible."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


class _SinglePassMetricsVisitor(ast.NodeVisitor):
    """Single-pass AST visitor computing complexity, security sinks, async-blocking, and N+1 / O(N^2) hotspots."""

    def __init__(self) -> None:
        self.functions: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, int]] = []
        self.classes: list[ast.ClassDef] = []
        self._func_stack: list[int] = []
        self._func_name_stack: list[str] = []
        self._async_stack: list[bool] = []
        self._loop_depth_stack: list[int] = []
        self.async_blocking_calls: list[tuple[str, int, str]] = []
        self.nested_loops: list[tuple[str, int, int]] = []
        self.n_plus_one_calls: list[tuple[str, int, str]] = []
        self.security_sinks: list[tuple[str, str, int, str]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(node)
        enclosing = self._func_stack
        self._func_stack = []
        try:
            self.generic_visit(node)
        finally:
            self._func_stack = enclosing

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_func(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_func(node, is_async=True)

    def _enter_func(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_async: bool = False,
    ) -> None:
        self._func_stack.append(0)
        self._func_name_stack.append(node.name)
        self._async_stack.append(is_async)
        self._loop_depth_stack.append(0)
        try:
            self.generic_visit(node)
        finally:
            self._loop_depth_stack.pop()
            self._async_stack.pop()
            self._func_name_stack.pop()
            branches = self._func_stack.pop()
            self.functions.append((node, branches))

    def _branch_node(self, node: ast.AST) -> None:
        if self._func_stack:
            self._func_stack[-1] += 1
        self.generic_visit(node)

    def _loop_node(self, node: ast.AST) -> None:
        if self._func_stack:
            self._func_stack[-1] += 1
        if self._loop_depth_stack:
            self._loop_depth_stack[-1] += 1
            depth = self._loop_depth_stack[-1]
            if depth >= 2:
                fn = self._func_name_stack[-1] if self._func_name_stack else "<module>"
                self.nested_loops.append((fn, getattr(node, "lineno", 1), depth))
        try:
            self.generic_visit(node)
        finally:
            if self._loop_depth_stack:
                self._loop_depth_stack[-1] -= 1

    visit_If = _branch_node
    visit_For = _loop_node
    visit_AsyncFor = _loop_node
    visit_While = _loop_node
    visit_ExceptHandler = _branch_node
    visit_With = _branch_node
    visit_AsyncWith = _branch_node
    visit_IfExp = _branch_node
    visit_match_case = _branch_node

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if self._func_stack:
            self._func_stack[-1] += len(node.values) - 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        dotted = _call_dotted_name(node.func)
        fn = self._func_name_stack[-1] if self._func_name_stack else "<module>"
        lineno = getattr(node, "lineno", 1)

        # 1. Async-blocking calls inside async def
        if self._async_stack and self._async_stack[-1]:
            if dotted in {
                "time.sleep",
                "requests.get",
                "requests.post",
                "requests.put",
                "requests.delete",
                "requests.request",
                "urllib.request.urlopen",
            }:
                self.async_blocking_calls.append((fn, lineno, dotted))

        # 2. N+1 query / network calls inside loop body
        if self._loop_depth_stack and self._loop_depth_stack[-1] >= 1:
            if dotted.endswith((".execute", ".executemany", ".find_one", ".fetchone", ".fetchall")) or dotted in {
                "requests.get",
                "requests.post",
                "httpx.get",
                "httpx.post",
            }:
                self.n_plus_one_calls.append((fn, lineno, dotted))

        # 3. Security sinks (weak crypto, shell=True command injection, unsafe eval, SQL f-string injection)
        if dotted in {"hashlib.md5", "hashlib.sha1"}:
            used_for_sec = True
            for kw in node.keywords:
                if kw.arg == "usedforsecurity" and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                    used_for_sec = False
            if used_for_sec:
                self.security_sinks.append(("weak_crypto", fn, lineno, dotted))
        elif dotted == "os.system":
            self.security_sinks.append(("command_injection", fn, lineno, dotted))
        elif dotted.startswith("subprocess.") and any(
            kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in node.keywords
        ):
            self.security_sinks.append(("command_injection", fn, lineno, f"{dotted}(shell=True)"))
        elif dotted == "eval":
            self.security_sinks.append(("unsafe_eval", fn, lineno, "eval()"))
        elif dotted.endswith((".execute", ".executemany")) and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, (ast.JoinedStr, ast.BinOp)):
                self.security_sinks.append(("sql_injection", fn, lineno, dotted))

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
        result.complexity_metrics["crypto_signals"] = []
        result.complexity_metrics["async_blocking"] = []
        result.complexity_metrics["nested_loop_hotspots"] = []
        result.complexity_metrics["n_plus_one_hotspots"] = []
        result.complexity_metrics["security_sinks"] = []
        result.complexity_metrics["copyleft_licenses"] = []
        result.complexity_metrics["has_lockfile"] = False
        result.complexity_metrics["multilang_metrics"] = {}

        api_call_files = 0
        real_impl_files = 0
        detected_crypto: set[str] = set()

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

            # Task 1: Detect cryptographic signals across all code files
            for sig_name, sig_pat in CRYPTO_SIGNAL_PATTERNS.items():
                if re.search(sig_pat, content, re.IGNORECASE):
                    detected_crypto.add(sig_name)

            # Python-specific AST analysis (Tasks 1 & 2)
            if suffix == ".py":
                self._analyze_python_ast(path, content, result)
            elif suffix in {".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".swift", ".dart", ".kt"}:
                self._analyze_multilang(path, suffix, content, result)

            # Check for test files
            if self._check_tests(path):
                result.has_tests = True

        result.complexity_metrics["crypto_signals"] = sorted(detected_crypto)

        # Pre-index manifest files for fast lookups
        manifest_paths = [e["path"].replace("\\", "/").lower() for e in self._loader.manifest]

        # Task 3: Audit M&A license contamination (AGPL/GPL/SSPL) & lockfiles
        self._audit_licenses_and_lockfiles(result, manifest_paths)

        # Compute API wrapper ratio
        if result.total_files > 0:
            result.api_wrapper_ratio = api_call_files / result.total_files

        # Check for CI/CD
        result.has_ci_cd = self._check_ci_cd(manifest_paths=manifest_paths)

        # Check for documentation
        result.has_documentation = self._check_documentation()

        # Dependency analysis
        result.dependency_count = self._count_dependencies(result=result)

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

        is_test = self._check_tests(path)

        # Record Task 1 & Task 2 AST telemetry for production files
        if not is_test:
            for fn, lineno, call_name in visitor.async_blocking_calls:
                loc = f"{path}:{lineno}"
                result.complexity_metrics["async_blocking"].append(
                    {"file_line": loc, "function": fn, "call": call_name}
                )
                result.findings.append(
                    f"Async-blocking I/O call '{call_name}' inside async def '{fn}' at {loc} "
                    f"(use asyncio.sleep / httpx.AsyncClient / asyncio.to_thread)"
                )
            for fn, lineno, depth in visitor.nested_loops:
                loc = f"{path}:{lineno}"
                result.complexity_metrics["nested_loop_hotspots"].append(
                    {"file_line": loc, "function": fn, "depth": depth}
                )
                if depth >= 3:
                    result.findings.append(
                        f"O(N^{depth}) deep nested loop in {loc} ({fn}) — pre-index with dict/set for O(1) lookup"
                    )
            for fn, lineno, call_name in visitor.n_plus_one_calls:
                loc = f"{path}:{lineno}"
                result.complexity_metrics["n_plus_one_hotspots"].append(
                    {"file_line": loc, "function": fn, "call": call_name}
                )
                result.findings.append(
                    f"Potential N+1 query/network call '{call_name}' inside loop at {loc} ({fn}) — batch or prefetch outside loop"
                )
            for sink_type, fn, lineno, call_name in visitor.security_sinks:
                loc = f"{path}:{lineno}"
                result.complexity_metrics["security_sinks"].append(
                    {"type": sink_type, "file_line": loc, "function": fn, "call": call_name}
                )
                if sink_type == "sql_injection":
                    result.red_flags.append(
                        RedFlag(
                            category="security_sqli",
                            title=f"SQL string interpolation in {loc}",
                            description=(
                                f"Dynamic SQL string formatting passed to {call_name} in {fn} ({loc}). "
                                f"Remediation: Use parameterized queries (? / :param) instead of f-strings or % formatting."
                            ),
                            severity=Severity.CRITICAL,
                            file_path=path,
                            line_number=lineno,
                            evidence=[f"{loc} -> {call_name}"],
                        )
                    )
                elif sink_type == "command_injection":
                    result.red_flags.append(
                        RedFlag(
                            category="security_injection",
                            title=f"Shell command execution sink in {loc}",
                            description=(
                                f"Shell execution via {call_name} in {fn} ({loc}). "
                                f"Remediation: Pass argument list with shell=False and validate inputs."
                            ),
                            severity=Severity.HIGH,
                            file_path=path,
                            line_number=lineno,
                            evidence=[f"{loc} -> {call_name}"],
                        )
                    )
                elif sink_type == "weak_crypto":
                    result.red_flags.append(
                        RedFlag(
                            category="security_crypto",
                            title=f"Weak cryptographic hash ({call_name}) in {loc}",
                            description=(
                                f"Collision-vulnerable hash {call_name} used in {fn} ({loc}). "
                                f"Remediation: Upgrade to SHA-256 / SHA-3 or pass usedforsecurity=False if non-cryptographic."
                            ),
                            severity=Severity.MEDIUM,
                            file_path=path,
                            line_number=lineno,
                            evidence=[f"{loc} -> {call_name}"],
                        )
                    )

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

    def _analyze_multilang(
        self, path: str, suffix: str, content: str, result: CodeAnalysisResult
    ) -> None:
        """Task 5: Static structural and reliability inspection for TS/JS, Rust, Go, Swift, Dart, and Kotlin."""
        if self._check_tests(path):
            return
        metrics = result.complexity_metrics.setdefault("multilang_metrics", {})
        lang_bucket = metrics.setdefault(suffix, {"files": 0, "functions": 0, "reliability_warnings": 0})
        lang_bucket["files"] += 1

        if suffix == ".rs":
            lang_bucket["functions"] += len(re.findall(r"\bfn\s+\w+", content))
            unwraps = len(re.findall(r"\.(?:unwrap|expect)\s*\(", content))
            if unwraps > 5:
                lang_bucket["reliability_warnings"] += unwraps
                result.findings.append(
                    f"Rust panic surface: {unwraps} .unwrap()/.expect() calls in {path} (replace with ? / Result propagation)"
                )
        elif suffix in {".ts", ".tsx", ".js", ".jsx"}:
            lang_bucket["functions"] += len(re.findall(r"\b(?:function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\()", content))
            any_usages = len(re.findall(r":\s*any\b", content))
            if any_usages > 5:
                lang_bucket["reliability_warnings"] += any_usages
                result.findings.append(
                    f"TypeScript type-safety erosion: {any_usages} ': any' annotations in {path}"
                )
        elif suffix == ".go":
            lang_bucket["functions"] += len(re.findall(r"\bfunc\s+", content))
            ignored_errs = len(re.findall(r"_\s*=\s*\w+\(", content))
            if ignored_errs > 3:
                lang_bucket["reliability_warnings"] += ignored_errs
                result.findings.append(
                    f"Go ignored error returns ({ignored_errs} occurrences) in {path}"
                )
        elif suffix in {".swift", ".kt", ".dart"}:
            lang_bucket["functions"] += len(re.findall(r"\b(?:func|fun)\s+\w+", content))
            force_unwraps = len(re.findall(r"\btry!|!!", content))
            if force_unwraps > 3:
                lang_bucket["reliability_warnings"] += force_unwraps
                result.findings.append(
                    f"Mobile force-unwrap crash surface ({force_unwraps} occurrences) in {path}"
                )

    def _audit_licenses_and_lockfiles(
        self, result: CodeAnalysisResult, manifest_paths: list[str]
    ) -> None:
        """Task 3: Audit M&A copyleft contamination (AGPL/GPL/SSPL) and deterministic lockfiles."""
        basenames = {Path(p).name for p in manifest_paths}
        result.complexity_metrics["has_lockfile"] = bool(basenames & LOCKFILE_NAMES)

        copyleft_found: set[str] = set()
        license_targets = {"pyproject.toml", "package.json", "cargo.toml", "license", "license.md", "license.txt", "copying"}
        for entry in self._loader.manifest:
            rel_path = entry["path"]
            if Path(rel_path).name.lower() not in license_targets:
                continue
            try:
                text = self._loader.read_file(rel_path)
            except (FileNotFoundError, UnicodeDecodeError):
                continue
            for lic_name, pat in COPYLEFT_LICENSE_PATTERNS.items():
                if re.search(pat, text, re.IGNORECASE):
                    copyleft_found.add(f"{lic_name} ({rel_path})")

        if copyleft_found:
            sorted_copyleft = sorted(copyleft_found)
            result.complexity_metrics["copyleft_licenses"] = sorted_copyleft
            result.red_flags.append(
                RedFlag(
                    category="legal_ip_license",
                    title="Viral copyleft license detected (M&A IP contamination risk)",
                    description=(
                        f"Detected restrictive copyleft license(s): {', '.join(sorted_copyleft)}. "
                        f"Remediation: Isolate behind network boundary or replace with permissive Apache-2.0 / MIT / BSD equivalents prior to M&A closing."
                    ),
                    severity=Severity.HIGH,
                    evidence=sorted_copyleft,
                )
            )

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

    def _count_dependencies(self, result: CodeAnalysisResult | None = None) -> int:
        """Count project dependencies and extract CycloneDX SBOM components from manifest files."""
        dep_count = 0
        sbom_components: list[dict[str, str]] = []
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
                                    for pkg_name, ver_spec in dependencies.items():
                                        ver_str = str(ver_spec).lstrip("^~>=< ") or "latest"
                                        sbom_components.append({
                                            "type": "library",
                                            "name": str(pkg_name),
                                            "version": ver_str,
                                            "purl": f"pkg:npm/{pkg_name}@{ver_str}",
                                            "manifest": entry["path"],
                                        })
                        continue
                    if name == "pyproject.toml":
                        project_config = tomllib.loads(content)
                        project = project_config.get("project", {})
                        if isinstance(project, dict):
                            dependencies = project.get("dependencies", [])
                            if isinstance(dependencies, list):
                                dep_count += sum(isinstance(dep, str) for dep in dependencies)
                                for dep in dependencies:
                                    if isinstance(dep, str):
                                        m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?\s*([><=~!]+.+)?", dep.strip())
                                        if m:
                                            pkg_n = m.group(1)
                                            pkg_v = (m.group(2) or "unspecified").lstrip("><=~! ")
                                            sbom_components.append({
                                                "type": "library",
                                                "name": pkg_n,
                                                "version": pkg_v,
                                                "purl": f"pkg:pypi/{pkg_n.lower()}@{pkg_v}",
                                                "manifest": entry["path"],
                                            })
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
                            dep_count += sum(pkg_k != "python" for pkg_k in dependencies)
                            for pkg_k, ver_v in dependencies.items():
                                if pkg_k != "python":
                                    ver_s = str(ver_v).lstrip("^~>=< ")
                                    sbom_components.append({
                                        "type": "library",
                                        "name": str(pkg_k),
                                        "version": ver_s,
                                        "purl": f"pkg:pypi/{str(pkg_k).lower()}@{ver_s}",
                                        "manifest": entry["path"],
                                    })
                        continue
                except (json.JSONDecodeError, tomllib.TOMLDecodeError):
                    # Malformed manifests retain the legacy best-effort estimate.
                    pass
                for line in content.splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith(("#", "//")):
                        dep_count += 1
                        if name == "requirements.txt":
                            m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?\s*([><=~!]+.+)?", stripped)
                            if m:
                                pkg_n = m.group(1)
                                pkg_v = (m.group(2) or "unspecified").lstrip("><=~! ")
                                sbom_components.append({
                                    "type": "library",
                                    "name": pkg_n,
                                    "version": pkg_v,
                                    "purl": f"pkg:pypi/{pkg_n.lower()}@{pkg_v}",
                                    "manifest": entry["path"],
                                })
        if result is not None:
            result.complexity_metrics["sbom_components"] = sbom_components
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
