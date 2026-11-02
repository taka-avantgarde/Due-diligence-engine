"""Fast Repository Governance & SSOT Invariant Verification CLI.

Enforces zero-drift invariants across versioning, pricing, multilingual docs,
and HTML templates in under 0.5 seconds.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

import due_diligence_engine
from due_diligence_engine import config
from due_diligence_engine.ai import providers
from due_diligence_engine.report.pdf_generator import _PDF_I18N

# Ensure config.calculate_token_cost exists as an alias for backwards compatibility
if not hasattr(config, "calculate_token_cost"):
    def _calculate_token_cost(
        model_tier: str,
        input_tokens: int,
        output_tokens: int,
        saas_multiplier: float = 1.0,
    ) -> float:
        """Alias for config.estimate_cost."""
        return config.estimate_cost(model_tier, input_tokens, output_tokens, saas_multiplier)

    config.calculate_token_cost = _calculate_token_cost  # type: ignore[attr-defined]


def run_quick_check(repo_root: Path | None = None) -> tuple[bool, list[str]]:
    """Run fast mechanical SSOT consistency checks across the repository.

    Executes in <0.5 seconds:
    1. Version SSOT: due_diligence_engine.__version__ matches pyproject.toml,
       all 6 READMEs, and scorecard.html.
    2. Template Parity: root templates/scorecard.html does not drift from
       canonical package template.
    3. Model ID Modernity: zero dated model IDs (e.g. claude-*-YYYYMMDD) in package.
    4. Pricing Consistency: config pricing SSOT matches provider cost estimates.
    5. Multilingual PDF Parity: all 14 languages in _PDF_I18N have identical key sets.

    Returns:
        tuple of (is_clean: bool, error_messages: list[str])
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent

    errors: list[str] = []
    version = due_diligence_engine.__version__
    pkg_dir = repo_root / "due_diligence_engine"

    # 1. Version SSOT Check
    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.exists():
        pyproject_text = pyproject_path.read_text(encoding="utf-8")
        m = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
        if not m or m.group(1) != version:
            found_v = m.group(1) if m else "None"
            errors.append(f"pyproject.toml version ({found_v}) != __version__ ({version})")
    else:
        errors.append("pyproject.toml not found")

    readme_files = [
        "README.md",
        "README.ja.md",
        "README.es.md",
        "README.ar.md",
        "README.fr.md",
        "README.de.md",
    ]
    badge_sub = f"version-v{version}"
    for r_name in readme_files:
        r_path = repo_root / r_name
        if not r_path.exists():
            errors.append(f"Missing documentation file: {r_name}")
            continue
        content = r_path.read_text(encoding="utf-8")
        if badge_sub not in content:
            errors.append(f"{r_name} missing version badge for v{version}")
        if f"v{version}" not in content:
            errors.append(f"{r_name} missing text mention of v{version}")

    pkg_scorecard = pkg_dir / "report" / "templates" / "scorecard.html"
    if pkg_scorecard.exists():
        scorecard_txt = pkg_scorecard.read_text(encoding="utf-8")
        if version not in scorecard_txt:
            errors.append(f"scorecard.html template does not contain version {version}")
    else:
        errors.append(f"Canonical scorecard template not found: {pkg_scorecard}")

    # 2. Duplicate root templates/scorecard.html parity/drift check
    root_scorecard = repo_root / "templates" / "scorecard.html"
    if (
        root_scorecard.exists()
        and pkg_scorecard.exists()
        and root_scorecard.read_bytes() != pkg_scorecard.read_bytes()
    ):
        errors.append(
            "Duplicate root templates/scorecard.html has drifted from canonical package template"
        )

    # 3. No dated model IDs in due_diligence_engine/
    dated_model_pattern = re.compile(r"claude-(haiku|sonnet|opus|fable)-\d+-\d{8}")
    if pkg_dir.exists():
        for py_file in pkg_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            match = dated_model_pattern.search(text)
            if match:
                rel = py_file.relative_to(repo_root)
                errors.append(
                    f"Dated model ID '{match.group(0)}' found in {rel}"
                )

    # 4. Pricing SSOT Consistency
    try:
        # Check standard tier estimate consistency between config and providers
        sonnet_cost = config.estimate_cost("sonnet", 200_000, 10_000)
        claude_cost = providers.estimate_provider_cost("claude", 200_000, 10_000)
        if abs(sonnet_cost - claude_cost) > 1e-6:
            errors.append(
                f"Pricing mismatch between config sonnet ({sonnet_cost}) and providers claude ({claude_cost})"
            )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Pricing check exception: {exc}")

    # 5. Multilingual PDF dictionaries parity (all 14 languages)
    if "en" in _PDF_I18N:
        base_keys = set(_PDF_I18N["en"].keys())
        for lang, lang_dict in _PDF_I18N.items():
            diff = base_keys.symmetric_difference(lang_dict.keys())
            if diff:
                errors.append(
                    f"Language '{lang}' key mismatch in _PDF_I18N (diff: {sorted(diff)})"
                )
    else:
        errors.append("_PDF_I18N missing 'en' base dictionary")

    return (len(errors) == 0, errors)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for repository governance and verification."""
    parser = argparse.ArgumentParser(
        prog="due_diligence_engine.maintenance",
        description="Fast repository governance and SSOT verification CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Run invariant checks")
    check_parser.add_argument(
        "--profile",
        choices=["quick", "release"],
        default="quick",
        help="Verification profile: 'quick' (<0.5s SSOT invariants) or 'release' (quick + pytest)",
    )

    # Top-level fallback options if 'check' subcommand is omitted
    parser.add_argument(
        "--profile",
        choices=["quick", "release"],
        default="quick",
        help="Verification profile: 'quick' (<0.5s SSOT invariants) or 'release' (quick + pytest)",
    )

    args = parser.parse_args(argv)
    profile = getattr(args, "profile", "quick")

    start_time = time.perf_counter()
    ok, errors = run_quick_check()
    elapsed = time.perf_counter() - start_time

    if not ok:
        print(f"[FAIL] Repository SSOT check failed ({elapsed:.3f}s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"[OK] Repository SSOT checks passed in {elapsed:.3f}s.")

    if profile == "release":
        print("[INFO] Running comprehensive pytest suite (--profile release)...")
        res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], check=False)
        return res.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
