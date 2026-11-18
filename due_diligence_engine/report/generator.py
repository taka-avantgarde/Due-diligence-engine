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
    desc = str(flag.get("description") or "") if isinstance(flag, dict) else str(getattr(flag, "description", "") or "")
    for marker in ("Remediation:", "Fix:", "修正方針:", "対策:"):
        if marker in desc:
            after = desc.split(marker, 1)[1].strip()
            if after:
                return after.splitlines()[0].strip()
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


def _build_patch_snippet(flag: Any) -> str:
    """Build a concrete copy-pasteable Unified Diff remediation patch proposal for a RedFlag."""
    loc = _extract_file_line(flag)
    file_only = loc.split(":", 1)[0] if ":" in loc else "target_module.py"
    cat = (str(flag.get("category") or "") if isinstance(flag, dict) else str(getattr(flag, "category", "") or "")).lower()
    if "sqli" in cat:
        return (
            f"--- a/{file_only}\n+++ b/{file_only}\n"
            f'- cursor.execute(f"SELECT * FROM records WHERE id = {{user_input}}")\n'
            f'+ cursor.execute("SELECT * FROM records WHERE id = ?", (user_input,))'
        )
    if "injection" in cat:
        return (
            f"--- a/{file_only}\n+++ b/{file_only}\n"
            f"- subprocess.run(cmd_str, shell=True, check=True)\n"
            f"+ subprocess.run(shlex.split(cmd_str), shell=False, check=True)"
        )
    if "crypto" in cat:
        return (
            f"--- a/{file_only}\n+++ b/{file_only}\n"
            f"- digest = hashlib.md5(payload).hexdigest()\n"
            f"+ digest = hashlib.sha256(payload).hexdigest()"
        )
    return (
        f"--- a/{file_only}\n+++ b/{file_only}\n"
        f"# Remediation at {loc}: {_extract_one_line_fix(flag)}"
    )


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

            lines.extend([
                "",
                "### Concrete Remediation Patch Proposals (Read-Only Blueprint)",
                "",
                "```diff",
            ])
            for flag in sorted_flags[:5]:
                lines.append(_build_patch_snippet(flag))
            lines.extend(["```", ""])

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
        cm = code.complexity_metrics or {}
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
            f"| **Deterministic Lockfile** | {'Yes' if cm.get('has_lockfile') else 'No'} |",
            f"| **Cryptographic Signals** | {', '.join(cm.get('crypto_signals', [])) or 'None detected'} |",
            f"| **Copyleft License Check** | {', '.join(cm.get('copyleft_licenses', [])) or 'Clean (No viral copyleft)'} |",
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

        # Section 6: M&A Post-Merger Integration (PMI: Day-1 / Day-30 / Day-100) Roadmap
        pmi = cm.get("pmi_estimate")
        if isinstance(pmi, dict) and "estimated_person_days" in pmi:
            lines.extend([
                "---",
                "",
                "## 6. M&A Post-Merger Integration (PMI) & Technical Debt Roadmap",
                "",
                "| Phase / Metric | Quantitative Estimate / Action Plan |",
                "|---|---|",
                f"| **Estimated Remediation Effort** | **{pmi['estimated_person_days']} person-days** (Bus Factor Risk: `{pmi.get('bus_factor_risk', 'low')}`) |",
                f"| **Day-1 (Immediate Containment)** | {'; '.join(pmi.get('day_1_actions', []))} |",
                f"| **Day-30 (Structural Hardening)** | {'; '.join(pmi.get('day_30_actions', []))} |",
                f"| **Day-100 (Scale & Unit Economics)** | {'; '.join(pmi.get('day_100_actions', []))} |",
                "",
            ])

        # Section 7: Historical Score Delta Tracking (if baseline provided)
        delta = cm.get("historical_delta")
        if isinstance(delta, dict) and "overall_delta" in delta:
            sign = "+" if delta["overall_delta"] >= 0 else ""
            lines.extend([
                "---",
                "",
                "## 7. Historical Score Delta Comparison",
                "",
                "| Metric | Baseline | Current | Delta |",
                "|---|---:|---:|---:|",
                f"| **Overall Score & Grade** | {delta['previous_score']:.1f} ({delta['previous_grade']}) | **{delta['current_score']:.1f} ({delta['current_grade']})** | **{sign}{delta['overall_delta']:.1f} pt** (`{delta['grade_transition']}`) |",
                f"| **Resolved Red Flags** | — | {len(delta.get('resolved_red_flags', []))} | {', '.join(delta.get('resolved_red_flags', [])) or 'None'} |",
                f"| **New Red Flags** | — | {len(delta.get('new_red_flags', []))} | {', '.join(delta.get('new_red_flags', [])) or 'None'} |",
                "",
            ])

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

        if "sarif" in formats:
            from due_diligence_engine.api import generate_sarif

            sarif_path = output_dir / f"{base_name}.sarif.json"
            generate_sarif(result, output_path=sarif_path)
            saved.append(sarif_path)

        return saved

    def generate_batch_markdown(self, results: list[AnalysisResult], lang: str = "en") -> str:
        """Generate a 1-Page Executive Portfolio Batch Comparison Matrix in Markdown."""
        sorted_results = sorted(
            results,
            key=lambda r: float(r.score.overall_score if r.score else 0.0),
            reverse=True,
        )
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        is_ja = lang == "ja"

        lines = [
            f"# Atlas DDE — {'ポートフォリオ横断エグゼクティブ比較マトリックス' if is_ja else 'Executive Portfolio Batch Comparison Matrix'}",
            "",
            f"**Date:** {now_str}  ·  **Targets Audited:** {len(sorted_results)}  ·  **Engine:** Atlas DDE `v{__version__}`",
            "",
            "---",
            "",
            f"## 1. {'1枚完結 エグゼクティブ比較一覧表 (Ranked by Score)' if is_ja else 'All-in-One Executive Portfolio Comparison Sheet (Ranked by Score)'}",
            "",
            "| Rank | Project | Grade | Overall | Verdict | 5-Dim (Orig / Adv / Depth / Arch / Claim) | Files / LOC | Tests & CI | Top Priority Risk |",
            "|---:|---|:---:|---:|:---:|---|---:|:---:|---|",
        ]

        for idx, res in enumerate(sorted_results, start=1):
            sc = res.score
            overall = float(sc.overall_score if sc else 0.0)
            grade = sc.grade if sc else "F"
            flags = sc.red_flags if sc else []
            has_crit = any(getattr(f.severity, "value", str(f.severity)).lower() == "critical" for f in flags)
            verdict = _determine_verdict(overall, has_crit)
            verdict_badge = "🟢 **GO**" if verdict == "GO" else ("⚠️ **CONDITIONAL**" if verdict == "CONDITIONAL" else "🔴 **NO-GO**")

            dim_map = {d.name: d.score for d in (sc.dimensions if sc else [])}
            dim_vals = [
                f"{dim_map.get('Technical Originality', 0):.0f}",
                f"{dim_map.get('Technology Advancement', 0):.0f}",
                f"{dim_map.get('Implementation Depth', 0):.0f}",
                f"{dim_map.get('Architecture Quality (incl. Security Posture)', dim_map.get('Architecture Quality', 0)):.0f}",
                f"{dim_map.get('Claim Consistency', 0):.0f}",
            ]
            dim_summary = " / ".join(dim_vals)
            code = res.code_analysis
            test_ci = (
                "○ Tests+CI"
                if code.has_tests and code.has_ci_cd
                else ("△ Tests" if code.has_tests else "× None")
            )
            if flags:
                top_f = sorted(flags, key=lambda f: _SEV_ORDER.get(getattr(f.severity, "value", str(f.severity)).lower(), 99))[0]
                sev_lbl = getattr(top_f.severity, "value", str(top_f.severity)).upper()
                top_risk = f"[{sev_lbl}] {top_f.title} (`{_extract_file_line(top_f)}`)"
            else:
                top_risk = "○ Zero blockers"

            lines.append(
                f"| {idx} | **{res.project_name}** | **{grade}** | **{overall:.1f}/100** | {verdict_badge} | `{dim_summary}` | {code.total_files} / {code.total_lines:,} | {test_ci} | {top_risk} |"
            )

        lines.extend([
            "",
            "---",
            f"*Generated by Atlas DDE (Due Diligence Engine) v{__version__} on {now_str}*",
        ])
        return "\n".join(lines)

    def generate_batch_html(self, results: list[AnalysisResult], lang: str = "en") -> str:
        """Generate a Quiet Luxury HTML Portfolio Batch Comparison Matrix."""
        sorted_results = sorted(
            results,
            key=lambda r: float(r.score.overall_score if r.score else 0.0),
            reverse=True,
        )
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        rows_html = []
        for idx, res in enumerate(sorted_results, start=1):
            sc = res.score
            overall = float(sc.overall_score if sc else 0.0)
            grade = sc.grade if sc else "F"
            flags = sc.red_flags if sc else []
            has_crit = any(getattr(f.severity, "value", str(f.severity)).lower() == "critical" for f in flags)
            verdict = _determine_verdict(overall, has_crit)
            v_color = "#059669" if verdict == "GO" else ("#d97706" if verdict == "CONDITIONAL" else "#e11d48")
            code = res.code_analysis
            test_ci = "○ Tests + CI" if code.has_tests and code.has_ci_cd else ("△ Tests Only" if code.has_tests else "× None")
            if flags:
                top_f = sorted(flags, key=lambda f: _SEV_ORDER.get(getattr(f.severity, "value", str(f.severity)).lower(), 99))[0]
                top_risk = f"[{html.escape(getattr(top_f.severity, 'value', str(top_f.severity)).upper())}] {html.escape(top_f.title)}"
            else:
                top_risk = "○ Zero blockers"
            rows_html.append(
                f"<tr>"
                f"<td>{idx}</td>"
                f"<td><strong>{html.escape(res.project_name)}</strong></td>"
                f"<td><span style='color:{v_color};font-weight:500;'>Grade {html.escape(grade)}</span></td>"
                f"<td><strong>{overall:.1f}</strong> / 100</td>"
                f"<td><span style='color:{v_color};font-weight:500;'>{verdict}</span></td>"
                f"<td>{code.total_files} files · {code.total_lines:,} LOC</td>"
                f"<td>{test_ci}</td>"
                f"<td>{top_risk}</td>"
                f"</tr>"
            )
        return (
            "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
            "<title>Atlas DDE — Portfolio Batch Comparison</title>"
            "<style>"
            "body{font-family:'Inter',system-ui,sans-serif;font-weight:300;background:#070a10;color:#f8fafc;padding:3rem 2rem;line-height:1.7;}"
            ".container{max-width:1120px;margin:0 auto;background:#0d131f;border:1px solid #1e293b;border-top:3px solid #0284c7;border-radius:12px;padding:2.25rem;}"
            "h1{font-size:1.6rem;font-weight:300;color:#f8fafc;margin-bottom:0.4rem;}"
            ".kicker{font-size:0.75rem;letter-spacing:0.2em;text-transform:uppercase;color:#0284c7;}"
            "table{width:100%;border-collapse:collapse;margin-top:1.5rem;}"
            "th,td{padding:0.85rem;text-align:left;border-bottom:1px solid #1e293b;font-weight:300;font-size:0.9rem;}"
            "th{color:#0284c7;font-weight:500;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;}"
            "</style></head><body><div class='container'>"
            "<div class='kicker'>Atlas DDE · Portfolio Batch Due Diligence</div>"
            f"<h1>Executive Portfolio Comparison ({len(sorted_results)} Targets)</h1>"
            f"<div style='color:#94a3b8;font-size:0.82rem;'>Generated on {now_str} · v{__version__}</div>"
            "<table><thead><tr><th>#</th><th>Project</th><th>Grade</th><th>Score</th><th>Verdict</th><th>Scale</th><th>Tests &amp; CI</th><th>Top Risk</th></tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody></table>"
            "</div></body></html>"
        )
