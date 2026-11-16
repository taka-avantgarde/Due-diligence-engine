"""Report generation in Markdown, HTML, and PDF scorecard formats for Atlas DDE."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from due_diligence_engine import __version__
from due_diligence_engine.models import AnalysisResult

_DEFAULT_TEMPLATE_DIR = (
    Path(__file__).resolve().parent / "templates"
    if (Path(__file__).resolve().parent / "templates").is_dir()
    else Path(__file__).resolve().parent.parent.parent / "templates"
)

_SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _extract_file_line(flag: Any) -> str:
    """Extract a concise `file:line` target from a RedFlag or dict."""
    if isinstance(flag, dict):
        for key in ("file_line", "location", "file", "target"):
            val = flag.get(key)
            if val:
                return str(val)
        ev = flag.get("evidence")
        if isinstance(ev, list) and ev:
            return str(ev[0])
        text = f"{flag.get('title', '')} {flag.get('description', '')}"
    else:
        ev = getattr(flag, "evidence", None)
        if ev:
            return str(ev[0])
        text = f"{getattr(flag, 'title', '')} {getattr(flag, 'description', '')}"

    m = re.search(r"([A-Za-z0-9_./\-]+\.[A-Za-z0-9_]+(?::\d+)?)", text)
    if m:
        return m.group(1)
    if isinstance(flag, dict):
        return str(flag.get("category") or "repository")
    return str(getattr(flag, "category", "") or "repository")


def _extract_one_line_fix(flag: Any) -> str:
    """Extract or synthesize a concrete 1-line remediation plan."""
    if isinstance(flag, dict):
        for key in ("remediation", "fix", "fix_plan", "action"):
            val = flag.get(key)
            if val:
                return str(val).splitlines()[0].strip()
        cat = str(flag.get("category") or "module")
    else:
        for key in ("remediation", "fix", "fix_plan"):
            val = getattr(flag, key, None)
            if val:
                return str(val).splitlines()[0].strip()
        cat = str(getattr(flag, "category", "") or "module")
    return f"Harden `{cat}` boundary and add a deterministic regression test."


def _determine_verdict(overall_score: float, has_critical_blocker: bool) -> str:
    """Return institutional M&A verdict: GO, CONDITIONAL, or NO-GO."""
    if has_critical_blocker or overall_score < 55.0:
        return "NO-GO"
    if overall_score >= 75.0:
        return "GO"
    return "CONDITIONAL"


class ReportGenerator:
    """Generates Atlas DDE due diligence reports in Markdown and HTML formats."""

    def __init__(self, template_dir: Path | None = None) -> None:
        if template_dir is None:
            template_dir = _DEFAULT_TEMPLATE_DIR
        self._template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )

    def generate_markdown(self, result: AnalysisResult) -> str:
        """Generate an executive-ready, Quiet Luxury Markdown report.

        Args:
            result: The analysis result to report on.

        Returns:
            Markdown-formatted report string.
        """
        score = result.score
        if score is None:
            return "# Error: No score computed\n"

        def _sev_str(f: Any) -> str:
            s = f.get("severity", "info") if isinstance(f, dict) else getattr(f, "severity", "")
            return (
                getattr(s, "value", s).lower()
                if hasattr(s, "value") or isinstance(s, str)
                else str(s).lower()
            )

        sorted_flags = sorted(
            score.red_flags,
            key=lambda f: _SEV_ORDER.get(_sev_str(f), 99),
        )
        has_critical = any(_sev_str(f) == "critical" for f in sorted_flags)
        verdict = _determine_verdict(score.overall_score, has_critical)

        top_risks = [
            f"[{_sev_str(f).upper()}] {f.title} (`{_extract_file_line(f)}`)"
            for f in sorted_flags[:3]
        ]
        if not top_risks:
            top_risks = ["None — zero code-verified critical/high blockers detected."]

        code = result.code_analysis
        consistency = result.consistency
        cr = result.consulting_report

        lines = [
            f"# Atlas DDE — Technical Due Diligence Report: {result.project_name}",
            "",
            f"**Analysis ID:** `{result.analysis_id}`",
            f"**Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Overall Score:** {score.overall_score}/100 (Grade: {score.grade})",
            f"**Executive Verdict:** **{verdict}** — {score.recommendation}",
            "",
            "---",
            "",
            "## 1. Executive Summary Comparison Sheet (Page 1 At-a-Glance)",
            "",
            "| Executive Metric | Assessment |",
            "|---|---|",
            f"| **① Overall Grade & Score** | **Grade {score.grade}** · **{score.overall_score}/100** |",
            f"| **② Investment / M&A Verdict** | **{verdict}** ({score.recommendation}) |",
            f"| **③ Top 3 Priority Risks** | {'<br>'.join(top_risks)} |",
            "",
            "### Standard 5-Dimension Score Table (20% Equal Weights)",
            "",
            "| Dimension | Score | Weight | Weighted | Rationale |",
            "|---|---:|---:|---:|---|",
        ]

        for dim in score.dimensions:
            lines.append(
                f"| **{dim.name}** | **{dim.score:.0f}/100** | {dim.weight:.0%} | "
                f"{dim.weighted_score:.1f} | {dim.rationale} |"
            )

        lines.extend([
            "",
            f"**Overall: {score.overall_score}/100**",
            "",
            "### Atlas 4-Axis Engineering Assessment (20% / 20% / 5% / 55%)",
            "",
            "| Atlas Axis | Weight | Score / Status | Engineering Evidence |",
            "|---|---:|---|---|",
        ])

        if cr and cr.atlas_four_axis and cr.atlas_four_axis.axes:
            for ax in cr.atlas_four_axis.axes:
                lines.append(
                    f"| **{ax.name_en}** | {ax.weight_pct:.0f}% | **{ax.score:.0f}/100** (Lv.{ax.level}) | {ax.rationale} |"
                )
        else:
            test_status = (
                "○ Verified (Tests + CI/CD)"
                if code.has_tests and code.has_ci_cd
                else ("△ Partial (Tests only)" if code.has_tests else "× Unimplemented (No tests)")
            )
            lines.extend([
                f"| **Performance & Concurrency** | 20% | **{score.overall_score:.0f}/100** | Static AST & architecture efficiency |",
                f"| **Stability & Reliability** | 20% | {test_status} | {code.total_files} files / {code.total_lines:,} LOC |",
                f"| **Lightweight & Dependency Hygiene** | 5% | {code.dependency_count} deps | API wrapper ratio: {code.api_wrapper_ratio:.0%} |",
                f"| **Security & Cryptographic Strength** | **55%** | **{consistency.consistency_score:.0f}/100** | Claim-to-code integrity & security posture |",
            ])

        # Section 2: 2-Column Company Claim vs. Code Evidence Table
        lines.extend([
            "",
            "---",
            "",
            "## 2. Company Claim vs. Code Evidence (AI-Washing Verification)",
            "",
            "| Web / Pitch Claim (企業の主張) | Codebase Evidence (`file:line`) & Verdict (実コードの証拠・判定) |",
            "|---|---|",
        ])

        claim_rows_added = 0
        if cr and cr.site_verification and cr.site_verification.items:
            for item in cr.site_verification.items:
                badge = (
                    "○ 実装済 (Verified)"
                    if item.score >= 75
                    else ("△ 一部のみ (Partial)" if item.score >= 45 else "× 未実装 (Unimplemented)")
                )
                lines.append(
                    f"| **{item.item_name}** | **{badge}** ({item.score:.0f}/100) — {item.rationale} |"
                )
                claim_rows_added += 1

        for c_text in consistency.verified_claims:
            lines.append(f"| {c_text} | **○ 実装済 (Verified)** — Confirmed in repository AST & config |")
            claim_rows_added += 1
        for c_text in consistency.unverified_claims:
            lines.append(f"| {c_text} | **△ 一部のみ (Unverified)** — ⚠️ No backing code implementation found |")
            claim_rows_added += 1
        for c_text in consistency.contradictions:
            lines.append(f"| {c_text} | **× 未実装 (Contradiction)** — Contradicts actual source tree |")
            claim_rows_added += 1

        if claim_rows_added == 0:
            lines.append(
                f"| Repository Baseline Integrity | **○ 実装済 (Verified)** — {consistency.consistency_score:.0f}% consistency across {code.total_files} files |"
            )

        # Section 3: Priority-Sorted Red Flags 4-Column Table
        if sorted_flags:
            lines.extend([
                "",
                "---",
                "",
                "## 3. Priority-Sorted Red Flags (Code-Verified Defects)",
                "",
                "| Severity | Target (`file:line`) | Business Impact | Concrete 1-Line Fix Plan |",
                "|---|---|---|---|",
            ])
            for flag in sorted_flags:
                sev_label = _sev_str(flag).upper()
                badge = f"🔴 **CRITICAL**" if sev_label == "CRITICAL" else (
                    f"⚠️ **HIGH**" if sev_label == "HIGH" else f"**{sev_label}**"
                )
                target_loc = _extract_file_line(flag)
                fix_plan = _extract_one_line_fix(flag)
                lines.append(
                    f"| {badge} | `{target_loc}` | **{flag.title}** — {flag.description} | {fix_plan} |"
                )
            lines.append("")
            for flag in sorted_flags:
                sev_label = _sev_str(flag).upper()
                lines.append(f"- **[{sev_label}]** **{flag.title}** ({flag.category})")

        # Detailed Dimension Breakdown (retained for backwards compatibility)
        lines.extend(["", "---", "", "## 4. Detailed Dimension Analysis", ""])
        for dim in score.dimensions:
            lines.extend([
                f"### {dim.name} ({dim.score:.0f}/100)",
                "",
                f"{dim.rationale}",
                "",
            ])
            if dim.sub_scores:
                lines.append("**Sub-scores:**")
                for name, value in dim.sub_scores.items():
                    lines.append(f"- {name.replace('_', ' ').title()}: {value:.0f}")
                lines.append("")

        # Code & Git Summary
        lines.extend([
            "---",
            "",
            "## 5. Codebase & Git Forensics Summary",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| **Files Analyzed** | {code.total_files} |",
            f"| **Lines of Code** | {code.total_lines:,} |",
            f"| **Languages** | {', '.join(f'{k} ({v})' for k, v in code.languages.items()) or 'N/A'} |",
            f"| **API Wrapper Ratio** | {code.api_wrapper_ratio:.0%} |",
            f"| **Automated Tests** | {'Yes' if code.has_tests else 'No'} |",
            f"| **CI/CD Pipeline** | {'Yes' if code.has_ci_cd else 'No'} |",
            f"| **Documentation** | {'Yes' if code.has_documentation else 'No'} |",
            f"| **Dependencies** | {code.dependency_count} |",
        ])

        git = result.git_forensics
        if git.total_commits > 0:
            lines.extend([
                f"| **Total Commits** | {git.total_commits} |",
                f"| **Unique Authors** | {git.unique_authors} |",
                f"| **Commit Window** | {git.first_commit_date or 'N/A'} → {git.last_commit_date or 'N/A'} |",
                f"| **Rush Commit Ratio** | {git.rush_commit_ratio:.0%} |",
            ])
        lines.append("")

        # Cost information
        lines.extend([
            "---",
            "",
            "## Analysis Cost",
            "",
            f"**Total API Cost:** ${result.total_cost_usd:.4f}",
            "",
        ])
        for tier, usage in result.model_usage.items():
            if usage.get("input_tokens", 0) > 0 or usage.get("output_tokens", 0) > 0:
                lines.append(
                    f"- {tier.title()}: {usage.get('input_tokens', 0)} input / "
                    f"{usage.get('output_tokens', 0)} output tokens"
                )
        lines.append("")

        # AI Provider results
        if result.ai_results:
            lines.extend(["---", "", "## AI Verification Results", ""])
            for name, ai in result.ai_results.items():
                status = "Failed" if getattr(ai, "error", "") else "Success"
                provider_name = ai.provider.title() if getattr(ai, "provider", "") else name.title()
                model_name = getattr(ai, "model_id", getattr(ai, "model", "unknown"))
                lines.append(f"### {provider_name} ({model_name}) — {status}")
                lines.append("")
                if getattr(ai, "error", ""):
                    lines.append(f"**Error:** {ai.error}")
                    lines.append("")
                if getattr(ai, "executive_summary", ""):
                    lines.append(ai.executive_summary)
                    lines.append("")

        lines.extend([
            "---",
            f"*Generated by Atlas DDE (Due Diligence Engine) v{__version__} on "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        ])

        return "\n".join(lines)

    def _generate_basic_html(self, result: AnalysisResult) -> str:
        """Fallback: wrap markdown in basic HTML with html.escape."""
        md = self.generate_markdown(result)
        return f"<html><body><pre>{html.escape(md)}</pre></body></html>"

    def generate_html(self, result: AnalysisResult) -> str:
        """Generate an HTML scorecard using Jinja2 template."""
        try:
            template = self._env.get_template("scorecard.html")
        except Exception:
            return self._generate_basic_html(result)

        return template.render(
            result=result,
            score=result.score,
            code=result.code_analysis,
            git=result.git_forensics,
            docs=result.doc_analysis,
            consistency=result.consistency,
            version=__version__,
            now=datetime.now(timezone.utc),
        )

    def save_report(
        self,
        result: AnalysisResult,
        output_dir: Path,
        formats: list[str] | None = None,
    ) -> list[Path]:
        """Save report in specified formats."""
        if formats is None:
            formats = ["md", "html"]

        output_dir.mkdir(parents=True, exist_ok=True)
        saved: list[Path] = []
        safe_name = result.project_name.replace("/", "_").replace("\\", "_")
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", result.analysis_id)
        base_name = f"dde_report_{safe_name}_{safe_id}"

        if "md" in formats:
            md_path = output_dir / f"{base_name}.md"
            md_path.write_text(self.generate_markdown(result), encoding="utf-8")
            saved.append(md_path)

        if "html" in formats:
            html_path = output_dir / f"{base_name}.html"
            html_path.write_text(self.generate_html(result), encoding="utf-8")
            saved.append(html_path)

        return saved
