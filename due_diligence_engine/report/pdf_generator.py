"""Professional PDF report generator for due diligence reports.

Generates multi-page PDF reports using ReportLab with:
- Cover page with overall score and grade
- Executive summary
- Dimension breakdown table with scores
- Red flags section with severity indicators
- Architecture and code analysis findings
- Purge certificate page (if applicable)
- NDA compliance footer on every page
- Japanese language support via CID fonts

IMPORTANT: No source code is ever included in the PDF output.
Only findings, scores, and recommendations are reported.
"""

from __future__ import annotations

import copy
import io
import logging
import re
import xml.sax.saxutils
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle, Polygon
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from due_diligence_engine.models import AIProviderResult, AnalysisResult, ConsultingReport, PurgeCertificate, Severity

logger = logging.getLogger(__name__)

# Register CID fonts for Japanese support
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))        # Simplified Chinese (zh)
pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))  # Korean (ko)

# Bundled Noto TTF fonts (OFL) for scripts not covered by the built-in CID
# fonts or Helvetica/WinAnsi: Vietnamese (Latin diacritics beyond WinAnsi)
# and Thai. Registration is best-effort — if a font file is missing the
# language simply falls back to Helvetica rather than crashing.
_FONT_DIR = Path(__file__).resolve().parent / "fonts"
_TTF_LANG_FONTS: dict[str, tuple[str, str]] = {}


def _register_ttf(name: str, filename: str) -> bool:
    try:
        pdfmetrics.registerFont(TTFont(name, str(_FONT_DIR / filename)))
        return True
    except Exception as exc:  # noqa: BLE001 — missing/corrupt font must not break import
        logger.warning("Could not register TTF font %s (%s): %s", name, filename, exc)
        return False


if _register_ttf("NotoSansVI", "NotoSans-Regular.ttf"):
    _TTF_LANG_FONTS["vi"] = ("NotoSansVI", "NotoSansVI")
if _register_ttf("NotoSansThai", "NotoSansThai-Regular.ttf"):
    _TTF_LANG_FONTS["th"] = ("NotoSansThai", "NotoSansThai")
if _register_ttf("NotoNaskhArabic", "NotoNaskhArabic-Regular.ttf"):
    _TTF_LANG_FONTS["ar"] = ("NotoNaskhArabic", "NotoNaskhArabic")

# Arabic shaping/bidi: reportlab renders strings left-to-right with no contextual
# shaping, so Arabic text must be pre-shaped (joined presentation forms) and
# reordered (bidi → visual order) before drawing. Optional deps; if missing,
# Arabic falls back to unshaped text rather than breaking.
try:
    import arabic_reshaper as _arabic_reshaper
    try:
        from bidi import get_display as _bidi_get_display
    except ImportError:
        from bidi.algorithm import get_display as _bidi_get_display
    _HAS_ARABIC = True
except Exception:  # pragma: no cover - optional at import time
    _arabic_reshaper = None  # type: ignore[assignment]
    _bidi_get_display = None  # type: ignore[assignment]
    _HAS_ARABIC = False


def _reshape_ar(text: str) -> str:
    """Shape + bidi-reorder Arabic text for an LTR-only renderer (reportlab).

    Non-Arabic strings pass through essentially unchanged (reshaper only touches
    Arabic letters; bidi of pure-LTR text is the identity).
    """
    if not _HAS_ARABIC or not isinstance(text, str) or not text:
        return text
    try:
        return _bidi_get_display(_arabic_reshaper.reshape(text))
    except Exception:  # noqa: BLE001 — never let shaping crash report generation
        return text


def _deep_reshape_inplace(obj):
    """Recursively shape every Arabic string inside a pydantic model / list / dict."""
    from pydantic import BaseModel

    if isinstance(obj, BaseModel):
        for name in obj.__class__.model_fields:
            try:
                setattr(obj, name, _deep_reshape_inplace(getattr(obj, name, None)))
            except Exception:  # noqa: BLE001 — frozen/validated fields: skip
                pass
        return obj
    if isinstance(obj, list):
        return [_deep_reshape_inplace(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _deep_reshape_inplace(v) for k, v in obj.items()}
    if isinstance(obj, str):
        return _reshape_ar(obj)
    return obj


def _esc(text: Any) -> str:
    """Escape dynamic text for safe inclusion in ReportLab Paragraph markup."""
    return xml.sax.saxutils.escape(str(text if text is not None else ""))


def _wrap_latin_in_ar(text: str) -> str:
    """Wrap Latin/ASCII word runs in <font name="Helvetica">...</font> so they render under NotoNaskhArabic."""
    def _repl(match):
        val = match.group(0)
        if val.startswith("&") and val.endswith(";"):
            return val
        return f'<font name="Helvetica">{val}</font>'

    return re.sub(r'(&[a-zA-Z]+;)|([A-Za-z0-9][A-Za-z0-9_./:+%&=-]*)', _repl, text)


# Language → (normal, bold) font family. CJK CID fonts have no separate bold
# face, so the same face is used for both weights. Latin-script languages use
# the standard Helvetica (WinAnsi) family.
_FONTS_FOR_LANG: dict[str, tuple[str, str]] = {
    "ja": ("HeiseiMin-W3", "HeiseiKakuGo-W5"),
    "zh": ("STSong-Light", "STSong-Light"),
    "ko": ("HYSMyeongJo-Medium", "HYSMyeongJo-Medium"),
    **_TTF_LANG_FONTS,
}
_DEFAULT_FONTS: tuple[str, str] = ("Helvetica", "Helvetica-Bold")

# Color palette — Atlas DDE Quiet Luxury (LVMH × Investment Bank hierarchy)
COLOR_BG_DARK = colors.HexColor("#070A10")       # Quiet Luxury deep obsidian (cover)
COLOR_SURFACE = colors.HexColor("#0D131F")       # Elevated dark surface
COLOR_ACCENT = colors.HexColor("#0284c7")        # Sky Blue — structural headings & primary accent
COLOR_ACCENT_DARK = colors.HexColor("#0369a1")   # Sky Blue darker
COLOR_ACCENT_LIGHT = colors.HexColor("#f0f9ff")  # Sky Blue soft tint (backgrounds)
COLOR_GREEN = colors.HexColor("#059669")         # Emerald Green — verified / strengths / GO / ○
COLOR_EMERALD_BG = colors.HexColor("#ecfdf5")    # Emerald soft tint
COLOR_YELLOW = colors.HexColor("#d97706")        # Amber — warnings ⚠️ / CONDITIONAL / △
COLOR_ORANGE = colors.HexColor("#d97706")        # Amber — HIGH severity
COLOR_AMBER_BG = colors.HexColor("#fffbeb")      # Amber soft tint
COLOR_RED = colors.HexColor("#e11d48")           # Pink-Red — CRITICAL / Blocker / NO-GO / ×
COLOR_ROSE_BG = colors.HexColor("#fff1f2")       # Pink-Red soft tint
COLOR_SLATE_BG = colors.HexColor("#f8fafc")      # Cool slate soft tint
COLOR_TEXT = colors.HexColor("#0f172a")          # Deep slate-black text
COLOR_TEXT_DIM = colors.HexColor("#64748b")      # Slate-500 muted text
COLOR_BORDER = colors.HexColor("#cbd5e1")        # Slate-300 clean hairline border
COLOR_WHITE = colors.white
COLOR_LIGHT_BG = colors.HexColor("#f8fafc")      # Slate-50 zebra background

# Severity color mapping
SEVERITY_COLORS = {
    Severity.CRITICAL: COLOR_RED,
    Severity.HIGH: COLOR_ORANGE,
    Severity.MEDIUM: COLOR_ACCENT,
    Severity.LOW: COLOR_GREEN,
    Severity.INFO: COLOR_ACCENT,
}

# Grade color mapping
GRADE_COLORS = {
    "A": colors.HexColor("#059669"),     # Emerald Green
    "B": colors.HexColor("#0284c7"),     # Sky Blue
    "C": colors.HexColor("#d97706"),     # Amber
    "D": colors.HexColor("#e11d48"),     # Pink-Red
    "F": colors.HexColor("#e11d48"),     # Pink-Red
}

# i18n strings for PDF
_PDF_I18N = {
    "en": {
        "title_prefix": "DUE DILIGENCE ENGINE",
        "report_title": "Technical Due Diligence Report",
        "analysis_id": "Analysis ID",
        "date": "Date",
        "grade_prefix": "Grade",
        "exec_summary": "Executive Summary",
        "metric": "Metric",
        "value": "Value",
        "overall_score": "Overall Score",
        "total_red_flags": "Total Red Flags",
        "critical_flags": "Critical Flags",
        "high_severity": "High Severity Flags",
        "files_analyzed": "Files Analyzed",
        "lines_of_code": "Lines of Code",
        "languages": "Languages",
        "api_cost": "API Cost",
        "score_breakdown": "Score Breakdown",
        "dimension": "Dimension",
        "score": "Score",
        "weight": "Weight",
        "weighted_score": "Weighted Score",
        "red_flags": "Red Flags",
        "codebase_metrics": "Codebase Metrics",
        "total_files": "Total Files",
        "total_lines": "Total Lines of Code",
        "wrapper_ratio": "API Wrapper Ratio",
        "test_coverage": "Test Coverage Estimate",
        "dependencies": "Dependencies",
        "has_tests": "Has Tests",
        "has_cicd": "Has CI/CD",
        "has_docs": "Has Documentation",
        "key_findings": "Key Findings",
        "git_forensics": "Git Forensics",
        "total_commits": "Total Commits",
        "unique_authors": "Unique Authors",
        "first_commit": "First Commit",
        "last_commit": "Last Commit",
        "rush_ratio": "Rush Commit Ratio",
        "suspicious_patterns": "Suspicious Patterns",
        "claim_consistency": "Claim Consistency",
        "consistency_score": "Consistency Score",
        "verified_claims": "Verified Claims",
        "unverified_claims": "Unverified Claims",
        "contradictions": "Contradictions",
        "contradictions_found": "Contradictions Found",
        "analysis_cost": "Analysis Cost",
        "total_api_cost": "Total API Cost",
        "model_tier": "Model Tier",
        "input_tokens": "Input Tokens",
        "output_tokens": "Output Tokens",
        "purge_cert_title": "Data Purge Certificate",
        "purge_cert_body": (
            "This certifies that all source code and analysis data associated with "
            "the following analysis has been cryptographically erased from this system."
        ),
        "field": "Field",
        "certificate_id": "Certificate ID",
        "project_name": "Project Name",
        "purge_timestamp": "Purge Timestamp",
        "files_purged": "Files Purged",
        "bytes_overwritten": "Bytes Overwritten",
        "deletion_method": "Deletion Method",
        "operator": "Operator",
        "verification_hash": "Verification Hash",
        "purge_footer": (
            "All source code data has been permanently deleted from this tool. "
            "Only report scores and findings have been retained."
        ),
        "nda_footer": (
            "CONFIDENTIAL - This report is subject to NDA. "
            "Do not distribute without authorization."
        ),
        "page": "Page",
        "yes": "Yes",
        "no": "No",
        "no_score": "No score was computed for this analysis.",
        "improvement_title": "Improvement Recommendations",
        # Consulting report sections
        "business_summary": "Executive Business Summary",
        "swot_analysis": "SWOT Analysis",
        "strengths": "Strengths",
        "weaknesses": "Weaknesses",
        "opportunities": "Opportunities",
        "threats": "Threats",
        "tech_level": "Technology Level Assessment",
        "future_outlook": "Future Outlook",
        "product_vision": "Product Vision",
        "viability": "Viability Assessment",
        "year_1": "Year 1",
        "year_3": "Year 3",
        "year_5": "Year 5",
        "confidence": "Confidence",
        "milestones": "Key Milestones",
        "strategic_advice": "Strategic Advice",
        "immediate_actions": "Immediate Actions",
        "medium_term": "Medium-Term Priorities",
        "long_term_vision": "Long-Term Vision",
        "investment_thesis": "Investment Thesis",
        "recommendation": "Recommendation",
        "key_risks": "Key Risks",
        "key_upside": "Key Upside",
        "comparable_companies": "Comparable Companies",
        "valuation_factors": "Valuation Factors",
        "glossary": "Glossary",
        "term": "Term",
        "definition": "Definition",
        "ai_model": "AI Model Used",
        "enables": "Enables",
        "action": "Action",
        "rationale": "Rationale",
        "impact": "Expected Impact",
        "invest_strong": "Strong Invest",
        "invest_conditions": "Invest with Conditions",
        "invest_cautious": "Cautious",
        "invest_pass": "Pass",
        "invest_strong_pass": "Strong Pass",
        "score_dashboard": "Score Dashboard",
        "score_dashboard_subtitle": "5-Dimension Evaluation at a Glance",
        # Site Verification
        "site_verification": "Site Verification",
        "site_verification_subtitle": "Website Claims vs Codebase Evidence",
        "overall_credibility": "Overall Credibility",
        "sv_urls_analyzed": "URLs Analyzed",
        "sv_summary": "Summary",
        # Competitive Analysis
        "competitive_analysis": "Competitive Analysis",
        "competitive_subtitle": "Market Positioning Charts",
        # Chart type names
        "chart_magic_quadrant": "Forrester Wave / Magic Quadrant",
        "chart_bcg_matrix": "BCG Growth-Share Matrix",
        "chart_mckinsey_moat": "Tech Moat Analysis",
        "chart_gs_risk_return": "Risk-Adjusted Return Analysis",
        "chart_bubble_3d": "Innovation vs. Commercialization",
        "chart_security_posture": "Security & Privacy Maturity",
        "chart_data_governance": "Data Governance & Transparency",
        # Quadrant labels — Magic Quadrant / Forrester Wave
        "leaders": "Leaders",
        "challengers": "Strong Performers",
        "visionaries": "Contenders",
        "niche_players": "Challengers",
        # Quadrant labels — BCG Matrix
        "stars": "Stars",
        "cash_cows": "Cash Cows",
        "question_marks": "Question Marks",
        "dogs": "Dogs",
        # Quadrant labels — Tech Moat
        "fortress": "Fortress",
        "innovator": "Innovator",
        "commodity": "Commodity",
        "fast_follower": "Fast Follower",
        # Quadrant labels — Security Posture
        "privacy_leader": "Privacy Leader",
        "security_fortress": "Security Fortress",
        "compliance_risk": "Compliance Risk",
        "exposed": "Exposed",
        # Quadrant labels — Data Governance
        "trust_leader": "Trust Leader",
        "opaque_fortress": "Opaque Fortress",
        "transparent_vuln": "Transparent / Vuln",
        "high_risk": "High Risk",
        # Risk-Return / Bubble zones
        "sweet_spot": "Sweet Spot",
        "avoid": "Avoid",
        # Confidence badges
        "confidence_high": "H",
        "confidence_medium": "M",
        "confidence_low": "L",
        # Atlas Optimization Assessment (v2.0)
        "atlas_four_axis": "Atlas Optimization Assessment",
        "atlas_subtitle": "Arc engineering philosophy — 4-axis evaluation (parallel to 5-dimension scoring)",
        "atlas_overall": "Atlas Composite Score",
        "atlas_industry_context": "Industry Context",
        "axis_performance": "Performance",
        "axis_stability": "Stability",
        "axis_lightweight": "Lightweight",
        "axis_security": "Security Strength",
        # Security sub-breakdown
        "security_breakdown": "Security Strength — Sub-Breakdown",
        "security_breakdown_subtitle": "Cybersecurity defense overall — 5 sub-categories within 55% (encryption is the largest at 35%)",
        "subitem_encryption": "Cryptographic Sophistication",
        "subitem_privacy": "Privacy Protection",
        "subitem_posture": "Basic Hygiene (MFA / SOC2 etc.)",
        "subitem_comms": "Communication Safety",
        "subitem_layers": "Layer Composition",
        # Implementation Capability Matrix (v2.0)
        "impl_matrix": "Implementation Capability Matrix",
        "impl_matrix_subtitle": "30 items × top global competitors — verified / claimed / not implemented / unknown",
        "impl_legend_verified": "Verified",
        "impl_legend_claimed": "Claimed",
        "impl_legend_not_impl": "Not Implemented",
        "impl_legend_unknown": "Unknown",
        # Matrix categories
        "matcat_performance": "Performance",
        "matcat_stability": "Stability",
        "matcat_lightweight": "Lightweight",
        "matcat_encryption": "Encryption (Core Differentiator)",
        "matcat_privacy": "Privacy",
        "matcat_posture": "Basic Hygiene",
        "matcat_comms": "Communication Safety",
        "matcat_layers": "Layer Composition",
        # Competitor Selection Rationales (v0.3.1)
        "competitor_rationales": "Competitor Selection Rationales",
        "competitor_rationales_subtitle": "Why these specific competitors were chosen as comparison targets",
        "rationale_category": "Category",
        "rationale_hq": "HQ",
        "rationale_position": "Market Position",
        # Data provenance (STEP 0 live web research)
        "data_freshness_title": "Data Provenance — Live Web Research",
        "df_search_date": "Search Date",
        "df_queries": "Queries Executed",
        "df_sources": "Sources Consulted",
        "df_no_web_warning": "No live web search performed — analysis relies on AI training data only",
        "visual_summary": "Visual Summary",
        "visual_summary_subtitle": "5-dimension radar + data provenance at a glance",
        "source_appendix_title": "Source Appendix",
        "source_appendix_subtitle": "Live web sources consulted during research",
        "src_verified_on": "Verification Date",
        "src_col_num": "#",
        "src_col_url": "Source URL",
        "src_none": "No external sources were recorded for this analysis.",
        "ai_provider_analysis": "AI Provider Analysis",
        "provider_score_comparison": "Provider Score Comparison",
        "avg_short": "Avg",
        "evidence": "Evidence",
    },
    "ja": {
        "title_prefix": "DUE DILIGENCE ENGINE",
        "report_title": "\u6280\u8853\u30c7\u30e5\u30fc\u30c7\u30ea\u30b8\u30a7\u30f3\u30b9\u30ec\u30dd\u30fc\u30c8",
        "analysis_id": "\u5206\u6790ID",
        "date": "\u65e5\u4ed8",
        "grade_prefix": "\u30b0\u30ec\u30fc\u30c9",
        "exec_summary": "\u30a8\u30b0\u30bc\u30af\u30c6\u30a3\u30d6\u30b5\u30de\u30ea",
        "metric": "\u6307\u6a19",
        "value": "\u5024",
        "overall_score": "\u7dcf\u5408\u30b9\u30b3\u30a2",
        "total_red_flags": "\u30ec\u30c3\u30c9\u30d5\u30e9\u30b0\u5408\u8a08",
        "critical_flags": "\u91cd\u5927\u30d5\u30e9\u30b0",
        "high_severity": "\u9ad8\u30ea\u30b9\u30af\u30d5\u30e9\u30b0",
        "files_analyzed": "\u5206\u6790\u30d5\u30a1\u30a4\u30eb\u6570",
        "lines_of_code": "\u30b3\u30fc\u30c9\u884c\u6570",
        "languages": "\u8a00\u8a9e",
        "api_cost": "API\u30b3\u30b9\u30c8",
        "score_breakdown": "\u30b9\u30b3\u30a2\u5185\u8a33",
        "dimension": "\u8a55\u4fa1\u8ef8",
        "score": "\u30b9\u30b3\u30a2",
        "weight": "\u91cd\u307f",
        "weighted_score": "\u52a0\u91cd\u30b9\u30b3\u30a2",
        "red_flags": "\u30ec\u30c3\u30c9\u30d5\u30e9\u30b0",
        "codebase_metrics": "\u30b3\u30fc\u30c9\u30d9\u30fc\u30b9\u6307\u6a19",
        "total_files": "\u30d5\u30a1\u30a4\u30eb\u6570",
        "total_lines": "\u30b3\u30fc\u30c9\u884c\u6570",
        "wrapper_ratio": "API\u30e9\u30c3\u30d1\u30fc\u7387",
        "test_coverage": "\u30c6\u30b9\u30c8\u30ab\u30d0\u30ec\u30c3\u30b8\u63a8\u5b9a",
        "dependencies": "\u4f9d\u5b58\u95a2\u4fc2",
        "has_tests": "\u30c6\u30b9\u30c8",
        "has_cicd": "CI/CD",
        "has_docs": "\u30c9\u30ad\u30e5\u30e1\u30f3\u30c8",
        "key_findings": "\u4e3b\u8981\u6240\u898b",
        "git_forensics": "Git\u5c65\u6b74\u30d5\u30a9\u30ec\u30f3\u30b8\u30c3\u30af",
        "total_commits": "\u30b3\u30df\u30c3\u30c8\u6570",
        "unique_authors": "\u8457\u8005\u6570",
        "first_commit": "\u521d\u56de\u30b3\u30df\u30c3\u30c8",
        "last_commit": "\u6700\u7d42\u30b3\u30df\u30c3\u30c8",
        "rush_ratio": "\u6025\u9020\u30b3\u30df\u30c3\u30c8\u7387",
        "suspicious_patterns": "\u7591\u308f\u3057\u3044\u30d1\u30bf\u30fc\u30f3",
        "claim_consistency": "\u4e3b\u5f35\u6574\u5408\u6027",
        "consistency_score": "\u6574\u5408\u6027\u30b9\u30b3\u30a2",
        "verified_claims": "\u691c\u8a3c\u6e08\u307f\u4e3b\u5f35",
        "unverified_claims": "\u672a\u691c\u8a3c\u306e\u4e3b\u5f35",
        "contradictions": "\u77db\u76fe",
        "contradictions_found": "\u691c\u51fa\u3055\u308c\u305f\u77db\u76fe",
        "analysis_cost": "\u5206\u6790\u30b3\u30b9\u30c8",
        "total_api_cost": "API\u5408\u8a08\u30b3\u30b9\u30c8",
        "model_tier": "\u30e2\u30c7\u30eb\u968e\u5c64",
        "input_tokens": "\u5165\u529b\u30c8\u30fc\u30af\u30f3",
        "output_tokens": "\u51fa\u529b\u30c8\u30fc\u30af\u30f3",
        "purge_cert_title": "\u30c7\u30fc\u30bf\u30d1\u30fc\u30b8\u8a3c\u660e\u66f8",
        "purge_cert_body": (
            "\u4ee5\u4e0b\u306e\u5206\u6790\u306b\u95a2\u9023\u3059\u308b\u5168\u3066\u306e\u30bd\u30fc\u30b9\u30b3\u30fc\u30c9\u304a\u3088\u3073\u5206\u6790\u30c7\u30fc\u30bf\u304c\u3001"
            "\u3053\u306e\u30b7\u30b9\u30c6\u30e0\u304b\u3089\u6697\u53f7\u5b66\u7684\u306b\u524a\u9664\u3055\u308c\u305f\u3053\u3068\u3092\u8a3c\u660e\u3057\u307e\u3059\u3002"
        ),
        "field": "\u9805\u76ee",
        "certificate_id": "\u8a3c\u660e\u66f8ID",
        "project_name": "\u30d7\u30ed\u30b8\u30a7\u30af\u30c8\u540d",
        "purge_timestamp": "\u30d1\u30fc\u30b8\u65e5\u6642",
        "files_purged": "\u524a\u9664\u30d5\u30a1\u30a4\u30eb\u6570",
        "bytes_overwritten": "\u4e0a\u66f8\u304d\u30d0\u30a4\u30c8\u6570",
        "deletion_method": "\u524a\u9664\u65b9\u6cd5",
        "operator": "\u5b9f\u884c\u8005",
        "verification_hash": "\u691c\u8a3c\u30cf\u30c3\u30b7\u30e5",
        "purge_footer": (
            "\u5168\u3066\u306e\u30bd\u30fc\u30b9\u30b3\u30fc\u30c9\u30c7\u30fc\u30bf\u304c\u3053\u306e\u30c4\u30fc\u30eb\u304b\u3089\u5b8c\u5168\u306b\u524a\u9664\u3055\u308c\u307e\u3057\u305f\u3002"
            "\u30ec\u30dd\u30fc\u30c8\u306e\u30b9\u30b3\u30a2\u3068\u6240\u898b\u306e\u307f\u4fdd\u6301\u3055\u308c\u3066\u3044\u307e\u3059\u3002"
        ),
        "nda_footer": "\u6a5f\u5bc6 - \u672c\u30ec\u30dd\u30fc\u30c8\u306fNDA\u306e\u5bfe\u8c61\u3067\u3059\u3002\u8a31\u53ef\u306a\u304f\u914d\u5e03\u3057\u306a\u3044\u3067\u304f\u3060\u3055\u3044\u3002",
        "page": "\u30da\u30fc\u30b8",
        "yes": "\u3042\u308a",
        "no": "\u306a\u3057",
        "no_score": "\u3053\u306e\u5206\u6790\u306e\u30b9\u30b3\u30a2\u306f\u8a08\u7b97\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002",
        "improvement_title": "改善提案",
        # Consulting report sections
        "business_summary": "ビジネスサマリー",
        "swot_analysis": "SWOT分析",
        "strengths": "強み",
        "weaknesses": "弱み",
        "opportunities": "機会",
        "threats": "脅威",
        "tech_level": "技術レベル評価",
        "future_outlook": "将来性評価",
        "product_vision": "プロダクトビジョン",
        "viability": "実現可能性",
        "year_1": "1年後",
        "year_3": "3年後",
        "year_5": "5年後",
        "confidence": "信頼度",
        "milestones": "主要マイルストーン",
        "strategic_advice": "戦略アドバイス",
        "immediate_actions": "即座のアクション",
        "medium_term": "中期優先事項",
        "long_term_vision": "長期ビジョン",
        "investment_thesis": "投資判断",
        "recommendation": "推奨度",
        "key_risks": "主要リスク",
        "key_upside": "アップサイド",
        "comparable_companies": "類似企業",
        "valuation_factors": "バリュエーション要因",
        "glossary": "用語集",
        "term": "用語",
        "definition": "定義",
        "ai_model": "使用AIモデル",
        "enables": "これにより可能になること",
        "action": "アクション",
        "rationale": "根拠",
        "impact": "期待される効果",
        "invest_strong": "強く投資推奨",
        "invest_conditions": "条件付き投資",
        "invest_cautious": "慎重",
        "invest_pass": "見送り",
        "invest_strong_pass": "強く見送り",
        "score_dashboard": "スコアダッシュボード",
        "score_dashboard_subtitle": "5次元評価の概要",
        # Site Verification
        "site_verification": "サイト検証",
        "site_verification_subtitle": "Webサイト主張 vs コードベース検証",
        "overall_credibility": "総合信頼性",
        "sv_urls_analyzed": "分析URL",
        "sv_summary": "サマリー",
        # Competitive Analysis
        "competitive_analysis": "競合分析",
        "competitive_subtitle": "市場ポジショニングチャート",
        # Chart type names
        "chart_magic_quadrant": "Forrester Wave / マジック・クアドラント",
        "chart_bcg_matrix": "BCG 成長・シェアマトリックス",
        "chart_mckinsey_moat": "テクノロジーモート分析",
        "chart_gs_risk_return": "リスク調整リターン分析",
        "chart_bubble_3d": "イノベーション vs 商業化",
        "chart_security_posture": "セキュリティ＆プライバシー成熟度",
        "chart_data_governance": "データガバナンス＆透明性",
        # Quadrant labels — Forrester Wave
        "leaders": "リーダー",
        "challengers": "ストロングパフォーマー",
        "visionaries": "コンテンダー",
        "niche_players": "チャレンジャー",
        # Quadrant labels — BCG Matrix
        "stars": "花形",
        "cash_cows": "金のなる木",
        "question_marks": "問題児",
        "dogs": "負け犬",
        # Quadrant labels — Tech Moat
        "fortress": "要塞",
        "innovator": "イノベーター",
        "commodity": "コモディティ",
        "fast_follower": "ファストフォロワー",
        # Quadrant labels — Security Posture
        "privacy_leader": "プライバシーリーダー",
        "security_fortress": "セキュリティ要塞",
        "compliance_risk": "コンプライアンスリスク",
        "exposed": "脆弱",
        # Quadrant labels — Data Governance
        "trust_leader": "信頼リーダー",
        "opaque_fortress": "不透明な要塞",
        "transparent_vuln": "透明だが脆弱",
        "high_risk": "高リスク",
        # Risk-Return / Bubble zones
        "sweet_spot": "最適ゾーン",
        "avoid": "回避",
        # Confidence badges
        "confidence_high": "H",
        "confidence_medium": "M",
        "confidence_low": "L",
        # Atlas 最適化評価 (v2.0)
        "atlas_four_axis": "Atlas 最適化評価",
        "atlas_subtitle": "Arc エンジニアリング哲学 — 4軸並列評価（既存5次元と並列）",
        "atlas_overall": "Atlas 総合スコア",
        "atlas_industry_context": "業界コンテキスト",
        "axis_performance": "高速化",
        "axis_stability": "安定化",
        "axis_lightweight": "軽量化",
        "axis_security": "セキュリティ強度",
        # セキュリティ内訳
        "security_breakdown": "セキュリティ強度 — サブ内訳",
        "security_breakdown_subtitle": "サイバーセキュリティ対策全般 — 55% 内訳 5 サブカテゴリ（暗号化が最大の 35%）",
        "subitem_encryption": "暗号化技術の高度さ",
        "subitem_privacy": "プライバシー保護",
        "subitem_posture": "基本衛生（MFA・SOC2等）",
        "subitem_comms": "通信の安全",
        "subitem_layers": "レイヤー構成",
        # 実装能力マトリックス (v2.0)
        "impl_matrix": "実装能力マトリックス",
        "impl_matrix_subtitle": "30項目 × グローバルトップ競合 — 実装確認済 / 主張あり / 未実装 / 不明",
        "impl_legend_verified": "実装確認済",
        "impl_legend_claimed": "主張あり",
        "impl_legend_not_impl": "未実装",
        "impl_legend_unknown": "不明",
        # マトリックスカテゴリ
        "matcat_performance": "高速化",
        "matcat_stability": "安定化",
        "matcat_lightweight": "軽量化",
        "matcat_encryption": "暗号化（核心差別化）",
        "matcat_privacy": "プライバシー",
        "matcat_posture": "基本衛生",
        "matcat_comms": "通信の安全",
        "matcat_layers": "レイヤー構成",
        # 競合選定理由 (v0.3.1)
        "competitor_rationales": "競合選定理由",
        "competitor_rationales_subtitle": "なぜこの競合企業群を比較対象に選んだのか",
        "rationale_category": "カテゴリ",
        "rationale_hq": "本社",
        "rationale_position": "市場ポジション",
        # Data provenance (STEP 0 live web research)
        "data_freshness_title": "データ出所 — ライブ Web 調査",
        "df_search_date": "検索日",
        "df_queries": "実行クエリ数",
        "df_sources": "参照ソース数",
        "df_no_web_warning": "ライブ Web 検索なし — AI の学習データのみに基づく分析",
        "visual_summary": "ビジュアルサマリー",
        "visual_summary_subtitle": "5次元レーダー + データ出所を一目で",
        "source_appendix_title": "出典付録",
        "source_appendix_subtitle": "調査中に参照したライブ Web ソース",
        "src_verified_on": "検証日",
        "src_col_num": "#",
        "src_col_url": "ソース URL",
        "src_none": "本分析では外部ソースの記録はありません。",
        "ai_provider_analysis": "AIプロバイダー分析",
        "provider_score_comparison": "プロバイダースコア比較",
        "avg_short": "平均",
        "evidence": "証拠",
    },
    "es": {
        "title_prefix": "DUE DILIGENCE ENGINE",
        "report_title": "Informe de Due Diligence Técnica",
        "analysis_id": "ID de Análisis",
        "date": "Fecha",
        "grade_prefix": "Calificación",
        "exec_summary": "Resumen Ejecutivo",
        "metric": "Métrica",
        "value": "Valor",
        "overall_score": "Puntuación Global",
        "total_red_flags": "Total de Señales de Alerta",
        "critical_flags": "Señales Críticas",
        "high_severity": "Señales de Alta Severidad",
        "files_analyzed": "Archivos Analizados",
        "lines_of_code": "Líneas de Código",
        "languages": "Lenguajes",
        "api_cost": "Costo de API",
        "score_breakdown": "Desglose de Puntuación",
        "dimension": "Dimensión",
        "score": "Puntuación",
        "weight": "Peso",
        "weighted_score": "Puntuación Ponderada",
        "red_flags": "Señales de Alerta",
        "codebase_metrics": "Métricas del Código Base",
        "total_files": "Total de Archivos",
        "total_lines": "Total de Líneas de Código",
        "wrapper_ratio": "Proporción de Wrappers de API",
        "test_coverage": "Estimación de Cobertura de Pruebas",
        "dependencies": "Dependencias",
        "has_tests": "Tiene Pruebas",
        "has_cicd": "Tiene CI/CD",
        "has_docs": "Tiene Documentación",
        "key_findings": "Hallazgos Clave",
        "git_forensics": "Análisis Forense de Git",
        "total_commits": "Total de Commits",
        "unique_authors": "Autores Únicos",
        "first_commit": "Primer Commit",
        "last_commit": "Último Commit",
        "rush_ratio": "Proporción de Commits Apresurados",
        "suspicious_patterns": "Patrones Sospechosos",
        "claim_consistency": "Consistencia de Afirmaciones",
        "consistency_score": "Puntuación de Consistencia",
        "verified_claims": "Afirmaciones Verificadas",
        "unverified_claims": "Afirmaciones No Verificadas",
        "contradictions": "Contradicciones",
        "contradictions_found": "Contradicciones Encontradas",
        "analysis_cost": "Costo del Análisis",
        "total_api_cost": "Costo Total de API",
        "model_tier": "Nivel del Modelo",
        "input_tokens": "Tokens de Entrada",
        "output_tokens": "Tokens de Salida",
        "purge_cert_title": "Certificado de Purga de Datos",
        "purge_cert_body": (
            "Esto certifica que todo el código fuente y los datos de análisis asociados con "
            "el siguiente análisis han sido borrados criptográficamente de este sistema."
        ),
        "field": "Campo",
        "certificate_id": "ID del Certificado",
        "project_name": "Nombre del Proyecto",
        "purge_timestamp": "Marca de Tiempo de la Purga",
        "files_purged": "Archivos Purgados",
        "bytes_overwritten": "Bytes Sobrescritos",
        "deletion_method": "Método de Eliminación",
        "operator": "Operador",
        "verification_hash": "Hash de Verificación",
        "purge_footer": (
            "Todos los datos del código fuente han sido eliminados permanentemente de esta herramienta. "
            "Solo se han conservado las puntuaciones y los hallazgos del informe."
        ),
        "nda_footer": (
            "CONFIDENCIAL - Este informe está sujeto a un NDA. "
            "No distribuir sin autorización."
        ),
        "page": "Página",
        "yes": "Sí",
        "no": "No",
        "no_score": "No se calculó ninguna puntuación para este análisis.",
        "improvement_title": "Recomendaciones de Mejora",
        "business_summary": "Resumen Ejecutivo de Negocio",
        "swot_analysis": "Análisis SWOT",
        "strengths": "Fortalezas",
        "weaknesses": "Debilidades",
        "opportunities": "Oportunidades",
        "threats": "Amenazas",
        "tech_level": "Evaluación del Nivel Tecnológico",
        "future_outlook": "Perspectiva a Futuro",
        "product_vision": "Visión del Producto",
        "viability": "Evaluación de Viabilidad",
        "year_1": "Año 1",
        "year_3": "Año 3",
        "year_5": "Año 5",
        "confidence": "Confianza",
        "milestones": "Hitos Clave",
        "strategic_advice": "Asesoría Estratégica",
        "immediate_actions": "Acciones Inmediatas",
        "medium_term": "Prioridades a Mediano Plazo",
        "long_term_vision": "Visión a Largo Plazo",
        "investment_thesis": "Tesis de Inversión",
        "recommendation": "Recomendación",
        "key_risks": "Riesgos Clave",
        "key_upside": "Potencial Alcista Clave",
        "comparable_companies": "Empresas Comparables",
        "valuation_factors": "Factores de Valoración",
        "glossary": "Glosario",
        "term": "Término",
        "definition": "Definición",
        "ai_model": "Modelo de IA Utilizado",
        "enables": "Habilita",
        "action": "Acción",
        "rationale": "Justificación",
        "impact": "Impacto Esperado",
        "invest_strong": "Inversión Sólida",
        "invest_conditions": "Invertir con Condiciones",
        "invest_cautious": "Cauteloso",
        "invest_pass": "Descartar",
        "invest_strong_pass": "Descartar Rotundamente",
        "score_dashboard": "Panel de Puntuación",
        "score_dashboard_subtitle": "Evaluación de 5 Dimensiones de un Vistazo",
        "site_verification": "Verificación del Sitio",
        "site_verification_subtitle": "Afirmaciones del Sitio Web vs Evidencia del Código Base",
        "overall_credibility": "Credibilidad Global",
        "sv_urls_analyzed": "URLs Analizadas",
        "sv_summary": "Resumen",
        "competitive_analysis": "Análisis Competitivo",
        "competitive_subtitle": "Gráficos de Posicionamiento de Mercado",
        "chart_magic_quadrant": "Forrester Wave / Magic Quadrant",
        "chart_bcg_matrix": "Matriz de Crecimiento-Participación BCG",
        "chart_mckinsey_moat": "Análisis de Foso Tecnológico",
        "chart_gs_risk_return": "Análisis de Rendimiento Ajustado al Riesgo",
        "chart_bubble_3d": "Innovación vs. Comercialización",
        "chart_security_posture": "Madurez de Seguridad y Privacidad",
        "chart_data_governance": "Gobernanza de Datos y Transparencia",
        "leaders": "Líderes",
        "challengers": "Competidores Destacados",
        "visionaries": "Aspirantes",
        "niche_players": "Retadores",
        "stars": "Estrellas",
        "cash_cows": "Vacas Lecheras",
        "question_marks": "Incógnitas",
        "dogs": "Perros",
        "fortress": "Fortaleza",
        "innovator": "Innovador",
        "commodity": "Producto Básico",
        "fast_follower": "Seguidor Rápido",
        "privacy_leader": "Líder en Privacidad",
        "security_fortress": "Fortaleza de Seguridad",
        "compliance_risk": "Riesgo de Cumplimiento",
        "exposed": "Expuesto",
        "trust_leader": "Líder en Confianza",
        "opaque_fortress": "Fortaleza Opaca",
        "transparent_vuln": "Transparente / Vulnerable",
        "high_risk": "Alto Riesgo",
        "sweet_spot": "Punto Óptimo",
        "avoid": "Evitar",
        "confidence_high": "H",
        "confidence_medium": "M",
        "confidence_low": "L",
        "atlas_four_axis": "Evaluación de Optimización Atlas",
        "atlas_subtitle": "Filosofía de ingeniería Arc — evaluación de 4 ejes (paralela a la puntuación de 5 dimensiones)",
        "atlas_overall": "Puntuación Compuesta Atlas",
        "atlas_industry_context": "Contexto de la Industria",
        "axis_performance": "Rendimiento",
        "axis_stability": "Estabilidad",
        "axis_lightweight": "Ligereza",
        "axis_security": "Solidez de Seguridad",
        "security_breakdown": "Solidez de Seguridad — Subdesglose",
        "security_breakdown_subtitle": "Defensa de ciberseguridad global — 5 subcategorías dentro del 55% (el cifrado es la mayor con un 35%)",
        "subitem_encryption": "Sofisticación Criptográfica",
        "subitem_privacy": "Protección de la Privacidad",
        "subitem_posture": "Higiene Básica (MFA / SOC2 etc.)",
        "subitem_comms": "Seguridad de las Comunicaciones",
        "subitem_layers": "Composición de Capas",
        "impl_matrix": "Matriz de Capacidad de Implementación",
        "impl_matrix_subtitle": "30 ítems × principales competidores globales — verificado / declarado / no implementado / desconocido",
        "impl_legend_verified": "Verificado",
        "impl_legend_claimed": "Declarado",
        "impl_legend_not_impl": "No Implementado",
        "impl_legend_unknown": "Desconocido",
        "matcat_performance": "Rendimiento",
        "matcat_stability": "Estabilidad",
        "matcat_lightweight": "Ligereza",
        "matcat_encryption": "Cifrado (Diferenciador Central)",
        "matcat_privacy": "Privacidad",
        "matcat_posture": "Higiene Básica",
        "matcat_comms": "Seguridad de las Comunicaciones",
        "matcat_layers": "Composición de Capas",
        "competitor_rationales": "Justificación de la Selección de Competidores",
        "competitor_rationales_subtitle": "Por qué se eligieron estos competidores específicos como objetivos de comparación",
        "rationale_category": "Categoría",
        "rationale_hq": "Sede Central",
        "rationale_position": "Posición de Mercado",
        # Data provenance (STEP 0 live web research)
        "data_freshness_title": "Procedencia de los Datos — Investigación Web en Vivo",
        "df_search_date": "Fecha de Búsqueda",
        "df_queries": "Consultas Ejecutadas",
        "df_sources": "Fuentes Consultadas",
        "df_no_web_warning": "Sin búsqueda web en vivo — el análisis se basa solo en datos de entrenamiento de la IA",
        "visual_summary": "Resumen Visual",
        "visual_summary_subtitle": "Radar de 5 dimensiones + procedencia de datos de un vistazo",
        "source_appendix_title": "Apéndice de Fuentes",
        "source_appendix_subtitle": "Fuentes web en vivo consultadas durante la investigación",
        "src_verified_on": "Fecha de verificación",
        "src_col_num": "#",
        "src_col_url": "URL de la fuente",
        "src_none": "No se registraron fuentes externas para este análisis.",
        "ai_provider_analysis": "Análisis de Proveedores de IA",
        "provider_score_comparison": "Comparación de Puntuaciones de Proveedores",
        "avg_short": "Prom.",
        "evidence": "Evidencia",
    },
}

# Grade recommendations for PDF
_PDF_GRADE_REC = {
    "en": {
        "A": "Strong investment candidate. Proceed with standard terms.",
        "B": "Viable with conditions. Address flagged items before closing.",
        "C": "Significant concerns. Require remediation plan with milestones.",
        "D": "High risk. Consider pass or heavily discounted terms.",
        "F": "Do not invest. Fundamental issues detected.",
    },
    "ja": {
        "A": "\u6709\u529b\u306a\u6295\u8cc7\u5019\u88dc\u3002\u6a19\u6e96\u6761\u4ef6\u3067\u9032\u884c\u53ef\u80fd\u3002",
        "B": "\u6761\u4ef6\u4ed8\u304d\u3067\u6295\u8cc7\u53ef\u80fd\u3002\u6307\u6458\u4e8b\u9805\u306e\u5bfe\u5fdc\u3092\u78ba\u8a8d\u3002",
        "C": "\u91cd\u8981\u306a\u61f8\u5ff5\u3042\u308a\u3002\u6539\u5584\u8a08\u753b\u306e\u63d0\u51fa\u3092\u8981\u6c42\u3002",
        "D": "\u9ad8\u30ea\u30b9\u30af\u3002\u898b\u9001\u308a\u307e\u305f\u306f\u5927\u5e45\u306a\u6761\u4ef6\u5909\u66f4\u3092\u691c\u8a0e\u3002",
        "F": "\u6295\u8cc7\u4e0d\u53ef\u3002\u6839\u672c\u7684\u306a\u554f\u984c\u3092\u691c\u51fa\u3002",
    },
    "es": {
        "A": "Candidato s\u00f3lido para inversi\u00f3n. Proceder con t\u00e9rminos est\u00e1ndar.",
        "B": "Viable con condiciones. Resolver los \u00edtems se\u00f1alados antes del cierre.",
        "C": "Preocupaciones significativas. Requerir un plan de remediaci\u00f3n con hitos.",
        "D": "Alto riesgo. Considerar descartar o t\u00e9rminos con fuerte descuento.",
        "F": "No invertir. Se detectaron problemas fundamentales.",
    },
}

# Dimension name translations
_DIM_NAME_JA = {
    "Technical Originality": "技術独自性",
    "Technology Advancement": "技術先進性",
    "Implementation Depth": "実装深度",
    "Architecture Quality": "アーキテクチャ品質",
    "Architecture Quality (incl. Security)": "アーキテクチャ品質（セキュリティ含む）",
    "Claim Consistency": "主張整合性",
    # v0.3: Security Posture was merged into Architecture Quality; kept here for backward compat
    "Security Posture": "セキュリティ態勢",
}

_DIM_NAME_ES = {
    "Technical Originality": "Originalidad Técnica",
    "Technology Advancement": "Avance Tecnológico",
    "Implementation Depth": "Profundidad de Implementación",
    "Architecture Quality": "Calidad de la Arquitectura",
    "Architecture Quality (incl. Security)": "Calidad de la Arquitectura (incl. Seguridad)",
    "Claim Consistency": "Consistencia de Afirmaciones",
    "Security Posture": "Postura de Seguridad",
}

# Per-language dimension-name maps (en and unmapped langs use the English name as-is)
_DIM_NAME_MAPS = {"en": {name: name for name in _DIM_NAME_JA}, "ja": _DIM_NAME_JA, "es": _DIM_NAME_ES}

# Merge in additional Latin-script language packs (fr / de / pt / nl / it / id).
# These render with the standard Helvetica font (WinAnsi), so no font work needed.
from due_diligence_engine.report.i18n_packs import (  # noqa: E402
    PDF_I18N_PACKS as _PDF_I18N_PACKS,
    GRADE_REC_PACKS as _GRADE_REC_PACKS,
    DIM_NAME_PACKS as _DIM_NAME_PACKS,
    DIM_DESC_PACKS as _DIM_DESC_PACKS,
)
_PDF_I18N.update(_PDF_I18N_PACKS)
_PDF_GRADE_REC.update(_GRADE_REC_PACKS)
_DIM_NAME_MAPS.update(_DIM_NAME_PACKS)

# Canonical dimension key → English name. Single source of truth shared by the
# score dashboard bar chart and the visual-summary radar chart.
_DIM_NAME_MAP = {
    "technical_originality": "Technical Originality",
    "technology_advancement": "Technology Advancement",
    "implementation_depth": "Implementation Depth",
    "architecture_quality": "Architecture Quality (incl. Security)",
    "claim_consistency": "Claim Consistency",
}


def inspect_flowables_scale(elements: list[Any], min_scale: float = 0.75) -> list[str]:
    """Inspect KeepInFrame instances in elements and return warnings if scale < min_scale."""
    from reportlab.platypus import KeepInFrame

    warnings: list[str] = []

    def _walk(item: Any, path: str = "root") -> None:
        if isinstance(item, KeepInFrame):
            scale = getattr(item, "_scale", 1.0)
            scale = 1.0 / scale if scale > 1.0 else scale
            if scale < min_scale:
                name = getattr(item, "name", None) or getattr(item, "_content", [None])[0] or "unnamed"
                warnings.append(
                    f"KeepInFrame ({path}: {name}) scale factor {scale:.2f} is below minimum {min_scale:.2f}"
                )
        if hasattr(item, "_content") and isinstance(item._content, (list, tuple)):
            for i, child in enumerate(item._content):
                _walk(child, f"{path}._content[{i}]")
        if hasattr(item, "_flowables") and isinstance(item._flowables, (list, tuple)):
            for i, child in enumerate(item._flowables):
                _walk(child, f"{path}._flowables[{i}]")
        if hasattr(item, "_cellvalues") and isinstance(item._cellvalues, (list, tuple)):
            for r_idx, row in enumerate(item._cellvalues):
                if isinstance(row, (list, tuple)):
                    for c_idx, cell in enumerate(row):
                        _walk(cell, f"{path}[{r_idx}][{c_idx}]")

    for idx, el in enumerate(elements):
        _walk(el, f"elements[{idx}]")

    return warnings


def _wrap_lines(text: str, max_chars_per_line: int, max_lines: int = 2) -> list[str]:
    """Wrap text into N lines for use with Drawing.String (no auto-wrap).

    CJK-aware approximation:
    - For Japanese mixed text, count each char as 1 unit (CJK chars are wider but
      this gives a reasonable visual fit at the calling site's font size).
    - For pure ASCII, ~70 chars/line is comfortable at 6.5pt.
    - Caller picks `max_chars_per_line` based on its render width.

    Returns up to `max_lines` lines. If text exceeds capacity, last line ends with "…".
    """
    if not text:
        return []
    text = text.strip()
    lines: list[str] = []
    remaining = text
    for i in range(max_lines):
        if not remaining:
            break
        if len(remaining) <= max_chars_per_line:
            lines.append(remaining)
            remaining = ""
            break
        # Try to break at a space near the limit (for ASCII / mixed text)
        cut = max_chars_per_line
        space_idx = remaining.rfind(" ", 0, max_chars_per_line)
        # Use space if it's not too far back (>50% of line)
        if space_idx > max_chars_per_line // 2:
            cut = space_idx
        lines.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()

    if remaining:
        # Truncate the last line and append ellipsis
        last = lines[-1]
        if len(last) >= max_chars_per_line - 1:
            last = last[: max_chars_per_line - 1]
        lines[-1] = last.rstrip() + "…"
    return lines


def _build_styles(lang: str = "en") -> dict[str, ParagraphStyle]:
    """Build custom paragraph styles for the PDF report."""
    base = getSampleStyleSheet()

    # Select font family based on language (CJK → CID fonts; Latin → Helvetica)
    font_normal, font_bold = _FONTS_FOR_LANG.get(lang, _DEFAULT_FONTS)

    # ── Typography system (v2.0 — explicit leading, hierarchical sizes) ──
    # All styles below specify `leading` explicitly to prevent overlap.
    # Size hierarchy: 28 (title) / 20 (H1) / 14 (H2) / 11 (H3) / 10 (body) /
    # 9 (body_dim) / 8.5 (small) / 7.5 (caption) / 7 (footer).
    # Leading: fontSize × 1.3-1.5 generally; body × 1.6 for Japanese readability.
    return {
        "title": ParagraphStyle(
            "CustomTitle",
            parent=base["Title"],
            fontSize=28,
            leading=36,
            textColor=COLOR_BG_DARK,
            spaceAfter=6 * mm,
            alignment=TA_CENTER,
            fontName=font_bold,
        ),
        "subtitle": ParagraphStyle(
            "CustomSubtitle",
            parent=base["Normal"],
            fontSize=14,
            leading=20,
            textColor=COLOR_TEXT_DIM,
            spaceAfter=4 * mm,
            alignment=TA_CENTER,
            fontName=font_normal,
        ),
        "heading1": ParagraphStyle(
            "CustomH1",
            parent=base["Heading1"],
            fontSize=20,                # was 18 — bigger for impact
            leading=26,
            textColor=COLOR_BG_DARK,
            spaceBefore=10 * mm,        # was 8mm — more breathing room
            spaceAfter=5 * mm,
            borderWidth=0,
            borderPadding=0,
            fontName=font_bold,
        ),
        "heading2": ParagraphStyle(
            "CustomH2",
            parent=base["Heading2"],
            fontSize=14,
            leading=18,
            textColor=COLOR_ACCENT,     # Arc sky #5271FF
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
            fontName=font_bold,
        ),
        "heading3": ParagraphStyle(
            "CustomH3",
            parent=base["Normal"],
            fontSize=11,
            leading=14,
            textColor=COLOR_TEXT,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            fontName=font_bold,
        ),
        "body": ParagraphStyle(
            "CustomBody",
            parent=base["Normal"],
            fontSize=10,
            leading=16,                 # was 14 — JA needs more (1.6 ratio)
            textColor=COLOR_TEXT,
            spaceAfter=3 * mm,
            fontName=font_normal,
        ),
        "body_small": ParagraphStyle(
            "CustomBodySmall",
            parent=base["Normal"],
            fontSize=8.5,               # was 8 — slightly larger for readability
            leading=12,
            textColor=COLOR_TEXT_DIM,
            spaceAfter=2 * mm,
            fontName=font_normal,
        ),
        "caption": ParagraphStyle(
            "CustomCaption",
            parent=base["Normal"],
            fontSize=7.5,
            leading=10,
            textColor=COLOR_TEXT_DIM,
            spaceAfter=1 * mm,
            fontName=font_normal,
        ),
        "footer": ParagraphStyle(
            "CustomFooter",
            parent=base["Normal"],
            fontSize=7,
            leading=9,
            textColor=COLOR_TEXT_DIM,
            alignment=TA_CENTER,
            fontName=font_normal,
        ),
        "score_large": ParagraphStyle(
            "ScoreLarge",
            parent=base["Normal"],
            fontSize=48,
            leading=56,
            textColor=COLOR_BG_DARK,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
            fontName=font_bold,
        ),
        "grade_label": ParagraphStyle(
            "GradeLabel",
            parent=base["Normal"],
            fontSize=16,
            leading=22,
            textColor=COLOR_TEXT_DIM,
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
            fontName=font_normal,
        ),
        "flag_title": ParagraphStyle(
            "FlagTitle",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            textColor=COLOR_TEXT,
            spaceAfter=1 * mm,
            fontName=font_bold,
        ),
        "flag_desc": ParagraphStyle(
            "FlagDesc",
            parent=base["Normal"],
            fontSize=9,
            leading=13,
            textColor=COLOR_TEXT_DIM,
            spaceAfter=3 * mm,
            leftIndent=10,
            fontName=font_normal,
        ),
        "center": ParagraphStyle(
            "CenterBody",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            textColor=COLOR_TEXT,
            alignment=TA_CENTER,
            spaceAfter=3 * mm,
            fontName=font_normal,
        ),
        "body_dim": ParagraphStyle(
            "CustomBodyDim",
            parent=base["Normal"],
            fontSize=9,
            leading=13,
            textColor=COLOR_TEXT_DIM,
            spaceAfter=2 * mm,
            fontName=font_normal,
        ),
        "nda_notice": ParagraphStyle(
            "NDANotice",
            parent=base["Normal"],
            fontSize=7,
            leading=10,
            textColor=COLOR_RED,
            alignment=TA_CENTER,
            fontName=font_normal,
        ),
    }


class PDFReportGenerator:
    """Generates professional PDF due diligence reports.

    The generated PDF contains:
    - Cover page with overall score
    - Executive summary
    - Score dimension breakdown
    - Red flags detail
    - Codebase metrics summary
    - Git forensics summary (if available)
    - Analysis cost breakdown
    - Purge certificate (if applicable)

    Source code is NEVER included in the output.
    """

    def __init__(self) -> None:
        self._styles: dict[str, ParagraphStyle] = {}
        self._lang = "en"
        self._t: dict[str, str] = {}

    def generate(
        self,
        result: AnalysisResult,
        purge_cert: PurgeCertificate | None = None,
        lang: str = "en",
    ) -> bytes:
        """Generate a PDF report as bytes.

        Args:
            result: The complete analysis result.
            purge_cert: Optional purge certificate to include.
            lang: Language code ("en" or "ja").

        Returns:
            PDF file content as bytes.
        """
        self._lang = lang if lang in _PDF_I18N else "en"
        self._styles = _build_styles(self._lang)
        self._t = _PDF_I18N.get(self._lang, _PDF_I18N["en"])
        cr = result.consulting_report
        if self._lang == "ar":
            # Pre-shape chrome labels + all report content for RTL rendering.
            self._t = {k: (_reshape_ar(v) if isinstance(v, str) else v)
                       for k, v in self._t.items()}
            if cr is not None:
                cr = copy.deepcopy(cr)
                _deep_reshape_inplace(cr)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
            title=f"Due Diligence Report: {result.project_name}",
            author="Due Diligence Engine",
        )

        story: list = []

        # Cover page
        story.extend(self._build_cover_page(result, cr=cr))

        # --- Consulting report sections (if available) ---
        if cr is not None:
            # Score dashboard (bar chart overview) — first page after cover
            story.append(PageBreak())
            story.extend(self._build_score_dashboard(cr))

            # Visual summary (radar chart + data provenance) — its own page so
            # neither element gets stranded across a page break.
            visual = self._build_visual_summary_page(cr)
            if visual:
                story.append(PageBreak())
                story.extend(visual)

            # Business summary
            story.append(PageBreak())
            story.extend(self._build_business_summary(cr))

            # SWOT
            story.append(PageBreak())
            story.extend(self._build_swot_page(cr))

            # Score breakdown + Tech level (combined — they belong together visually)
            story.append(PageBreak())
            story.extend(self._build_consulting_scores(cr))
            # Tech level flows naturally after scores; PDF engine will page-break if needed
            story.extend(self._build_tech_level_page(cr))

            # Future outlook + Strategic advice + Investment thesis flow together
            # (removed forced PageBreaks between — let PDF engine handle overflow naturally
            #  to avoid sparse half-empty pages)
            story.append(PageBreak())
            story.extend(self._build_future_outlook_page(cr))
            story.extend(self._build_strategic_advice_page(cr))
            story.extend(self._build_investment_thesis_page(cr))

            # Red flags — allowed to flow with investment thesis if space permits
            if cr.red_flags:
                story.extend(self._build_consulting_red_flags(cr))

            # Site Verification
            if cr.site_verification and cr.site_verification.items:
                story.append(PageBreak())
                story.extend(self._build_site_verification_page(cr))

            # Competitive Analysis
            if cr.competitive_analysis and cr.competitive_analysis.markets:
                story.extend(self._build_competitive_analysis_pages(cr))

            # Atlas Optimization Assessment (v2.0)
            if cr.atlas_four_axis and cr.atlas_four_axis.axes:
                story.append(PageBreak())
                story.extend(self._build_atlas_four_axis_page(cr))
                # Security sub-breakdown only if security axis has sub_items
                security_axis = next(
                    (a for a in cr.atlas_four_axis.axes if a.axis_key == "security"),
                    None,
                )
                if security_axis and security_axis.sub_items:
                    story.append(PageBreak())
                    story.extend(self._build_atlas_security_breakdown_page(cr, security_axis))

            # Competitor Selection Rationales (v0.3.1)
            if cr.competitor_rationales:
                story.append(PageBreak())
                story.extend(self._build_competitor_rationales_page(cr))

            # Implementation Capability Matrix (v2.0)
            if cr.implementation_matrix and cr.implementation_matrix.items:
                story.extend(self._build_implementation_matrix_page(cr))

        else:
            # Standard report flow (no consulting data)
            # Executive summary
            story.append(PageBreak())
            story.extend(self._build_executive_summary(result))

            # Score breakdown
            story.extend(self._build_score_breakdown(result))

            # Multi-AI provider results
            if result.ai_results:
                story.extend(self._build_ai_provider_section(result))

            # Red flags
            if result.score and result.score.red_flags:
                story.append(PageBreak())
                story.extend(self._build_red_flags_section(result))

        # Heuristic sections — only when NOT in consulting-only mode
        # (consulting PDF gets its data from AI evaluation, not heuristics)
        has_heuristic_data = (
            result.code_analysis.total_files > 0
            or result.git_forensics.total_commits > 0
        )

        if has_heuristic_data:
            # Codebase metrics
            story.append(PageBreak())
            story.extend(self._build_codebase_metrics(result))

            # Git forensics
            if result.git_forensics.total_commits > 0:
                story.extend(self._build_git_forensics(result))

            # Consistency check
            story.extend(self._build_consistency_section(result))

        # Glossary (consulting only)
        if cr is not None:
            story.append(PageBreak())
            story.extend(self._build_glossary_page(cr))

            # Source appendix — the actual live-web URLs consulted in STEP 0.
            appendix = self._build_source_appendix_page(cr)
            if appendix:
                story.append(PageBreak())
                story.extend(appendix)

        # Cost breakdown — skip if zero (consulting mode uses no API)
        if result.total_cost_usd > 0:
            story.extend(self._build_cost_section(result))

        # Purge certificate
        if purge_cert is not None:
            story.append(PageBreak())
            story.extend(self._build_purge_certificate(purge_cert))

        # Build PDF with footer (dark cover on first page)
        doc.build(story, onFirstPage=self._add_cover_bg, onLaterPages=self._add_footer)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def generate_to_file(
        self,
        result: AnalysisResult,
        output_path: Path,
        purge_cert: PurgeCertificate | None = None,
        lang: str = "en",
    ) -> Path:
        """Generate a PDF report and save to file.

        Args:
            result: The complete analysis result.
            output_path: Path to save the PDF file.
            purge_cert: Optional purge certificate to include.
            lang: Language code ("en" or "ja").

        Returns:
            Path to the generated PDF file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_bytes = self.generate(result, purge_cert, lang=lang)
        output_path.write_bytes(pdf_bytes)
        logger.info(f"PDF report saved to {output_path}")
        return output_path

    def _maybe_reshape(self, text: str) -> str:
        """Shape Arabic chrome/content strings for RTL; no-op for other languages."""
        return _reshape_ar(text) if self._lang == "ar" else text

    def _esc_text(self, text: Any) -> str:
        """Escape text for ReportLab Paragraph, and wrap Latin runs if in Arabic or Thai mode."""
        raw = str(text if text is not None else "")
        if self._lang not in ("ar", "th"):
            return _esc(raw)

        # Arabic & Thai mode: split raw string by Latin/ASCII runs BEFORE XML escaping
        # so entities like &amp; are never sliced across <font> tags.
        pattern = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./:+%&=@#?~,\-]*")
        result_parts = []
        last_end = 0
        for m in pattern.finditer(raw):
            start, end = m.span()
            if start > last_end:
                result_parts.append(_esc(raw[last_end:start]))
            result_parts.append(f'<font name="Helvetica">{_esc(m.group(0))}</font>')
            last_end = end
        if last_end < len(raw):
            result_parts.append(_esc(raw[last_end:]))
        return "".join(result_parts)

    def _dim_name(self, name: str) -> str:
        """Get dimension name in the current language."""
        lookup = _DIM_NAME_MAP.get(name, name)
        translated = _DIM_NAME_MAPS.get(self._lang, {}).get(lookup)
        if not translated:
            translated = _DIM_NAME_MAPS.get(self._lang, {}).get(name, lookup)
        return self._maybe_reshape(translated)

    def _font_normal(self) -> str:
        """Normal-weight font for the current language (CJK-aware)."""
        return _FONTS_FOR_LANG.get(self._lang, _DEFAULT_FONTS)[0]

    def _font_bold(self) -> str:
        """Bold-weight font for the current language (CJK-aware)."""
        return _FONTS_FOR_LANG.get(self._lang, _DEFAULT_FONTS)[1]

    def _build_cover_page(self, result: AnalysisResult, cr: ConsultingReport | None = None) -> list:
        """Build Page 1: All-in-One Executive Summary Comparison Sheet (LVMH Quiet Luxury)."""
        from due_diligence_engine.report.generator import _determine_verdict, _extract_file_line

        t = self._t
        elements: list = []

        cover_title = ParagraphStyle(
            "CoverTitle",
            fontName=self._font_bold(),
            fontSize=20,
            leading=26,
            textColor=colors.white,
            alignment=1,
            spaceAfter=2 * mm,
        )
        cover_subtitle = ParagraphStyle(
            "CoverSubtitle",
            fontName=self._font_normal(),
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#38bdf8"),
            alignment=1,
            spaceAfter=2 * mm,
        )
        cover_center = ParagraphStyle(
            "CoverCenter",
            fontName=self._font_normal(),
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#e2e8f0"),
            alignment=1,
            spaceAfter=1.5 * mm,
        )
        cover_small = ParagraphStyle(
            "CoverSmall",
            fontName=self._font_normal(),
            fontSize=7.5,
            leading=11,
            textColor=colors.HexColor("#94a3b8"),
            alignment=1,
            spaceAfter=1 * mm,
        )
        tbl_header_style = ParagraphStyle(
            "CoverTblHeader",
            fontName=self._font_bold(),
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#38bdf8"),
        )
        tbl_cell_style = ParagraphStyle(
            "CoverTblCell",
            fontName=self._font_normal(),
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#f1f5f9"),
        )

        # Compact top spacer so the full 1-page Executive Summary Sheet fits on Page 1
        elements.append(Spacer(1, 0.4 * cm))

        elements.append(
            Paragraph(
                f'<font color="#0284c7" size="9"><b>ATLAS DDE · {self._esc_text(t["title_prefix"])}</b></font>',
                cover_center,
            )
        )
        elements.append(Paragraph(self._esc_text(t["report_title"]), cover_title))
        elements.append(Paragraph(self._esc_text(result.project_name), cover_subtitle))
        elements.append(
            HRFlowable(
                width="35%", thickness=0.6,
                color=COLOR_ACCENT,
                spaceAfter=3 * mm,
                hAlign="CENTER",
            )
        )

        if cr is None:
            cr = result.consulting_report

        overall_val: float | None = None
        grade = "?"
        recommendation = ""
        has_critical_blocker = False

        if cr is not None and cr.overall_score is not None:
            overall_val = float(cr.overall_score)
            grade = cr.grade or "?"
            rec = _PDF_GRADE_REC.get(self._lang, _PDF_GRADE_REC["en"])
            recommendation = self._maybe_reshape(rec.get(grade, ""))
            has_critical_blocker = any(
                isinstance(rf, dict) and str(rf.get("severity", "")).lower() == "critical"
                for rf in (cr.red_flags or [])
            )
        elif result.score is not None:
            overall_val = float(result.score.overall_score)
            grade = result.score.grade
            rec = _PDF_GRADE_REC.get(self._lang, _PDF_GRADE_REC["en"])
            recommendation = self._maybe_reshape(rec.get(grade, result.score.recommendation))
            has_critical_blocker = any(f.is_deal_breaker for f in result.score.red_flags)

        if overall_val is not None:
            verdict = _determine_verdict(overall_val, has_critical_blocker)
            verdict_hex = "#059669" if verdict == "GO" else ("#d97706" if verdict == "CONDITIONAL" else "#e11d48")
            grade_hex = GRADE_COLORS.get(grade, COLOR_ACCENT).hexval()

            grade_label = f'{t["grade_prefix"]}: {grade}'
            elements.append(
                Paragraph(
                    f'<font color="{grade_hex}" size="13"><b>{self._esc_text(grade_label)}</b></font>'
                    f'  ·  <font color="{verdict_hex}" size="12"><b>[{verdict}]</b></font>'
                    f'  <font color="#94a3b8" size="9.5">{self._esc_text(recommendation)}</font>',
                    cover_center,
                )
            )
            elements.append(Spacer(1, 1.5 * mm))

            # ① Large score number (kept as top-level Paragraph in elements for invariant test compatibility)
            score_style = ParagraphStyle(
                "CoverScore", fontName="Helvetica-Bold", fontSize=42,
                leading=48, alignment=1, textColor=colors.white,
            )
            score_text = (
                f'<font color="{colors.white.hexval()}">{overall_val:.0f}</font>'
                f'<font color="#94a3b8" size="16"> / 100</font>'
            )
            elements.append(Paragraph(score_text, score_style))
            elements.append(Spacer(1, 3 * mm))

            # ② Standard 5-Dimension Score Table & ③ Atlas 4-Axis (20/20/5/55) Score Table
            dim_rows = [[
                Paragraph("<b>② 5-Dimension Evaluation</b>", tbl_header_style),
                Paragraph("<b>Wt</b>", tbl_header_style),
                Paragraph("<b>Score</b>", tbl_header_style),
            ]]
            if cr is not None and cr.dimension_scores:
                for key, en_name in _DIM_NAME_MAP.items():
                    d_obj = cr.dimension_scores.get(key)
                    if not d_obj:
                        continue
                    sc_v = float(d_obj.score)
                    sc_hex = "#059669" if sc_v >= 75 else ("#0284c7" if sc_v >= 60 else ("#d97706" if sc_v >= 40 else "#e11d48"))
                    dim_rows.append([
                        Paragraph(self._esc_text(self._dim_name(en_name)), tbl_cell_style),
                        Paragraph("20%", tbl_cell_style),
                        Paragraph(f'<font color="{sc_hex}"><b>{sc_v:.0f}/100</b></font> (Lv.{d_obj.level})', tbl_cell_style),
                    ])
            elif result.score and result.score.dimensions:
                for dim in result.score.dimensions[:5]:
                    sc_v = float(dim.score)
                    sc_hex = "#059669" if sc_v >= 75 else ("#0284c7" if sc_v >= 60 else ("#d97706" if sc_v >= 40 else "#e11d48"))
                    dim_rows.append([
                        Paragraph(self._esc_text(self._dim_name(dim.name)), tbl_cell_style),
                        Paragraph(f"{dim.weight:.0%}", tbl_cell_style),
                        Paragraph(f'<font color="{sc_hex}"><b>{sc_v:.0f}/100</b></font>', tbl_cell_style),
                    ])

            atlas_rows = [[
                Paragraph("<b>③ Atlas 4-Axis (20/20/5/55)</b>", tbl_header_style),
                Paragraph("<b>Wt</b>", tbl_header_style),
                Paragraph("<b>Score / Status</b>", tbl_header_style),
            ]]
            if cr is not None and cr.atlas_four_axis and cr.atlas_four_axis.axes:
                for ax in cr.atlas_four_axis.axes[:4]:
                    ax_name = ax.name_ja if self._lang == "ja" and ax.name_ja else ax.name_en
                    ax_sc = float(ax.score)
                    ax_hex = "#059669" if ax_sc >= 75 else ("#0284c7" if ax_sc >= 60 else ("#d97706" if ax_sc >= 40 else "#e11d48"))
                    atlas_rows.append([
                        Paragraph(self._esc_text(ax_name), tbl_cell_style),
                        Paragraph(f"{ax.weight_pct:.0f}%", tbl_cell_style),
                        Paragraph(f'<font color="{ax_hex}"><b>{ax_sc:.0f}/100</b></font> (Lv.{ax.level})', tbl_cell_style),
                    ])
            else:
                code_res = result.code_analysis
                cons_res = result.consistency
                atlas_rows.extend([
                    [Paragraph("Performance", tbl_cell_style), Paragraph("20%", tbl_cell_style), Paragraph(f'<font color="#0284c7"><b>{overall_val:.0f}/100</b></font>', tbl_cell_style)],
                    [Paragraph("Stability", tbl_cell_style), Paragraph("20%", tbl_cell_style), Paragraph('<font color="#059669"><b>○ Tests+CI</b></font>' if code_res.has_tests else '<font color="#d97706"><b>⚠️ Check Tests</b></font>', tbl_cell_style)],
                    [Paragraph("Lightweight", tbl_cell_style), Paragraph("5%", tbl_cell_style), Paragraph(f"{code_res.dependency_count} deps", tbl_cell_style)],
                    [Paragraph("<b>Security Strength</b>", tbl_cell_style), Paragraph("<b>55%</b>", tbl_cell_style), Paragraph(f'<font color="#059669"><b>{cons_res.consistency_score:.0f}%</b></font>', tbl_cell_style)],
                ])

            sub_style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#0D131F")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#1e293b")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ])
            left_tbl = Table(dim_rows, colWidths=[46 * mm, 12 * mm, 24 * mm])
            left_tbl.setStyle(sub_style)
            right_tbl = Table(atlas_rows, colWidths=[46 * mm, 12 * mm, 24 * mm])
            right_tbl.setStyle(sub_style)

            grid_tbl = Table([[left_tbl, right_tbl]], colWidths=[85 * mm, 85 * mm])
            grid_tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(grid_tbl)
            elements.append(Spacer(1, 3.5 * mm))

            # ④ Investment / M&A Verdict & Top 3 Priority Risks Table
            risk_items: list[str] = []
            if cr is not None and cr.investment_thesis and cr.investment_thesis.key_risks:
                risk_items = [str(r) for r in cr.investment_thesis.key_risks[:3]]
            elif cr is not None and cr.red_flags:
                for rf in cr.red_flags[:3]:
                    if isinstance(rf, dict):
                        risk_items.append(f"[{str(rf.get('severity', 'HIGH')).upper()}] {rf.get('title', '')}")
            elif result.score and result.score.red_flags:
                for rf in result.score.red_flags[:3]:
                    risk_items.append(f"[{rf.severity.value.upper()}] {rf.title} ({_extract_file_line(rf)})")
            if not risk_items:
                risk_items = ["Zero critical/high code blockers identified."]

            risk_html = "<br/>".join(
                f'<font color="#e11d48">•</font> {self._esc_text(r[:110])}' for r in risk_items[:3]
            )
            verdict_rows = [
                [
                    Paragraph("<b>④ Executive Verdict</b>", tbl_header_style),
                    Paragraph("<b>Top 3 Priority Risks &amp; Conditions</b>", tbl_header_style),
                ],
                [
                    Paragraph(
                        f'<font color="{verdict_hex}" size="11"><b>{verdict}</b></font><br/>'
                        f'<font color="#94a3b8" size="7.5">{self._esc_text(recommendation)}</font>',
                        tbl_cell_style,
                    ),
                    Paragraph(risk_html, tbl_cell_style),
                ],
            ]
            verdict_tbl = Table(verdict_rows, colWidths=[48 * mm, 122 * mm])
            verdict_tbl.setStyle(sub_style)
            elements.append(verdict_tbl)
            elements.append(Spacer(1, 3 * mm))

        meta_bits = [
            f"{self._esc_text(t['analysis_id'])}: {self._esc_text(result.analysis_id)}",
            f"{self._esc_text(t['date'])}: {self._esc_text(result.timestamp.strftime('%Y-%m-%d %H:%M UTC'))}",
        ]
        if cr and cr.ai_model_used:
            meta_bits.append(f"{self._esc_text(t['ai_model'])}: {self._esc_text(cr.ai_model_used)}")
        elements.append(Paragraph("   ·   ".join(meta_bits), cover_small))

        if self._lang == "ar":
            note_style = ParagraphStyle(
                "CoverRTLNote", parent=cover_small,
                fontSize=7, leading=10, alignment=1,
                textColor=colors.HexColor("#94a3b8"),
            )
            rtl_note = (
                "ملاحظة: النص العربي مُشكَّل ويُقرأ من اليمين إلى اليسار، "
                "لكن تخطيط الصفحة يظل من اليسار إلى اليمين (التسميات يساراً والقيم يميناً) "
                "كما في سائر اللغات."
            )
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(self._maybe_reshape(rtl_note), note_style))

        return elements

    def _build_executive_summary(self, result: AnalysisResult) -> list:
        """Build the executive summary section."""
        s = self._styles
        t = self._t
        elements: list = []

        elements.append(Paragraph(t["exec_summary"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        score = result.score
        if score is not None:
            rec = _PDF_GRADE_REC.get(self._lang, _PDF_GRADE_REC["en"])
            recommendation = self._maybe_reshape(rec.get(score.grade, score.recommendation))
            elements.append(Paragraph(self._esc_text(recommendation), s["body"]))

            # Key metrics summary
            critical_count = sum(1 for f in score.red_flags if f.is_deal_breaker)
            high_count = sum(1 for f in score.red_flags if f.severity == Severity.HIGH)

            summary_data = [
                [t["metric"], t["value"]],
                [t["overall_score"], f"{score.overall_score:.0f}/100 ({score.grade})"],
                [t["total_red_flags"], str(len(score.red_flags))],
                [t["critical_flags"], str(critical_count)],
                [t["high_severity"], str(high_count)],
                [t["files_analyzed"], str(result.code_analysis.total_files)],
                [t["lines_of_code"], f"{result.code_analysis.total_lines:,}"],
                [t["languages"], str(len(result.code_analysis.languages))],
                [t["api_cost"], f"${result.total_cost_usd:.4f}"],
            ]

            table = Table(summary_data, colWidths=[7 * cm, 8 * cm])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
                ("FONTNAME", (0, 0), (-1, 0), self._font_bold()),
                ("FONTNAME", (0, 1), (-1, -1), self._font_normal()),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)
        else:
            elements.append(
                Paragraph(t["no_score"], s["body"])
            )

        return elements

    def _build_score_breakdown(self, result: AnalysisResult) -> list:
        """Build the score dimension breakdown table."""
        s = self._styles
        t = self._t
        elements: list = []

        score = result.score
        if score is None:
            return elements

        elements.append(Paragraph(t["score_breakdown"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        # Dimension table
        table_data = [[t["dimension"], t["score"], t["weight"], t["weighted_score"]]]
        for dim in score.dimensions:
            table_data.append([
                self._dim_name(dim.name),
                f"{dim.score:.0f}/100",
                f"{dim.weight:.0%}",
                f"{dim.weighted_score:.1f}",
            ])

        font_header = self._font_bold()
        font_body = self._font_normal()

        table = Table(table_data, colWidths=[6 * cm, 3 * cm, 3 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), font_header),
            ("FONTNAME", (0, 1), (-1, -1), font_body),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        # Dimension rationales
        elements.append(Spacer(1, 6 * mm))
        for dim in score.dimensions:
            elements.append(
                Paragraph(f"<b>{_esc(self._dim_name(dim.name))}</b> ({dim.score:.0f}/100)", s["body"])
            )
            elements.append(Paragraph(self._esc_text(dim.rationale), s["body_small"]))

        return elements

    def _build_ai_provider_section(self, result: AnalysisResult) -> list:
        """マルチAIプロバイダーの分析結果セクションを生成。"""
        s = self._styles
        t = self._t
        elements: list = []

        elements.append(Paragraph(t["ai_provider_analysis"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        # プロバイダーカラー
        provider_colors = {
            "claude": COLOR_ORANGE,
            "gemini": COLOR_ACCENT,
            "chatgpt": COLOR_GREEN,
        }

        # 各プロバイダーのサマリー
        for name, ai_result in result.ai_results.items():
            if ai_result.error:
                elements.append(Paragraph(
                    f"<b>{name.capitalize()}</b>: Error - {self._esc_text(ai_result.error)}",
                    s["body_small"],
                ))
                continue

            color = provider_colors.get(name, COLOR_TEXT)
            elements.append(Paragraph(
                f'<font color="{color.hexval()}"><b>{name.capitalize()}</b></font>'
                f' ({self._esc_text(ai_result.model_id)}) — '
                f'Verdict: <b>{self._esc_text(ai_result.verdict)}</b> | '
                f'Confidence: {ai_result.confidence:.0f}%',
                s["body"],
            ))
            if ai_result.executive_summary:
                elements.append(Paragraph(self._esc_text(ai_result.executive_summary), s["body_small"]))
            elements.append(Spacer(1, 3 * mm))

        # プロバイダー比較テーブル
        valid_providers = [
            (name, r) for name, r in result.ai_results.items()
            if r.error is None and r.dimension_scores
        ]

        if valid_providers:
            elements.append(Spacer(1, 4 * mm))
            elements.append(Paragraph(t["provider_score_comparison"], s["heading2"]))

            # v0.3: 5 dimensions (security_posture merged into architecture_quality)
            dim_keys = [
                "technical_originality", "technology_advancement",
                "implementation_depth", "architecture_quality",
                "claim_consistency",
            ]

            # ヘッダー行
            header = [t.get("dimension", "Dimension")]
            for name, _ in valid_providers:
                header.append(name.capitalize())
            header.append(t["avg_short"])

            table_data = [header]
            for key in dim_keys:
                row = [self._dim_name(key)]
                scores = []
                for _, r in valid_providers:
                    score_val = r.dimension_scores.get(key, 0)
                    row.append(f"{score_val:.0f}")
                    scores.append(score_val)
                avg = sum(scores) / len(scores) if scores else 0
                row.append(f"{avg:.0f}")
                table_data.append(row)

            # コスト行
            cost_row = [f"{t['api_cost']} (USD)"]
            total_cost = 0.0
            for _, r in valid_providers:
                cost_row.append(f"${r.cost_usd:.4f}")
                total_cost += r.cost_usd
            cost_row.append(f"${total_cost:.4f}")
            table_data.append(cost_row)

            n_cols = len(header)
            col_width = 15 * cm / n_cols
            col_widths = [col_width] * n_cols

            font_header = self._font_bold()
            font_body = self._font_normal()

            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
                ("FONTNAME", (0, 0), (-1, 0), font_header),
                ("FONTNAME", (0, 1), (-1, -1), font_body),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        return elements

    def _build_red_flags_section(self, result: AnalysisResult) -> list:
        """Build the priority-sorted 4-column Red Flags table (standard report)."""
        from due_diligence_engine.report.generator import _extract_file_line, _extract_one_line_fix

        s = self._styles
        t = self._t
        elements: list = []

        score = result.score
        if score is None or not score.red_flags:
            return elements

        elements.append(Paragraph(t["red_flags"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_RED, spaceAfter=4 * mm)
        )

        sev_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        sorted_flags = sorted(score.red_flags, key=lambda f: sev_order.get(f.severity, 99))

        hdr_style = ParagraphStyle(
            "RFHdr", fontName=self._font_bold(), fontSize=8, leading=11, textColor=COLOR_WHITE,
        )
        cell_style = ParagraphStyle(
            "RFCell", fontName=self._font_normal(), fontSize=8.5, leading=13, textColor=COLOR_TEXT,
        )

        rows = [[
            Paragraph("<b>Severity</b>", hdr_style),
            Paragraph("<b>Target (file:line)</b>", hdr_style),
            Paragraph("<b>Business Impact</b>", hdr_style),
            Paragraph("<b>Concrete 1-Line Fix Plan</b>", hdr_style),
        ]]
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ]

        for r_idx, flag in enumerate(sorted_flags, start=1):
            sev_val = flag.severity.value.lower()
            if sev_val == "critical":
                sev_badge = '<font color="#e11d48"><b>CRITICAL</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_ROSE_BG))
            elif sev_val == "high":
                sev_badge = '<font color="#d97706"><b>! HIGH</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_AMBER_BG))
            elif sev_val == "medium":
                sev_badge = '<font color="#0284c7"><b>MEDIUM</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_ACCENT_LIGHT))
            else:
                sev_badge = f'<font color="#059669"><b>{self._esc_text(sev_val.upper())}</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_SLATE_BG))

            rows.append([
                Paragraph(sev_badge, cell_style),
                Paragraph(f'<font name="Helvetica">{self._esc_text(_extract_file_line(flag))}</font>', cell_style),
                Paragraph(f"<b>{self._esc_text(flag.title)}</b><br/>{self._esc_text(flag.description)}", cell_style),
                Paragraph(self._esc_text(_extract_one_line_fix(flag)), cell_style),
            ])

        tbl = Table(rows, colWidths=[24 * mm, 36 * mm, 55 * mm, 50 * mm], repeatRows=1)
        tbl.setStyle(TableStyle(style_cmds))
        elements.append(tbl)
        return elements

    def _build_codebase_metrics(self, result: AnalysisResult) -> list:
        """Build the codebase metrics section."""
        s = self._styles
        t = self._t
        elements: list = []

        code = result.code_analysis

        elements.append(Paragraph(t["codebase_metrics"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        metrics_data = [
            [t["metric"], t["value"]],
            [t["total_files"], str(code.total_files)],
            [t["total_lines"], f"{code.total_lines:,}"],
            [t["languages"], ", ".join(f"{k} ({v})" for k, v in code.languages.items()) or "N/A"],
            [t["wrapper_ratio"], f"{code.api_wrapper_ratio:.0%}"],
            [t["test_coverage"], f"{code.test_coverage_estimate:.0%}"],
            [t["dependencies"], str(code.dependency_count)],
            [t["has_tests"], t["yes"] if code.has_tests else t["no"]],
            [t["has_cicd"], t["yes"] if code.has_ci_cd else t["no"]],
            [t["has_docs"], t["yes"] if code.has_documentation else t["no"]],
        ]

        font_header = self._font_bold()
        font_body = self._font_normal()

        table = Table(metrics_data, colWidths=[6 * cm, 9 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), font_header),
            ("FONTNAME", (0, 1), (-1, -1), font_body),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        # Code findings (no source code, only findings text)
        if code.findings:
            elements.append(Paragraph(t["key_findings"], s["heading2"]))
            for finding in code.findings[:20]:  # Limit to 20 findings
                elements.append(
                    Paragraph(f"&bull; {self._esc_text(finding)}", s["body_small"])
                )

        return elements

    def _build_git_forensics(self, result: AnalysisResult) -> list:
        """Build the git forensics section."""
        s = self._styles
        t = self._t
        elements: list = []

        git = result.git_forensics

        elements.append(Paragraph(t["git_forensics"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        git_data = [
            [t["metric"], t["value"]],
            [t["total_commits"], str(git.total_commits)],
            [t["unique_authors"], str(git.unique_authors)],
            [t["first_commit"], git.first_commit_date or "N/A"],
            [t["last_commit"], git.last_commit_date or "N/A"],
            [t["rush_ratio"], f"{git.rush_commit_ratio:.0%}"],
        ]

        font_header = self._font_bold()
        font_body = self._font_normal()

        table = Table(git_data, colWidths=[6 * cm, 9 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), font_header),
            ("FONTNAME", (0, 1), (-1, -1), font_body),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        if git.suspicious_patterns:
            elements.append(Paragraph(t["suspicious_patterns"], s["heading2"]))
            for pattern in git.suspicious_patterns:
                elements.append(
                    Paragraph(f"&bull; {self._esc_text(pattern)}", s["body_small"])
                )

        return elements

    def _build_consistency_section(self, result: AnalysisResult) -> list:
        """Build the claim consistency section."""
        s = self._styles
        t = self._t
        elements: list = []

        consistency = result.consistency

        elements.append(Paragraph(t["claim_consistency"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        consistency_data = [
            [t["metric"], t["value"]],
            [t["consistency_score"], f"{consistency.consistency_score:.0f}%"],
            [t["verified_claims"], str(len(consistency.verified_claims))],
            [t["unverified_claims"], str(len(consistency.unverified_claims))],
            [t["contradictions"], str(len(consistency.contradictions))],
        ]

        font_header = self._font_bold()
        font_body = self._font_normal()

        table = Table(consistency_data, colWidths=[6 * cm, 9 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), font_header),
            ("FONTNAME", (0, 1), (-1, -1), font_body),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        # 2-Column Company Claim vs. Code Evidence Comparison Table
        elements.append(Spacer(1, 5 * mm))
        hdr_style = ParagraphStyle(
            "ConsHdr", fontName=font_header, fontSize=8.5, leading=11, textColor=COLOR_WHITE,
        )
        cell_style = ParagraphStyle(
            "ConsCell", fontName=font_body, fontSize=8.5, leading=13, textColor=COLOR_TEXT,
        )
        comp_rows = [[
            Paragraph("<b>Web / Pitch Claim</b>", hdr_style),
            Paragraph("<b>Codebase Evidence (file:line) &amp; Verdict</b>", hdr_style),
        ]]
        comp_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]
        r_idx = 1
        for vc in consistency.verified_claims[:10]:
            comp_rows.append([
                Paragraph(self._esc_text(vc), cell_style),
                Paragraph('<font color="#059669"><b>[Verified]</b></font> Confirmed in repository AST &amp; configs', cell_style),
            ])
            comp_styles.append(("BACKGROUND", (1, r_idx), (1, r_idx), COLOR_EMERALD_BG))
            r_idx += 1
        for uc in consistency.unverified_claims[:10]:
            comp_rows.append([
                Paragraph(self._esc_text(uc), cell_style),
                Paragraph('<font color="#d97706"><b>[Partial]</b></font> No direct backing implementation found', cell_style),
            ])
            comp_styles.append(("BACKGROUND", (1, r_idx), (1, r_idx), COLOR_AMBER_BG))
            r_idx += 1
        for cc in consistency.contradictions[:10]:
            comp_rows.append([
                Paragraph(self._esc_text(cc), cell_style),
                Paragraph('<font color="#e11d48"><b>[Unimplemented]</b></font> Contradicts repository source tree', cell_style),
            ])
            comp_styles.append(("BACKGROUND", (1, r_idx), (1, r_idx), COLOR_ROSE_BG))
            r_idx += 1
        if len(comp_rows) > 1:
            comp_tbl = Table(comp_rows, colWidths=[72 * mm, 93 * mm], repeatRows=1)
            comp_tbl.setStyle(TableStyle(comp_styles))
            elements.append(comp_tbl)

        return elements

    def _build_cost_section(self, result: AnalysisResult) -> list:
        """Build the analysis cost breakdown section."""
        s = self._styles
        t = self._t
        elements: list = []

        elements.append(Paragraph(t["analysis_cost"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        elements.append(
            Paragraph(f"{t['total_api_cost']}: <b>${result.total_cost_usd:.4f}</b>", s["body"])
        )

        if result.model_usage:
            cost_data = [[t["model_tier"], t["input_tokens"], t["output_tokens"]]]
            for tier, usage in result.model_usage.items():
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                if input_tokens > 0 or output_tokens > 0:
                    cost_data.append([
                        tier.title(),
                        f"{input_tokens:,}",
                        f"{output_tokens:,}",
                    ])

            if len(cost_data) > 1:
                font_header = self._font_bold()
                font_body = self._font_normal()

                table = Table(cost_data, colWidths=[5 * cm, 5 * cm, 5 * cm])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
                    ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
                    ("FONTNAME", (0, 0), (-1, 0), font_header),
                    ("FONTNAME", (0, 1), (-1, -1), font_body),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]))
                elements.append(table)

        return elements

    def _build_purge_certificate(self, cert: PurgeCertificate) -> list:
        """Build the purge certificate page."""
        s = self._styles
        t = self._t
        elements: list = []

        elements.append(Spacer(1, 2 * cm))
        elements.append(
            Paragraph(
                f'<font color="#ef4444" size="20">{t["purge_cert_title"]}</font>',
                s["center"],
            )
        )
        elements.append(Spacer(1, 1 * cm))
        elements.append(
            HRFlowable(width="100%", thickness=2, color=COLOR_RED, spaceAfter=6 * mm)
        )

        elements.append(
            Paragraph(t["purge_cert_body"], s["center"])
        )
        elements.append(Spacer(1, 8 * mm))

        cert_data = [
            [t["field"], t["value"]],
            [t["certificate_id"], cert.certificate_id],
            [t["analysis_id"], cert.analysis_id],
            [t["project_name"], cert.project_name],
            [t["purge_timestamp"], cert.purge_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")],
            [t["files_purged"], str(cert.files_purged)],
            [t["bytes_overwritten"], f"{cert.bytes_overwritten:,}"],
            [t["deletion_method"], cert.method],
            [t["operator"], cert.operator],
        ]

        font_header = self._font_bold()
        font_body = self._font_normal()

        table = Table(cert_data, colWidths=[5 * cm, 10 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), font_header),
            ("FONTNAME", (0, 1), (0, -1), font_header),
            ("FONTNAME", (1, 1), (-1, -1), font_body),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 1 * cm))

        # Verification hash (truncated for readability)
        if cert.verification_hash:
            display_hash = cert.verification_hash[:64]
            if len(cert.verification_hash) > 64:
                display_hash += "..."
            elements.append(
                Paragraph(
                    f"{t['verification_hash']}: <font name='Courier' size='8'>{display_hash}</font>",
                    s["body_small"],
                )
            )

        elements.append(Spacer(1, 1 * cm))
        elements.append(Paragraph(t["purge_footer"], s["center"]))

        return elements

    # Atlas Associates Inc. credit — hardcoded, not configurable.
    # This attribution is required by the license and must not be removed.
    _CREDIT = "Powered by Atlas DDE (Due Diligence Engine) \u2014 Takayuki Miyano / Atlas Associates Inc"

    def _add_cover_bg(self, canvas, doc) -> None:
        """Draw Quiet Luxury dark background + Atlas DDE branding on Page 1."""
        canvas.saveState()
        page_width, page_height = A4

        # Full-page dark background
        canvas.setFillColor(COLOR_BG_DARK)
        canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        # Top hairline accent bar (#0284c7)
        canvas.setFillColor(COLOR_ACCENT)
        canvas.rect(0, page_height - 4 * mm, page_width, 4 * mm, fill=1, stroke=0)

        # Atlas DDE logo text (top-left)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(2 * cm, page_height - 1.5 * cm, "ATLAS DDE")
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#38bdf8"))
        canvas.drawString(4.3 * cm, page_height - 1.5 * cm, "EXECUTIVE TECHNICAL DUE DILIGENCE")

        # Decorative thin line
        canvas.setStrokeColor(colors.HexColor("#1e293b"))
        canvas.setLineWidth(0.6)
        canvas.line(2 * cm, page_height - 1.85 * cm, page_width - 2 * cm, page_height - 1.85 * cm)

        # Bottom credit
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawCentredString(
            page_width / 2,
            1.2 * cm,
            self._CREDIT,
        )

        # Page number (lang-aware font: the page label may be CJK for ja/zh/ko)
        page_label = self._t.get("page", "Page")
        canvas.setFont(self._font_normal(), 7)
        canvas.drawRightString(
            page_width - 2 * cm,
            1.2 * cm,
            f"{page_label} {doc.page}",
        )

        canvas.restoreState()

    def _add_footer(self, canvas, doc) -> None:
        """Add NDA compliance footer + Atlas Associates credit to every page."""
        canvas.saveState()
        page_width, page_height = A4

        # Atlas Associates credit (left side, every page)
        canvas.setFont("Helvetica", 6)
        canvas.setFillColor(COLOR_TEXT_DIM)
        canvas.drawString(
            2 * cm,
            0.8 * cm,
            self._CREDIT,
        )

        # NDA notice
        font_name = self._font_normal()
        canvas.setFont(font_name, 7)
        canvas.setFillColor(COLOR_TEXT_DIM)
        canvas.drawCentredString(
            page_width / 2,
            1.2 * cm,
            self._t.get("nda_footer", "CONFIDENTIAL"),
        )

        # Page number (lang-aware font: the page label may be CJK for ja/zh/ko)
        page_label = self._t.get("page", "Page")
        canvas.setFont(self._font_normal(), 7)
        canvas.drawRightString(
            page_width - 2 * cm,
            1.2 * cm,
            f"{page_label} {doc.page}",
        )

        # Separator line
        canvas.setStrokeColor(COLOR_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, 1.8 * cm, page_width - 2 * cm, 1.8 * cm)

        canvas.restoreState()

    # ===================================================================
    # Consulting Report build methods
    # ===================================================================

    def _build_score_dashboard(self, cr) -> list:
        """Score dashboard with overall score + 5-dimension horizontal bar chart."""
        t = self._t
        s = self._styles
        elements: list = []

        # Title
        elements.append(Paragraph(t["score_dashboard"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )
        elements.append(
            Paragraph(t["score_dashboard_subtitle"], s["body_dim"])
        )
        elements.append(Spacer(1, 6 * mm))

        # --- Overall score large display ---
        grade = cr.grade or "?"
        grade_color = GRADE_COLORS.get(grade, COLOR_TEXT_DIM)

        # Grade label first (above score to prevent overlap)
        grade_label = f'{t["grade_prefix"]}: {grade}'
        rec = _PDF_GRADE_REC.get(self._lang, _PDF_GRADE_REC["en"])
        recommendation = self._maybe_reshape(rec.get(grade, ""))
        grade_line = (
            f'<font color="{grade_color.hexval()}" size="14"><b>{self._esc_text(grade_label)}</b></font>'
            f'  <font color="{COLOR_TEXT_DIM.hexval()}" size="10">{self._esc_text(recommendation)}</font>'
        )
        elements.append(Paragraph(grade_line, s["center"]))
        elements.append(Spacer(1, 2 * mm))

        # Large score — use explicit leading to match font size
        score_large_style = ParagraphStyle(
            "DashboardScoreLarge", fontName="Helvetica-Bold", fontSize=48,
            leading=56, alignment=1, textColor=grade_color,
        )
        overall_text = (
            f'{cr.overall_score:.0f}'
            f'<font color="{COLOR_TEXT_DIM.hexval()}" size="18"> / 100</font>'
        )
        elements.append(Paragraph(overall_text, score_large_style))
        elements.append(Spacer(1, 8 * mm))

        # --- 5-Dimension bar chart (v0.3: Security Posture merged into Architecture Quality) ---
        dim_name_map = _DIM_NAME_MAP
        _dim_desc_en = {
            "technical_originality": "Novelty of algorithms, patents, and proprietary tech",
            "technology_advancement": "Modernity of stack, frameworks, and tooling",
            "implementation_depth": "Test coverage, error handling, production readiness",
            "architecture_quality": "Code structure + security maturity (encryption, auth, vulns)",
            "claim_consistency": "Alignment between marketing claims and actual code",
        }
        _dim_desc_ja = {
            "technical_originality": "アルゴリズム・特許・独自技術の新規性",
            "technology_advancement": "技術スタック・フレームワークの先進性",
            "implementation_depth": "テストカバレッジ・エラー処理・本番運用品質",
            "architecture_quality": "コード構造 + セキュリティ成熟度（暗号化・認証・脆弱性）",
            "claim_consistency": "マーケティング主張と実装コードの整合性",
        }
        _dim_desc_es = {
            "technical_originality": "Novedad de los algoritmos, patentes y tecnología propietaria",
            "technology_advancement": "Modernidad del stack, frameworks y herramientas",
            "implementation_depth": "Cobertura de pruebas, manejo de errores y preparación para producción",
            "architecture_quality": "Estructura del código + madurez de seguridad (cifrado, autenticación, vulnerabilidades)",
            "claim_consistency": "Alineación entre las afirmaciones de marketing y el código real",
        }
        _dim_desc_maps = {"en": _dim_desc_en, "ja": _dim_desc_ja, "es": _dim_desc_es, **_DIM_DESC_PACKS}
        weights = {
            "technical_originality": 0.20,
            "technology_advancement": 0.20,
            "implementation_depth": 0.20,
            "architecture_quality": 0.20,
            "claim_consistency": 0.20,
        }

        # Collect dimension data
        dims = []
        for key, en_name in dim_name_map.items():
            dim = cr.dimension_scores.get(key)
            if not dim:
                continue
            name = self._dim_name(en_name)
            desc = self._maybe_reshape(_dim_desc_maps.get(self._lang, _dim_desc_en).get(key, ""))
            w = weights.get(key, 0)
            dims.append((name, dim.score, dim.level, w, desc))

        if not dims:
            return elements

        # Drawing dimensions
        bar_max_w = 250  # max bar width in points (narrowed to widen label area)
        row_h = 44       # height per row (increased for description line)
        label_w = 170    # label area width (widened to fit long JA labels w/o overlap)
        chart_w = label_w + bar_max_w + 80  # total width
        chart_h = len(dims) * row_h + 10

        d = Drawing(chart_w, chart_h)

        for i, (name, score, level, weight, desc) in enumerate(dims):
            y = chart_h - (i + 1) * row_h + 14

            # Dimension label (left, bold)
            font_name = self._font_bold()
            d.add(String(0, y + 4, name, fontName=font_name, fontSize=8.5,
                         fillColor=COLOR_TEXT))

            # Dimension description (below label, small gray text — truncated to label width)
            desc_font = self._font_normal()
            desc_fit = desc if len(desc) <= 22 else desc[:21] + "…"
            d.add(String(0, y - 8, desc_fit, fontName=desc_font, fontSize=6.5,
                         fillColor=COLOR_TEXT_DIM))

            # Background bar (gray track) — rounded for a modern pill look
            d.add(Rect(label_w, y, bar_max_w, 16, rx=8, ry=8,
                        fillColor=colors.HexColor("#eef2f7"),
                        strokeColor=None, strokeWidth=0))

            # Score bar (Arc brand: black + sky blue dominant)
            bar_w = max(2, (score / 100) * bar_max_w)
            if score >= 75:
                bar_color = COLOR_ACCENT                  # Arc sky #5271FF
            elif score >= 50:
                bar_color = COLOR_ACCENT_DARK             # Arc sky darker
            elif score >= 30:
                bar_color = colors.HexColor("#000000")    # pure black
            else:
                bar_color = colors.HexColor("#6b2a2a")    # muted red (warning)
            bar_radius = min(8, bar_w / 2)  # clamp radius so thin bars don't distort
            d.add(Rect(label_w, y, bar_w, 16, rx=bar_radius, ry=bar_radius,
                        fillColor=bar_color,
                        strokeColor=None, strokeWidth=0))

            # Score text (right of bar)
            score_str = f"{score:.0f}  Lv.{level}  ({weight:.0%})"
            d.add(String(label_w + bar_max_w + 6, y + 3, score_str,
                         fontName="Helvetica", fontSize=8,
                         fillColor=COLOR_TEXT_DIM))

        elements.append(d)
        elements.append(Spacer(1, 8 * mm))

        # Weighted total line
        weighted_total = sum(sc * w for _, sc, _, w, _ in dims)
        _wt_label = self._t.get("weighted_score", "Weighted Total Score")
        total_text = f"{_wt_label}: <b>{weighted_total:.1f}</b> / 100"
        elements.append(Paragraph(total_text, s["body"]))

        # Score barometer
        elements.append(Spacer(1, 6 * mm))
        barometer = Drawing(chart_w, 40)
        # Track
        barometer.add(Rect(label_w, 15, bar_max_w, 10,
                           fillColor=colors.HexColor("#e2e8f0"),
                           strokeColor=None, strokeWidth=0))
        # Colored segments (Arc brand: black→sky blue gradient, red for fail)
        segments = [
            (0, 40, colors.HexColor("#6b2a2a")),       # muted red (F)
            (40, 60, colors.HexColor("#000000")),      # black (D)
            (60, 75, colors.HexColor("#1a1a2e")),      # near-black (C)
            (75, 90, COLOR_ACCENT_DARK),               # Arc sky darker (B)
            (90, 100, COLOR_ACCENT),                   # Arc sky (A)
        ]
        for lo, hi, clr in segments:
            x = label_w + (lo / 100) * bar_max_w
            w = ((hi - lo) / 100) * bar_max_w
            barometer.add(Rect(x, 15, w, 10, fillColor=clr,
                               strokeColor=None, strokeWidth=0))

        # Position marker
        marker_x = label_w + (cr.overall_score / 100) * bar_max_w
        barometer.add(Rect(marker_x - 1.5, 12, 3, 16,
                           fillColor=COLOR_TEXT, strokeColor=None, strokeWidth=0))

        # Grade labels
        grade_labels = [("F", 20), ("D", 50), ("C", 67.5), ("B", 82.5), ("A", 95)]
        for g_label, pos in grade_labels:
            x = label_w + (pos / 100) * bar_max_w
            barometer.add(String(x - 3, 2, g_label, fontName="Helvetica-Bold",
                                 fontSize=8, fillColor=COLOR_TEXT_DIM))

        elements.append(barometer)

        return elements

    def _collect_radar_data(self, cr) -> list:
        """(short localized dimension name, score) pairs for the radar chart.

        Shared source of truth with the score dashboard so the two views never
        drift; labels strip the parenthetical from the ENGLISH key *before*
        localization so RTL (Arabic) reshaping stays intact.
        """
        radar_data: list[tuple[str, float]] = []
        for key, en_name in _DIM_NAME_MAP.items():
            dim = cr.dimension_scores.get(key)
            if not dim:
                continue
            short = self._dim_name(en_name.split(" (")[0])
            radar_data.append((short, dim.score))
        return radar_data

    def _build_radar_drawing(self, radar_data: list, scale: float = 1.0) -> "Drawing | None":
        """Pentagon radar (spider) chart of the dimension scores.

        Consulting-report staple: shows the balance/skew of the 5 dimensions
        at a glance. ``scale`` enlarges the whole drawing for the dedicated
        visual-summary page (1.0 = the original 300×200 footprint).
        """
        import math

        if len(radar_data) < 3:
            return None
        n = len(radar_data)
        cx, cy, radius = 150.0 * scale, 96.0 * scale, 62.0 * scale
        d = Drawing(300 * scale, 200 * scale)

        def pt(i: int, r: float) -> tuple[float, float]:
            ang = math.radians(90 - 360.0 * i / n)  # start at top, clockwise
            return cx + r * math.cos(ang), cy + r * math.sin(ang)

        # Grid rings (25/50/75/100) + spokes
        grid = colors.HexColor("#e2e8f0")
        for frac in (0.25, 0.5, 0.75, 1.0):
            ring: list[float] = []
            for i in range(n):
                x, y = pt(i, radius * frac)
                ring.extend((x, y))
            d.add(Polygon(ring, strokeColor=grid, strokeWidth=0.75, fillColor=None))
        for i in range(n):
            x, y = pt(i, radius)
            d.add(Line(cx, cy, x, y, strokeColor=grid, strokeWidth=0.75))

        # Score polygon — translucent Arc-sky fill + solid outline + dots
        pts: list[float] = []
        for i, (_, score) in enumerate(radar_data):
            x, y = pt(i, radius * max(score, 2.0) / 100.0)
            pts.extend((x, y))
        d.add(Polygon(pts, fillColor=colors.Color(82 / 255, 113 / 255, 1.0, alpha=0.30),
                      strokeColor=COLOR_ACCENT, strokeWidth=1.5))
        for j in range(0, len(pts), 2):
            d.add(Circle(pts[j], pts[j + 1], 2.2 * scale,
                         fillColor=COLOR_ACCENT, strokeColor=None, strokeWidth=0))

        # Vertex labels: short dimension name + score
        font = self._font_normal()
        for i, (short, score) in enumerate(radar_data):
            label = short if len(short) <= 18 else short[:17] + "…"
            x, y = pt(i, radius + 12 * scale)
            anchor = "middle"
            if x > cx + 4:
                anchor = "start"
            elif x < cx - 4:
                anchor = "end"
            dy = 1 if y >= cy else -7
            d.add(String(x, y + dy, f"{label}  {score:.0f}",
                         fontName=font, fontSize=6.5 * scale,
                         fillColor=COLOR_TEXT_DIM, textAnchor=anchor))
        return d

    def _build_data_freshness_box(self, cr) -> list:
        """Provenance box: surfaces the STEP 0 live-web-research metadata.

        Makes the freshness guarantee visible in the PDF itself — search date
        and query/source counts when web research ran, or a clearly marked
        training-data-only warning when it did not.
        """
        df = getattr(cr, "data_freshness", None)
        if df is None:
            return []
        t = self._t
        s = self._styles

        title = Paragraph(f"<b>{t['data_freshness_title']}</b>", s["body_small"])
        if df.web_search_performed:
            parts = []
            if df.search_date:
                parts.append(f"{t['df_search_date']}: {self._esc_text(df.search_date)}")
            parts.append(f"{t['df_queries']}: {len(df.queries_executed)}")
            parts.append(f"{t['df_sources']}: {len(df.sources_consulted)}")
            detail = Paragraph("   ·   ".join(parts), s["body_small"])
            edge = COLOR_ACCENT
        else:
            warn = df.data_cutoff_warning or t["df_no_web_warning"]
            detail = Paragraph(
                f'<font color="{COLOR_RED.hexval()}">{self._esc_text(warn)}</font>', s["body_small"],
            )
            edge = COLOR_RED

        box = Table([[title], [detail]], colWidths=[430])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ("LINEBEFORE", (0, 0), (0, -1), 2, edge),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
        ]))
        return [box]

    def _build_visual_summary_page(self, cr) -> list:
        """Dedicated 'Visual Summary' page: enlarged 5-dimension radar chart +
        the STEP 0 data-provenance box.

        Split out of the score dashboard so neither element gets pushed across a
        page break (which previously left the dashboard half-empty and the radar
        stranded on a near-blank page).
        """
        t = self._t
        s = self._styles

        radar = self._build_radar_drawing(self._collect_radar_data(cr), scale=1.3)
        df_flow = self._build_data_freshness_box(cr)
        if radar is None and not df_flow:
            return []  # nothing to show → caller skips the PageBreak

        elements: list = [
            Paragraph(t["visual_summary"], s["heading1"]),
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm),
            Paragraph(t["visual_summary_subtitle"], s["body_dim"]),
            Spacer(1, 8 * mm),
        ]
        if radar is not None:
            radar.hAlign = "CENTER"
            elements.append(radar)
        if df_flow:
            elements.append(Spacer(1, 8 * mm))
            elements.extend(df_flow)
        return elements

    def _build_source_appendix_page(self, cr) -> list:
        """Appendix listing the actual live-web sources consulted during STEP 0.

        Makes the 'sources are traceable' claim provable from the PDF alone.
        Long URLs wrap character-by-character (wordWrap='CJK'); the table
        auto-paginates with a repeated header for large source lists.
        """
        df = getattr(cr, "data_freshness", None)
        if df is None:
            return []
        # No appendix when web research never ran — the red provenance box on the
        # visual-summary page already states that; an empty URL list is just noise.
        if not df.web_search_performed and not df.sources_consulted:
            return []

        t = self._t
        s = self._styles
        elements: list = [
            Paragraph(t["source_appendix_title"], s["heading1"]),
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm),
            Paragraph(t["source_appendix_subtitle"], s["body_dim"]),
        ]
        if df.search_date:
            elements.append(Spacer(1, 2 * mm))
            elements.append(
                Paragraph(f"{t['src_verified_on']}: {self._esc_text(df.search_date)}", s["body_small"])
            )
        elements.append(Spacer(1, 4 * mm))

        if not df.sources_consulted:
            elements.append(Paragraph(t["src_none"], s["body_dim"]))
            return elements

        # URLs are always ASCII/LTR — render them in Helvetica, NOT the language
        # font. The Arabic font (NotoNaskhArabic) has no Latin glyphs, so a
        # localized font would make every URL invisible in `ar` reports.
        url_style = ParagraphStyle(
            "SourceURL", parent=s["body_small"], fontName="Helvetica",
            fontSize=7.5, leading=10, wordWrap="CJK",
        )
        hdr_style = ParagraphStyle(
            "SourceHdr", parent=s["body_small"], fontName=self._font_bold(),
            fontSize=8, textColor=COLOR_TEXT,
        )
        rows = [[Paragraph(t["src_col_num"], hdr_style),
                 Paragraph(t["src_col_url"], hdr_style)]]
        for i, url in enumerate(df.sources_consulted, 1):
            rows.append([Paragraph(str(i), url_style), Paragraph(_esc(url), url_style)])

        table = Table(rows, colWidths=[28, 422], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_LIGHT_BG),
            ("LINEBELOW", (0, 0), (-1, 0), 0.75, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (1, 0), (1, -1), "LEFT"),  # URLs read LTR even in RTL reports
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        return elements

    def _build_business_summary(self, cr) -> list:
        """Executive business summary page."""
        from due_diligence_engine.models import ConsultingReport

        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["business_summary"], s["heading1"]))
        elements.append(Spacer(1, 6 * mm))

        # AI model attribution
        if cr.ai_model_used:
            elements.append(
                Paragraph(f"{t['ai_model']}: {self._esc_text(cr.ai_model_used)}", s["body_dim"])
            )
            elements.append(Spacer(1, 4 * mm))

        # Grade badge
        grade = cr.grade or "N/A"
        grade_color = GRADE_COLORS.get(grade, COLOR_TEXT_DIM)
        score_text = f"{cr.overall_score:.0f}/100 — {t['grade_prefix']}: {grade}"
        elements.append(
            Paragraph(
                f'<font color="{grade_color.hexval()}">{self._esc_text(score_text)}</font>',
                s["heading2"],
            )
        )
        elements.append(Spacer(1, 6 * mm))

        # Business summary text
        if cr.executive_summary_business:
            for para in cr.executive_summary_business.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(self._esc_text(para), s["body"]))
                    elements.append(Spacer(1, 3 * mm))

        # Technical summary
        if cr.executive_summary:
            elements.append(Spacer(1, 4 * mm))
            elements.append(
                Paragraph(t.get("exec_summary", "Executive Summary"), s["heading2"])
            )
            elements.append(Spacer(1, 3 * mm))
            for para in cr.executive_summary.split("\n\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(self._esc_text(para), s["body"]))
                    elements.append(Spacer(1, 3 * mm))

        return elements

    def _build_swot_page(self, cr) -> list:
        """SWOT analysis as visual 2×2 grid with overflow protection (v0.3.1 fix).

        Uses ReportLab Table + KeepInFrame to ENFORCE cell boundaries:
        - Colored header bar (Strengths=green, Weaknesses=gray, Opportunities=Arc sky, Threats=red)
        - Cell body content is CLIPPED if it exceeds the fixed row height (no bleeding
          into adjacent cells like in v0.3.0)
        - Max 3 items per cell + 180-char truncation per item
        """
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle, KeepInFrame

        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["swot_analysis"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        swot = cr.swot
        # 4 quadrants: (label, items, header color)
        quadrants = [
            (t["strengths"], swot.strengths, colors.HexColor("#2d5a3d")),       # green
            (t["weaknesses"], swot.weaknesses, colors.HexColor("#4a4a4a")),     # dark gray
            (t["opportunities"], swot.opportunities, COLOR_ACCENT),             # Arc sky
            (t["threats"], swot.threats, colors.HexColor("#6b2a2a")),           # muted red
        ]

        # Style for cell content
        font_header = self._font_bold()
        font_body = self._font_normal()
        # Colored header — rendered as a separate "tag" row above body
        cell_header_style = ParagraphStyle(
            "SWOTHeader", fontName=font_header, fontSize=11,
            textColor=COLOR_WHITE, leading=14, alignment=TA_LEFT,
            leftIndent=0, rightIndent=0,
            spaceBefore=0, spaceAfter=0,
        )
        # Body items — smaller font than before (8pt) + tighter leading (11)
        cell_item_style = ParagraphStyle(
            "SWOTItem", fontName=font_body, fontSize=8,
            textColor=COLOR_TEXT, leading=11,
            spaceAfter=3, leftIndent=2, rightIndent=2,
        )
        cell_extra_style = ParagraphStyle(
            "SWOTExtra", fontName=font_body, fontSize=7.5,
            textColor=COLOR_TEXT_DIM, leading=10,
            spaceAfter=3, leftIndent=8, rightIndent=2,
        )

        def _truncate(s: str, n: int = 180) -> str:
            """Truncate long strings with ellipsis to prevent cell overflow."""
            if not s:
                return ""
            s = s.strip()
            return s if len(s) <= n else s[: n - 1] + "…"

        def _build_cell(title: str, items: list, color_hex) -> "KeepInFrame":
            """Build one SWOT quadrant cell wrapped in KeepInFrame (mode=shrink)."""
            cell_flow: list = []
            # Colored header strip (background via a small Table, not <para>)
            header_row = RLTable(
                [[Paragraph(f"<b>{title}</b>", cell_header_style)]],
                colWidths=[82 * mm - 4],
            )
            header_row.setStyle(RLTableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), color_hex),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            cell_flow.append(header_row)
            cell_flow.append(Spacer(1, 2))

            if not items:
                cell_flow.append(Paragraph("—", cell_item_style))
            else:
                # Max 3 items per cell to fit within fixed row height
                for item in items[:3]:
                    point = _truncate(item.point, 80)
                    explanation = _truncate(item.explanation, 180)
                    bullet = f"<b>{self._esc_text(point)}</b>: {self._esc_text(explanation)}"
                    cell_flow.append(Paragraph(f"• {bullet}", cell_item_style))

                    extra = (
                        item.business_analogy
                        or item.business_impact
                        or item.potential_value
                        or item.mitigation
                    )
                    if extra:
                        cell_flow.append(
                            Paragraph(f"<i>{self._esc_text(_truncate(extra, 140))}</i>", cell_extra_style)
                        )

            # KeepInFrame clips content to fit cell (mode="shrink" → auto-scale down if overflow)
            return KeepInFrame(
                maxWidth=82 * mm - 4,
                maxHeight=110 * mm - 4,
                content=cell_flow,
                mode="shrink",  # shrink to fit, never overflow
                hAlign="LEFT",
                vAlign="TOP",
            )

        # Build 2×2 table data
        cells = [_build_cell(title, items, color) for title, items, color in quadrants]
        table_data = [
            [cells[0], cells[1]],   # Strengths | Weaknesses
            [cells[2], cells[3]],   # Opportunities | Threats
        ]

        col_w = 82 * mm
        row_h = 110 * mm
        tbl = RLTable(
            table_data,
            colWidths=[col_w, col_w],
            rowHeights=[row_h, row_h],
        )
        tbl.setStyle(RLTableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ]))
        elements.append(tbl)

        return elements

    def _build_consulting_scores(self, cr) -> list:
        """Dimension scores from consulting report with business explanations."""
        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["score_breakdown"], s["heading1"]))
        elements.append(Spacer(1, 6 * mm))

        # v0.3: 5 dimensions, Security Posture merged into Architecture Quality
        dim_name_map = {
            "technical_originality": "Technical Originality",
            "technology_advancement": "Technology Advancement",
            "implementation_depth": "Implementation Depth",
            "architecture_quality": "Architecture Quality (incl. Security)",
            "claim_consistency": "Claim Consistency",
        }

        weights = {
            "technical_originality": 0.20,
            "technology_advancement": 0.20,
            "implementation_depth": 0.20,
            "architecture_quality": 0.20,
            "claim_consistency": 0.20,
        }

        # Score table (use Paragraph cells for proper CID font rendering)
        cell_style_h = ParagraphStyle(
            "ScoreH", fontName=s["heading1"].fontName, fontSize=9,
            textColor=COLOR_WHITE, leading=12, alignment=1,
        )
        cell_style_name = ParagraphStyle(
            "ScoreName", fontName=s["heading1"].fontName, fontSize=9,
            textColor=COLOR_TEXT, leading=12,
        )
        cell_style_val = ParagraphStyle(
            "ScoreVal", fontName="Helvetica", fontSize=9,
            textColor=COLOR_TEXT, leading=12, alignment=1,
        )

        header = [
            Paragraph(t["dimension"], ParagraphStyle("DimH", parent=cell_style_h, alignment=0)),
            Paragraph(t["score"], cell_style_h),
            Paragraph("Lv.", cell_style_h),
            Paragraph(t["weight"], cell_style_h),
            Paragraph(t["weighted_score"], cell_style_h),
        ]
        rows = [header]

        for key in dim_name_map:
            dim = cr.dimension_scores.get(key)
            if not dim:
                continue
            name = self._dim_name(dim_name_map[key])
            w = weights.get(key, 0)
            rows.append([
                Paragraph(name, cell_style_name),
                Paragraph(f"{dim.score:.0f}", cell_style_val),
                Paragraph(f"Lv.{dim.level}", cell_style_val),
                Paragraph(f"{w:.0%}", cell_style_val),
                Paragraph(f"{dim.score * w:.1f}", cell_style_val),
            ])

        if len(rows) > 1:
            table = Table(rows, colWidths=[140, 50, 40, 50, 70])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_SURFACE),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_WHITE]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 6 * mm))

        # Detailed rationale per dimension — wrapped in KeepTogether to prevent
        # orphans (e.g., heading at bottom of page with body on next page).
        for key in dim_name_map:
            dim = cr.dimension_scores.get(key)
            if not dim or not dim.rationale:
                continue
            name = self._dim_name(dim_name_map[key])

            block: list = [
                Paragraph(f"<b>{self._esc_text(name)}</b> — Lv.{dim.level} {self._esc_text(dim.label)}", s["body"]),
                Paragraph(self._esc_text(dim.rationale), s["body"]),
            ]
            if dim.business_explanation:
                block.append(Paragraph(f"<i>{self._esc_text(dim.business_explanation)}</i>", s["body_dim"]))
            if dim.enables:
                block.append(Paragraph(f"{t['enables']}: {self._esc_text(dim.enables)}", s["body_dim"]))
            block.append(Spacer(1, 4 * mm))
            elements.append(KeepTogether(block))

        return elements

    def _build_tech_level_page(self, cr) -> list:
        """Tech level summary with visual gauge."""
        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph(t["tech_level"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )

        tls = cr.tech_level_summary
        if not tls:
            return elements

        try:
            level = int(float(tls.get("overall_level", 0) or 0))
        except (ValueError, TypeError):
            level = 0
        label = tls.get("overall_label", "")
        explanation = tls.get("plain_explanation", "")

        # ── Per-dimension tech levels (v0.3: 5 dimensions) ──
        # Shows a compact horizontal bar per dimension for visual richness.
        dim_name_map = {
            "technical_originality": "Technical Originality",
            "technology_advancement": "Technology Advancement",
            "implementation_depth": "Implementation Depth",
            "architecture_quality": "Architecture Quality (incl. Security)",
            "claim_consistency": "Claim Consistency",
        }
        dim_levels: list[tuple[str, int, str]] = []
        for key, en_name in dim_name_map.items():
            dim = cr.dimension_scores.get(key)
            if not dim:
                continue
            display_name = self._dim_name(en_name)
            dim_levels.append((display_name, int(dim.level or 0), dim.label or ""))

        if dim_levels:
            label_font = self._font_bold()
            val_font = "Helvetica-Bold"
            label_w = 172
            seg_w = 22
            gap = 2
            row_h = 26
            chart_w = label_w + 10 * (seg_w + gap) + 80
            chart_h = len(dim_levels) * row_h + 6

            dgrid = Drawing(chart_w, chart_h)
            for i, (name, lv, lbl) in enumerate(dim_levels):
                y = chart_h - (i + 1) * row_h + 6
                # Dimension name (left)
                dgrid.add(String(0, y + 4, name, fontName=label_font, fontSize=8.5,
                                 fillColor=COLOR_TEXT))
                # 10-segment gauge
                for j in range(10):
                    x = label_w + j * (seg_w + gap)
                    if j < lv:
                        fill = COLOR_ACCENT if lv >= 7 else (
                            COLOR_ACCENT_DARK if lv >= 5 else colors.HexColor("#000000")
                        )
                    else:
                        fill = colors.HexColor("#e2e8f0")
                    dgrid.add(Rect(x, y, seg_w, 14, rx=3, ry=3,
                                   fillColor=fill, strokeColor=None, strokeWidth=0))
                # Lv.X/10 text right
                text_x = label_w + 10 * (seg_w + gap) + 6
                dgrid.add(String(text_x, y + 3, f"Lv.{lv}/10",
                                 fontName=val_font, fontSize=8.5,
                                 fillColor=COLOR_TEXT_DIM))
            elements.append(dgrid)
            elements.append(Spacer(1, 6 * mm))

        # ── Overall tech level gauge (larger, summary) ──
        overall_label = t.get("tech_level", "Overall Tech Level")
        elements.append(Paragraph(f"<b>{self._esc_text(overall_label)}</b>", s["heading2"]))

        gauge_w = 380
        gauge_h = 30
        seg_w = 32
        seg_h = 20
        gap = 3

        d = Drawing(gauge_w, gauge_h)
        for i in range(10):
            x = i * (seg_w + gap)
            if i < level:
                fill = COLOR_ACCENT
            else:
                fill = colors.HexColor("#e2e8f0")
            d.add(Rect(x, 4, seg_w, seg_h, rx=3, ry=3,
                        fillColor=fill, strokeColor=None, strokeWidth=0))

        text_x = 10 * (seg_w + gap) + 8
        level_str = f"Lv.{level}/10"
        d.add(String(text_x, 10, level_str,
                     fontName="Helvetica-Bold", fontSize=12,
                     fillColor=COLOR_TEXT))
        elements.append(d)
        elements.append(Spacer(1, 4 * mm))

        if label:
            elements.append(Paragraph(f"<b>{self._esc_text(label)}</b>", s["body"]))

        if explanation:
            elements.append(Paragraph(self._esc_text(explanation), s["body"]))

        return elements

    def _build_future_outlook_page(self, cr) -> list:
        """Future outlook with timeline projections."""
        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["future_outlook"], s["heading1"]))
        elements.append(Spacer(1, 6 * mm))

        fo = cr.future_outlook

        if fo.product_vision:
            elements.append(Paragraph(f"<b>{t['product_vision']}</b>", s["body"]))
            elements.append(Paragraph(self._esc_text(fo.product_vision), s["body"]))
            elements.append(Spacer(1, 4 * mm))

        if fo.viability_assessment:
            elements.append(Paragraph(f"<b>{t['viability']}</b>", s["body"]))
            elements.append(Paragraph(self._esc_text(fo.viability_assessment), s["body"]))
            elements.append(Spacer(1, 6 * mm))

        # Projections
        confidence_colors = {
            "high": COLOR_GREEN,
            "medium": COLOR_YELLOW,
            "low": COLOR_RED,
        }

        for label_key, proj in [
            ("year_1", fo.year_1),
            ("year_3", fo.year_3),
            ("year_5", fo.year_5),
        ]:
            if proj is None:
                continue
            conf_color = confidence_colors.get(proj.confidence, COLOR_TEXT_DIM)
            elements.append(
                Paragraph(
                    f"<b>{t[label_key]}</b> "
                    f'({t["confidence"]}: <font color="{conf_color.hexval()}">'
                    f"{self._esc_text(proj.confidence)}</font>)",
                    s["heading2"],
                )
            )
            elements.append(Paragraph(self._esc_text(proj.projection), s["body"]))
            if proj.key_milestones:
                elements.append(
                    Paragraph(f"<b>{t['milestones']}:</b>", s["body"])
                )
                for ms in proj.key_milestones:
                    elements.append(Paragraph(f"• {self._esc_text(ms)}", s["body"]))
            elements.append(Spacer(1, 4 * mm))

        return elements

    def _build_strategic_advice_page(self, cr) -> list:
        """Strategic advice with prioritized actions."""
        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["strategic_advice"], s["heading1"]))
        elements.append(Spacer(1, 6 * mm))

        sa = cr.strategic_advice

        for section_key, actions in [
            ("immediate_actions", sa.immediate_actions),
            ("medium_term", sa.medium_term),
        ]:
            if not actions:
                continue
            elements.append(Paragraph(t[section_key], s["heading2"]))
            elements.append(Spacer(1, 3 * mm))

            cell_style = ParagraphStyle(
                "CellStyle", fontName=s["body"].fontName, fontSize=8,
                textColor=COLOR_TEXT, leading=11,
            )
            cell_style_h = ParagraphStyle(
                "CellStyleH", fontName=s["heading1"].fontName, fontSize=8,
                textColor=COLOR_WHITE, leading=11,
            )
            header = [
                Paragraph(t["action"], cell_style_h),
                Paragraph(t["rationale"], cell_style_h),
                Paragraph(t["impact"], cell_style_h),
            ]
            rows = [header]
            for act in actions:
                rows.append([
                    Paragraph(self._esc_text(act.action), cell_style),
                    Paragraph(self._esc_text(act.rationale), cell_style),
                    Paragraph(self._esc_text(act.expected_impact), cell_style),
                ])

            col_w = 150
            table = Table(rows, colWidths=[col_w, col_w, col_w])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_SURFACE),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_WHITE]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 6 * mm))

        if sa.long_term_vision:
            elements.append(Paragraph(t["long_term_vision"], s["heading2"]))
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph(self._esc_text(sa.long_term_vision), s["body"]))

        return elements

    def _build_investment_thesis_page(self, cr) -> list:
        """Investment thesis with recommendation badge."""
        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["investment_thesis"], s["heading1"]))
        elements.append(Spacer(1, 6 * mm))

        thesis = cr.investment_thesis

        # Recommendation badge
        rec_labels = {
            "strong_invest": (t.get("invest_strong", "Strong Invest"), COLOR_GREEN),
            "invest_with_conditions": (t.get("invest_conditions", "Invest with Conditions"), colors.HexColor("#84cc16")),
            "cautious": (t.get("invest_cautious", "Cautious"), COLOR_YELLOW),
            "pass": (t.get("invest_pass", "Pass"), COLOR_ORANGE),
            "strong_pass": (t.get("invest_strong_pass", "Strong Pass"), COLOR_RED),
        }
        rec_label, rec_color = rec_labels.get(
            thesis.recommendation,
            (thesis.recommendation, COLOR_TEXT_DIM),
        )
        elements.append(
            Paragraph(
                f'{t["recommendation"]}: '
                f'<font color="{rec_color.hexval()}" size="14"><b>{self._esc_text(rec_label)}</b></font>',
                s["body"],
            )
        )
        elements.append(Spacer(1, 4 * mm))

        # Rationale
        if thesis.rationale:
            elements.append(Paragraph(self._esc_text(thesis.rationale), s["body"]))
            elements.append(Spacer(1, 6 * mm))

        # Each item is a separate row; long individual cells may split too.
        risks, upside = thesis.key_risks, thesis.key_upside
        rows = [[Paragraph(f"<b>{t['key_risks']}</b>", s["body"]),
                 Paragraph(f"<b>{t['key_upside']}</b>", s["body"])]]
        for index in range(max(len(risks), len(upside), 1)):
            rows.append([
                Paragraph("• " + self._esc_text(items[index]) if index < len(items) else "—", s["body"])
                for items in (risks, upside)
            ])
        risk_upside = Table(rows, colWidths=[225, 225], repeatRows=1, splitByRow=1, splitInRow=1)
        risk_upside.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(risk_upside)
        elements.append(Spacer(1, 4 * mm))

        # Comparable companies
        if thesis.comparable_companies:
            elements.append(
                Paragraph(
                    f"<b>{t['comparable_companies']}:</b> "
                    + ", ".join(self._esc_text(c) for c in thesis.comparable_companies),
                    s["body"],
                )
            )
            elements.append(Spacer(1, 3 * mm))

        # Valuation factors
        if thesis.suggested_valuation_factors:
            elements.append(
                Paragraph(
                    f"<b>{t['valuation_factors']}:</b> "
                    + self._esc_text(thesis.suggested_valuation_factors),
                    s["body"],
                )
            )

        return elements

    def _build_consulting_red_flags(self, cr) -> list:
        """Red flags from consulting report.

        Note: Red flags are NOT factored into the numeric score. They are
        included in the report as actionable items for the development team
        to consider — useful for source code improvement and remediation.
        """
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle

        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["red_flags"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=3 * mm)
        )

        # Note callout: red flags are informational, not scored
        if self._lang == "ja":
            note_text = (
                "<b>ℹ レッドフラグについて</b><br/>"
                "本セクションのレッドフラグは <b>スコアリングには反映されていません</b>。"
                "本レポートを読んだ開発チームが <b>ソースコードの改善に活用できる可能性</b> がある"
                "事項として参考情報として記載しています。優先順位付けや改修計画の立案にご活用ください。"
            )
        else:
            note_text = (
                "<b>ℹ About Red Flags</b><br/>"
                "Red flags in this section are <b>NOT factored into the numeric score</b>. "
                "They are listed as reference information that the development team can "
                "<b>potentially use to improve the source code</b>. Useful for prioritization "
                "and remediation planning."
            )
        callout = RLTable(
            [[Paragraph(note_text, s["body_small"])]],
            colWidths=[160 * mm],
        )
        callout.setStyle(RLTableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_ACCENT_LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEABOVE", (0, 0), (-1, 0), 2, COLOR_ACCENT),
        ]))
        elements.append(callout)
        elements.append(Spacer(1, 5 * mm))

        severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        from due_diligence_engine.report.generator import _extract_file_line, _extract_one_line_fix

        valid_flags = [f for f in (cr.red_flags or []) if isinstance(f, dict)]
        sorted_flags = sorted(
            valid_flags,
            key=lambda f: severity_rank.get(str(f.get("severity", "info")).lower(), 99),
        )

        hdr_style = ParagraphStyle(
            "CRFHeader", fontName=self._font_bold(), fontSize=8, leading=11, textColor=COLOR_WHITE,
        )
        cell_style = ParagraphStyle(
            "CRFCell", fontName=self._font_normal(), fontSize=8.5, leading=13, textColor=COLOR_TEXT,
        )

        if self._lang == "ja":
            headers = ["深刻度", "対象 (file:line)", "ビジネス影響・欠陥詳細", "具体的な1行修正方針"]
        else:
            headers = ["Severity", "Target (file:line)", "Defect & Business Impact", "Concrete 1-Line Fix Plan"]

        rows = [[Paragraph(f"<b>{self._esc_text(h)}</b>", hdr_style) for h in headers]]
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ]

        for r_idx, flag in enumerate(sorted_flags, start=1):
            sev = str(flag.get("severity", "info")).lower()
            title = str(flag.get("title", ""))
            desc = str(flag.get("description", ""))
            impact = str(flag.get("business_impact", ""))
            loc = _extract_file_line(flag)
            fix_plan = _extract_one_line_fix(flag)

            if sev == "critical":
                badge_html = '<font color="#e11d48"><b>CRITICAL</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_ROSE_BG))
            elif sev == "high":
                badge_html = '<font color="#d97706"><b>! HIGH</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_AMBER_BG))
            elif sev == "medium":
                badge_html = '<font color="#0284c7"><b>MEDIUM</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_ACCENT_LIGHT))
            else:
                badge_html = f'<font color="#059669"><b>{self._esc_text(sev.upper())}</b></font>'
                style_cmds.append(("BACKGROUND", (0, r_idx), (0, r_idx), COLOR_SLATE_BG))

            impact_parts = [f"<b>{self._esc_text(title)}</b>"]
            if impact:
                impact_parts.append(self._esc_text(impact))
            elif desc:
                impact_parts.append(self._esc_text(desc))

            rows.append([
                Paragraph(badge_html, cell_style),
                Paragraph(f'<font name="Helvetica">{self._esc_text(loc)}</font>', cell_style),
                Paragraph("<br/>".join(impact_parts), cell_style),
                Paragraph(self._esc_text(fix_plan if not desc else f"{fix_plan} ({desc[:90]})"), cell_style),
            ])

        if len(rows) > 1:
            rf_table = RLTable(rows, colWidths=[24 * mm, 36 * mm, 53 * mm, 52 * mm], repeatRows=1)
            rf_table.setStyle(RLTableStyle(style_cmds))
            elements.append(rf_table)

        return elements

    def _build_glossary_page(self, cr) -> list:
        """Glossary page combining base glossary and AI additions."""
        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["glossary"], s["heading1"]))
        elements.append(Spacer(1, 6 * mm))

        # AI-generated glossary additions
        glossary = cr.glossary_additions or []
        if not glossary:
            elements.append(Paragraph("—", s["body_dim"]))
            return elements

        cell_style = ParagraphStyle(
            "GlossCell", fontName=s["body"].fontName, fontSize=8,
            textColor=COLOR_TEXT, leading=11,
        )
        cell_style_h = ParagraphStyle(
            "GlossCellH", fontName=s["heading1"].fontName, fontSize=8,
            textColor=COLOR_WHITE, leading=11,
        )
        cell_style_bold = ParagraphStyle(
            "GlossCellB", fontName=s["heading1"].fontName, fontSize=8,
            textColor=COLOR_TEXT, leading=11,
        )
        header = [Paragraph(t["term"], cell_style_h), Paragraph(t["definition"], cell_style_h)]
        rows = [header]
        for entry in glossary:
            if isinstance(entry, dict):
                rows.append([
                    Paragraph(self._esc_text(entry.get("term", "")), cell_style_bold),
                    Paragraph(self._esc_text(entry.get("definition", "")), cell_style),
                ])

        if len(rows) > 1:
            table = Table(rows, colWidths=[120, 330])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), COLOR_SURFACE),
                ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_LIGHT_BG, COLOR_WHITE]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(table)

        return elements

    # ------------------------------------------------------------------
    # Site Verification page
    # ------------------------------------------------------------------

    def _build_site_verification_page(self, cr) -> list:
        """Site verification page with horizontal bar chart for 10 items."""
        t = self._t
        s = self._styles
        elements: list = []

        sv = cr.site_verification
        if not sv or not sv.items:
            return elements

        # Title + subtitle
        elements.append(Paragraph(t["site_verification"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )
        elements.append(Paragraph(t["site_verification_subtitle"], s["body_dim"]))
        elements.append(Spacer(1, 4 * mm))

        # URLs analyzed
        if sv.urls_analyzed:
            elements.append(
                Paragraph(f"<b>{t['sv_urls_analyzed']}:</b>", s["body"])
            )
            for url in sv.urls_analyzed:
                elements.append(Paragraph(f"  {self._esc_text(url)}", s["body_small"]))
            elements.append(Spacer(1, 4 * mm))

        # Overall credibility score — Arc brand coloring
        cred_score = sv.overall_credibility
        if cred_score >= 75:
            cred_color = COLOR_ACCENT                # Arc sky
        elif cred_score >= 50:
            cred_color = COLOR_ACCENT_DARK           # Arc sky darker
        elif cred_score >= 30:
            cred_color = colors.HexColor("#000000")  # black
        else:
            cred_color = colors.HexColor("#6b2a2a")  # muted red

        cred_text = (
            f'<font color="{cred_color.hexval()}" size="36">{cred_score:.0f}</font>'
            f'<font color="{COLOR_TEXT_DIM.hexval()}" size="14"> / 100</font>'
        )
        elements.append(Paragraph(cred_text, s["score_large"]))
        elements.append(
            Paragraph(t["overall_credibility"], s["center"])
        )
        elements.append(Spacer(1, 5 * mm))

        # --- Requirement 3: 2-Column "Company Claim vs. Code Evidence" Comparison Table ---
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle

        sv_hdr_style = ParagraphStyle(
            "SVHdr", fontName=self._font_bold(), fontSize=8.5, leading=11, textColor=COLOR_WHITE,
        )
        sv_cell_style = ParagraphStyle(
            "SVCell", fontName=self._font_normal(), fontSize=8.5, leading=13, textColor=COLOR_TEXT,
        )
        if self._lang == "ja":
            sv_headers = ["Web・ピッチの主張 / 検証項目", "実コードの検証結果 (file:line) と判定バッジ"]
        else:
            sv_headers = ["Web / Pitch Claim & Verification Axis", "Codebase Evidence (file:line) & Verdict Badge"]

        sv_rows = [[
            Paragraph(f"<b>{self._esc_text(sv_headers[0])}</b>", sv_hdr_style),
            Paragraph(f"<b>{self._esc_text(sv_headers[1])}</b>", sv_hdr_style),
        ]]
        sv_table_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]

        symbol_font = "HeiseiKakuGo-W5"
        for idx, item in enumerate(sv.items[:14], start=1):
            item_title = item.item_name_ja if self._lang == "ja" and item.item_name_ja else item.item_name
            sc_v = float(item.score)
            if sc_v >= 75:
                verdict_badge = f'<font name="{symbol_font}" color="#059669">○</font> <font color="#059669"><b>{"実装済" if self._lang == "ja" else "Verified"} ({sc_v:.0f}/100)</b></font>'
                sv_table_styles.append(("BACKGROUND", (1, idx), (1, idx), COLOR_EMERALD_BG))
            elif sc_v >= 45:
                verdict_badge = f'<font name="{symbol_font}" color="#d97706">△</font> <font color="#d97706"><b>{"一部のみ" if self._lang == "ja" else "Partial"} ({sc_v:.0f}/100)</b></font>'
                sv_table_styles.append(("BACKGROUND", (1, idx), (1, idx), COLOR_AMBER_BG))
            else:
                verdict_badge = f'<font name="{symbol_font}" color="#e11d48">×</font> <font color="#e11d48"><b>{"未実装" if self._lang == "ja" else "Unimplemented"} ({sc_v:.0f}/100)</b></font>'
                sv_table_styles.append(("BACKGROUND", (1, idx), (1, idx), COLOR_ROSE_BG))

            rationale_txt = self._esc_text(item.rationale or "")
            sv_rows.append([
                Paragraph(f"<b>{self._esc_text(item_title)}</b>", sv_cell_style),
                Paragraph(f"{verdict_badge}<br/>{rationale_txt}", sv_cell_style),
            ])

        sv_tbl = RLTable(sv_rows, colWidths=[65 * mm, 100 * mm], repeatRows=1)
        sv_tbl.setStyle(RLTableStyle(sv_table_styles))
        elements.append(sv_tbl)
        elements.append(Spacer(1, 6 * mm))

        # --- Horizontal bar chart for verification items ---
        confidence_badge = {
            "high": t.get("confidence_high", "H"),
            "medium": t.get("confidence_medium", "M"),
            "low": t.get("confidence_low", "L"),
        }

        bar_max_w = 240
        row_h = 44
        label_w = 160
        chart_w = label_w + bar_max_w + 80
        sv_items = sv.items[:14]
        chart_h = len(sv_items) * row_h + 10

        d = Drawing(chart_w, chart_h)

        for i, item in enumerate(sv_items):
            y = chart_h - (i + 1) * row_h + 14

            # Item name (bold)
            item_name = item.item_name_ja if self._lang == "ja" and item.item_name_ja else item.item_name
            font_bold = self._font_bold()
            d.add(String(0, y + 4, item_name, fontName=font_bold, fontSize=8.5,
                         fillColor=COLOR_TEXT))

            # Confidence label (small gray below name)
            conf_label = confidence_badge.get(item.confidence, "M")
            conf_font = self._font_normal()
            conf_text = f"Confidence: {conf_label}"
            d.add(String(0, y - 8, conf_text, fontName=conf_font, fontSize=6.5,
                         fillColor=COLOR_TEXT_DIM))

            # Gray track bar
            d.add(Rect(label_w, y, bar_max_w, 16,
                        fillColor=colors.HexColor("#e2e8f0"),
                        strokeColor=None, strokeWidth=0))

            # Score bar (Arc brand: black + sky blue)
            score = item.score
            bar_w = max(2, (score / 100) * bar_max_w)
            if score >= 75:
                bar_color = COLOR_ACCENT                  # Arc sky
            elif score >= 50:
                bar_color = COLOR_ACCENT_DARK             # Arc sky darker
            elif score >= 30:
                bar_color = colors.HexColor("#000000")    # black
            else:
                bar_color = colors.HexColor("#6b2a2a")    # muted red
            d.add(Rect(label_w, y, bar_w, 16,
                        fillColor=bar_color,
                        strokeColor=None, strokeWidth=0))

            # Score number (right of bar)
            score_str = f"{score:.0f}"
            d.add(String(label_w + bar_max_w + 6, y + 3, score_str,
                         fontName="Helvetica", fontSize=9,
                         fillColor=COLOR_TEXT_DIM))

        elements.append(d)
        elements.append(Spacer(1, 8 * mm))

        # Summary text
        if sv.summary:
            elements.append(Paragraph(f"<b>{t['sv_summary']}</b>", s["body"]))
            elements.append(Paragraph(self._esc_text(sv.summary), s["body"]))

        return elements

    # ------------------------------------------------------------------
    # Competitive Analysis — Forrester Wave-style 2×3 grid
    # ------------------------------------------------------------------

    _MARKET_ORDER_JA = {
        "Global": "グローバル", "US": "米国", "EMEA": "EMEA",
        "LATAM": "中南米", "Japan": "日本", "SEA": "東南アジア",
    }

    # Cell size for mini charts (fits 2 per row within A4 margins)
    _CELL_W = 235
    _CELL_H = 152

    def _mini_chart(self, chart, ctype: str, quadrant_labels: list[str] | None = None) -> Drawing:
        """Render a single Forrester-style mini chart as a standalone Drawing."""
        w, h = self._CELL_W, self._CELL_H
        d = Drawing(w, h)

        # Paddings: left for Y-axis label, bottom for X-axis label, top/right margins
        pl, pb, pr, pt = 32, 22, 8, 8
        pw = w - pl - pr  # plot width
        ph = h - pb - pt  # plot height

        # --- Background & border ---
        d.add(Rect(0, 0, w, h,
                   fillColor=colors.HexColor("#f8f9fa"),
                   strokeColor=COLOR_BORDER, strokeWidth=0.4))

        # --- Grid lines (Forrester style: light horizontal/vertical bands) ---
        for frac in (0.25, 0.5, 0.75):
            gx = pl + pw * frac
            gy = pb + ph * frac
            d.add(Line(gx, pb, gx, pb + ph,
                       strokeColor=colors.HexColor("#e5e7eb"), strokeWidth=0.3))
            d.add(Line(pl, gy, pl + pw, gy,
                       strokeColor=colors.HexColor("#e5e7eb"), strokeWidth=0.3))

        # --- Axes (solid) ---
        d.add(Line(pl, pb, pl + pw, pb,
                   strokeColor=COLOR_TEXT_DIM, strokeWidth=0.6))
        d.add(Line(pl, pb, pl, pb + ph,
                   strokeColor=COLOR_TEXT_DIM, strokeWidth=0.6))

        # --- Axis scale ticks: 0, 25, 50, 75, 100 ---
        af = self._font_normal()
        for val in (0, 50, 100):
            # X ticks
            tx = pl + pw * (val / 100)
            d.add(Line(tx, pb, tx, pb - 3,
                       strokeColor=COLOR_TEXT_DIM, strokeWidth=0.3))
            d.add(String(tx - 4, pb - 11, str(val),
                         fontName=af, fontSize=5, fillColor=COLOR_TEXT_DIM))
            # Y ticks
            ty = pb + ph * (val / 100)
            d.add(Line(pl, ty, pl - 3, ty,
                       strokeColor=COLOR_TEXT_DIM, strokeWidth=0.3))
            d.add(String(pl - 14, ty - 2, str(val),
                         fontName=af, fontSize=5, fillColor=COLOR_TEXT_DIM))

        # --- Quadrant labels (for quadrant-type charts) ---
        if quadrant_labels and len(quadrant_labels) == 4:
            lf = self._font_bold()
            lc = colors.HexColor("#c0c4cc")
            ls = 5.5
            mx = pl + pw / 2
            my = pb + ph / 2
            # [top-left, top-right, bottom-left, bottom-right]
            d.add(String(pl + 3, pb + ph - 10, quadrant_labels[0],
                         fontName=lf, fontSize=ls, fillColor=lc))
            d.add(String(mx + 3, pb + ph - 10, quadrant_labels[1],
                         fontName=lf, fontSize=ls, fillColor=lc))
            d.add(String(pl + 3, pb + 3, quadrant_labels[2],
                         fontName=lf, fontSize=ls, fillColor=lc))
            d.add(String(mx + 3, pb + 3, quadrant_labels[3],
                         fontName=lf, fontSize=ls, fillColor=lc))
            # Center cross (dashed)
            d.add(Line(mx, pb, mx, pb + ph,
                       strokeColor=colors.HexColor("#d1d5db"), strokeWidth=0.4,
                       strokeDashArray=[3, 3]))
            d.add(Line(pl, my, pl + pw, my,
                       strokeColor=colors.HexColor("#d1d5db"), strokeWidth=0.4,
                       strokeDashArray=[3, 3]))

        # --- Risk-return special: sweet spot zone + efficient frontier ---
        if ctype == "gs_risk_return":
            # Sweet spot = low risk, high return (left-top)
            sx, sy = pl + pw * 0.02, pb + ph * 0.58
            sw, sh = pw * 0.38, ph * 0.38
            d.add(Rect(sx, sy, sw, sh,
                       fillColor=colors.HexColor("#e8f4f8"),
                       strokeColor=colors.HexColor("#b8d8e8"), strokeWidth=0.3))
            lf = self._font_bold()
            d.add(String(sx + 2, sy + sh - 9,
                         self._t.get("sweet_spot", "Sweet Spot"),
                         fontName=lf, fontSize=5, fillColor=COLOR_ACCENT))
            # Efficient frontier diagonal
            d.add(Line(pl + pw * 0.05, pb + ph * 0.1,
                       pl + pw * 0.95, pb + ph * 0.9,
                       strokeColor=COLOR_ACCENT, strokeWidth=0.7,
                       strokeDashArray=[4, 2]))

        # --- Axis labels ---
        x_lab = chart.x_axis_label_ja if self._lang == "ja" and chart.x_axis_label_ja else chart.x_axis_label
        y_lab = chart.y_axis_label_ja if self._lang == "ja" and chart.y_axis_label_ja else chart.y_axis_label
        # Truncate
        x_lab = (x_lab[:22] + "…") if len(x_lab) > 24 else x_lab
        y_lab = (y_lab[:14] + "…") if len(y_lab) > 16 else y_lab
        d.add(String(pl + pw / 2 - len(x_lab) * 1.5, 2, x_lab,
                     fontName=af, fontSize=5.5, fillColor=COLOR_TEXT_DIM))
        # Y-axis label (rotated text not supported in ReportLab String,
        # so place vertically at left edge)
        d.add(String(1, pb + ph / 2 - len(y_lab) * 1.2, y_lab,
                     fontName=af, fontSize=5, fillColor=COLOR_TEXT_DIM))

        # --- Data points ---
        is_bubble = (ctype == "bubble_3d")
        nf = self._font_normal()
        # Sort: non-target first, target on top
        sorted_pts = sorted(chart.data_points, key=lambda dp: dp.is_target)
        label_positions: list[tuple[float, float]] = []

        for dp in sorted_pts:
            cx = pl + (dp.x / 100) * pw
            cy = pb + (dp.y / 100) * ph

            if is_bubble:
                r = max(4, min(18, dp.z * 0.18))
                fill = COLOR_ACCENT if dp.is_target else colors.HexColor("#d1d5db")
                alpha = 0.85
            else:
                r = 5.5 if dp.is_target else 4
                fill = COLOR_ACCENT if dp.is_target else colors.HexColor("#9ca3af")
                alpha = 1.0

            stroke_c = colors.white if dp.is_target else colors.HexColor("#ffffff")
            stroke_w = 1.0 if dp.is_target else 0.3
            d.add(Circle(cx, cy, r, fillColor=fill,
                         strokeColor=stroke_c, strokeWidth=stroke_w))

            # Smart label placement to avoid overlaps
            name = dp.name[:12]
            lx = cx + r + 2
            ly = cy - 2
            # If off right edge, place left
            if lx + len(name) * 3 > w - 2:
                lx = cx - r - len(name) * 3 - 1
            # If off top, shift down
            if ly + 6 > h - 2:
                ly = cy - 8
            # Check overlap with previous labels (simple)
            for plx, ply in label_positions:
                if abs(lx - plx) < 25 and abs(ly - ply) < 7:
                    ly -= 7
                    break
            label_positions.append((lx, ly))

            fs = 5.5 if dp.is_target else 5
            fc = COLOR_TEXT if dp.is_target else COLOR_TEXT_DIM
            d.add(String(lx, ly, name,
                         fontName=nf, fontSize=fs, fillColor=fc))

        return d

    # ────────────────────────────────────────────────────────
    # Task C: Atlas Optimization Assessment (4-axis parallel evaluation)
    # ────────────────────────────────────────────────────────

    def _build_atlas_four_axis_page(self, cr) -> list:
        """Atlas 4-axis dashboard — same visual language as 6-dim score dashboard.

        Inviolable rules respected:
        - Horizontal progress bars (filled vs empty contrast)
        - Left label → bar → right monospaced score value
        - Arc sky (#5271FF) + black brand colors
        - F→A barometer at the bottom
        """
        t = self._t
        s = self._styles
        elements: list = []

        afa = cr.atlas_four_axis
        if afa is None or not afa.axes:
            return elements

        # Title
        elements.append(Paragraph(t["atlas_four_axis"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )
        elements.append(Paragraph(t["atlas_subtitle"], s["body_dim"]))
        elements.append(Spacer(1, 6 * mm))

        # Industry context badge
        if afa.industry_context:
            ind_text = (
                f'<font color="{COLOR_TEXT_DIM.hexval()}" size="9">'
                f'{t["atlas_industry_context"]}: <b>{self._esc_text(afa.industry_context)}</b></font>'
            )
            elements.append(Paragraph(ind_text, s["center"]))
            elements.append(Spacer(1, 3 * mm))

        # Atlas composite score (large display, accent color)
        atlas_label = f'{t["atlas_overall"]}'
        elements.append(
            Paragraph(
                f'<font color="{COLOR_ACCENT.hexval()}" size="13"><b>{atlas_label}</b></font>',
                s["center"],
            )
        )
        elements.append(Spacer(1, 2 * mm))

        score_large_style = ParagraphStyle(
            "AtlasScoreLarge", fontName="Helvetica-Bold", fontSize=48,
            leading=56, alignment=1, textColor=COLOR_ACCENT,
        )
        overall_text = (
            f'{afa.overall_score:.0f}'
            f'<font color="{COLOR_TEXT_DIM.hexval()}" size="18"> / 100</font>'
        )
        elements.append(Paragraph(overall_text, score_large_style))
        elements.append(Spacer(1, 8 * mm))

        # 4-axis horizontal bar chart — Table layout for full-text wrapping (v0.3.4)
        # Each row: [Label + auto-wrap description (Paragraph)] | [Bar (Drawing)] | [Score]
        # Row height auto-grows with content — no truncation, no orphan ellipsis.
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle

        axes_ordered = sorted(
            afa.axes,
            key=lambda a: {"performance": 0, "stability": 1, "lightweight": 2, "security": 3}.get(a.axis_key, 99),
        )

        # Column widths (total ~165mm A4 portrait usable)
        label_col_w = 50 * mm   # label + auto-wrap rationale
        bar_col_w = 75 * mm     # bar drawing
        score_col_w = 30 * mm   # score / Lv / weight%
        bar_max_w = bar_col_w - 4   # actual drawing width

        font_label = self._font_bold()
        font_body = self._font_normal()

        label_para_style = ParagraphStyle(
            "AxisLabel", fontName=font_label, fontSize=10,
            leading=13, textColor=COLOR_TEXT, spaceAfter=2,
        )
        rationale_para_style = ParagraphStyle(
            "AxisRationale", fontName=font_body, fontSize=7.5,
            leading=10, textColor=COLOR_TEXT_DIM, spaceAfter=0,
        )
        score_para_style = ParagraphStyle(
            "AxisScore", fontName="Helvetica-Bold", fontSize=9,
            leading=12, textColor=COLOR_TEXT_DIM, alignment=TA_RIGHT,
        )

        def _bar_drawing(score_val: float) -> Drawing:
            """Build a single horizontal bar drawing."""
            d = Drawing(bar_max_w, 16)
            # Background track
            d.add(Rect(0, 0, bar_max_w, 16, rx=8, ry=8,
                       fillColor=colors.HexColor("#e2e8f0"),
                       strokeColor=None, strokeWidth=0))
            # Filled portion
            bar_w = max(2, (score_val / 100) * bar_max_w)
            if score_val >= 75:
                bar_color = COLOR_ACCENT
            elif score_val >= 50:
                bar_color = COLOR_ACCENT_DARK
            elif score_val >= 30:
                bar_color = colors.HexColor("#000000")
            else:
                bar_color = colors.HexColor("#6b2a2a")
            d.add(Rect(0, 0, bar_w, 16, rx=min(8, bar_w / 2), ry=min(8, bar_w / 2),
                       fillColor=bar_color, strokeColor=None, strokeWidth=0))
            return d

        rows = []
        for axis in axes_ordered:
            name = axis.name_ja if self._lang == "ja" and axis.name_ja else axis.name_en
            rationale = axis.rationale or ""

            # Cell 1: label + full rationale (auto-wrap, NO truncation)
            label_cell = [Paragraph(f"<b>{self._esc_text(name)}</b>", label_para_style)]
            if rationale:
                label_cell.append(Paragraph(self._esc_text(rationale), rationale_para_style))

            # Cell 2: bar drawing
            bar_cell = _bar_drawing(axis.score)

            # Cell 3: score text (right-aligned)
            score_str = f"{axis.score:.0f}  Lv.{axis.level}  ({axis.weight_pct:.0f}%)"
            score_cell = Paragraph(score_str, score_para_style)

            rows.append([label_cell, bar_cell, score_cell])

        tbl = RLTable(
            rows,
            colWidths=[label_col_w, bar_col_w, score_col_w],
            # rowHeights=None → auto-sizing
        )
        tbl.setStyle(RLTableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("VALIGN", (1, 0), (1, -1), "MIDDLE"),  # bar centered
            ("VALIGN", (2, 0), (2, -1), "MIDDLE"),  # score centered
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 6 * mm))

        # Summary text
        summary = afa.summary_ja if self._lang == "ja" and afa.summary_ja else afa.summary
        if summary:
            elements.append(Paragraph(self._esc_text(summary), s["body"]))

        return elements

    def _build_atlas_security_breakdown_page(self, cr, security_axis) -> list:
        """Security Strength sub-breakdown — emphasizes encryption (35%) as core."""
        t = self._t
        s = self._styles
        elements: list = []

        elements.append(Paragraph(t["security_breakdown"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=4 * mm)
        )
        elements.append(Paragraph(t["security_breakdown_subtitle"], s["body_dim"]))
        elements.append(Spacer(1, 6 * mm))

        # Sub-items in fixed order: encryption (largest) → privacy → comms → layers → posture (smallest)
        order = {"encryption": 0, "privacy": 1, "comms": 2, "layers": 3, "posture": 4}
        sub_items = sorted(security_axis.sub_items, key=lambda si: order.get(si.key, 99))

        # Sub-item rows — Table layout for full-text wrapping (v0.3.4)
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle

        # Column widths
        label_col_w = 50 * mm
        bar_col_w = 75 * mm
        score_col_w = 30 * mm
        bar_max_w = bar_col_w - 4

        # Map sub-item keys to short i18n labels (fallback to provided name)
        subitem_labels = {
            "encryption": t.get("subitem_encryption", "Encryption"),
            "privacy": t.get("subitem_privacy", "Privacy"),
            "posture": t.get("subitem_posture", "Posture"),
            "comms": t.get("subitem_comms", "Comms"),
            "layers": t.get("subitem_layers", "Layers"),
        }

        font_label = self._font_bold()
        font_body = self._font_normal()

        sub_label_style = ParagraphStyle(
            "SubLabel", fontName=font_label, fontSize=10,
            leading=13, textColor=COLOR_TEXT, spaceAfter=2,
        )
        sub_rationale_style = ParagraphStyle(
            "SubRationale", fontName=font_body, fontSize=7.5,
            leading=10, textColor=COLOR_TEXT_DIM, spaceAfter=0,
        )
        sub_score_style = ParagraphStyle(
            "SubScore", fontName="Helvetica-Bold", fontSize=9,
            leading=12, textColor=COLOR_TEXT_DIM, alignment=TA_RIGHT,
        )

        def _sub_bar(score_val: float) -> Drawing:
            d = Drawing(bar_max_w, 16)
            d.add(Rect(0, 0, bar_max_w, 16, rx=8, ry=8,
                       fillColor=colors.HexColor("#e2e8f0"),
                       strokeColor=None, strokeWidth=0))
            bar_w = max(2, (score_val / 100) * bar_max_w)
            if score_val >= 75:
                bc = COLOR_ACCENT
            elif score_val >= 50:
                bc = COLOR_ACCENT_DARK
            elif score_val >= 30:
                bc = colors.HexColor("#000000")
            else:
                bc = colors.HexColor("#6b2a2a")
            d.add(Rect(0, 0, bar_w, 16, rx=min(8, bar_w / 2), ry=min(8, bar_w / 2),
                       fillColor=bc, strokeColor=None, strokeWidth=0))
            return d

        sub_rows = []
        for si in sub_items:
            name = subitem_labels.get(si.key, si.name_ja if self._lang == "ja" else si.name_en)
            rationale = si.rationale or ""

            label_cell = [Paragraph(f"<b>{self._esc_text(name)}</b>", sub_label_style)]
            if rationale:
                label_cell.append(Paragraph(self._esc_text(rationale), sub_rationale_style))

            bar_cell = _sub_bar(si.score)

            score_str = f"{si.score:.0f}  Lv.{si.level}  ({si.weight_pct:.0f}%)"
            score_cell = Paragraph(score_str, sub_score_style)

            sub_rows.append([label_cell, bar_cell, score_cell])

        sub_tbl = RLTable(
            sub_rows,
            colWidths=[label_col_w, bar_col_w, score_col_w],
        )
        sub_tbl.setStyle(RLTableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("VALIGN", (1, 0), (1, -1), "MIDDLE"),
            ("VALIGN", (2, 0), (2, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(sub_tbl)
        elements.append(Spacer(1, 6 * mm))

        # Weight philosophy callout + source-code-only disclaimer
        if self._lang == "ja":
            philosophy = (
                "<b>重み哲学:</b> Atlas は <b>サイバーセキュリティ対策全般</b>（暗号化・プライバシー・"
                "通信・レイヤー防御）を 55% で重視する。中でも暗号化技術の実装深度（35%）が最大ウェイト。"
                "MFA・WebAuthn 等の「誰でもできる」項目は最小重み（2%）に抑制。<br/>"
                "<b>第三者認証（SOC2・ISO 27001・HIPAA 等）は参考情報のみでスコア対象外。</b>"
                "DDE は純粋にソースコードから評価する。認証バッジではなくコードを読む。"
            )
        else:
            philosophy = (
                "<b>Weight Philosophy:</b> Atlas places strong emphasis on "
                "<b>cybersecurity defense overall</b> (encryption + privacy + communications + layers) "
                "at 55%, with cryptographic implementation depth (35%) as the largest sub-weight. "
                "Checkbox items (MFA/WebAuthn — \"anyone can do\") are minimum-weighted (2%).<br/>"
                "<b>Third-party certifications (SOC2, ISO 27001, HIPAA, etc.) are REFERENCE ONLY — "
                "not scored.</b> DDE judges the code, not the badge."
            )
        elements.append(Paragraph(philosophy, s["body"]))
        elements.append(Spacer(1, 4 * mm))

        # Plain-language glossary for non-engineers reading the report
        elements.append(
            Paragraph(
                "<b>" + ("用語ミニ解説（非エンジニア向け）" if self._lang == "ja"
                         else "Glossary for non-engineer readers") + "</b>",
                s["heading3"],
            )
        )
        if self._lang == "ja":
            gloss_items = [
                ("暗号化技術", "通信や保存データを、本人以外には読めない状態に変換する技術。"
                              "Signal Protocol / PQXDH などが最先端。"),
                ("E2E暗号化", "送信者と受信者だけが読める暗号化。サービス運営者でも中身は見られない。"),
                ("MFA (多要素認証)", "パスワードに加え、SMS コードや認証アプリで本人確認する仕組み。"
                                      "今や標準。導入していないと論外。"),
                ("SOC2", "米国 AICPA が定めたセキュリティ監査基準。<b>DDE のスコアには一切反映しない</b>"
                         "（参考情報のみ）。取得していてもコードが弱い企業はあり、未取得でも暗号実装が"
                         "強い企業はある。本ツールはコードを読んで判断する。"),
                ("libsignal", "Signal Foundation が公開している、Signal Protocol の公式実装ライブラリ。"
                              "使うと暗号の自前実装ミスを避けられる。"),
                ("PQXDH / ML-KEM", "量子コンピュータでも破れない次世代暗号（ポスト量子暗号）。"
                                    "Apple の iMessage (PQ3) や Signal が採用済み。"),
            ]
        else:
            gloss_items = [
                ("Cryptography", "The art of making data unreadable to anyone but the intended recipient. "
                                 "Signal Protocol / PQXDH are state-of-the-art."),
                ("E2E Encryption", "End-to-end: only sender & recipient can decrypt. Even the service provider cannot read it."),
                ("MFA (Multi-Factor Auth)", "Password + second factor (SMS code / authenticator app). "
                                             "Standard hygiene — missing it is a red flag, having it is not a differentiator."),
                ("SOC2", "US AICPA security audit standard. <b>Not factored into DDE's score</b> "
                         "(reference only). Certified companies can still have weak code; "
                         "uncertified companies can still have strong crypto. DDE reads the code."),
                ("libsignal", "Official Signal Protocol implementation by Signal Foundation. "
                              "Using it avoids self-rolled crypto mistakes."),
                ("PQXDH / ML-KEM", "Post-quantum cryptography — safe even against future quantum computers. "
                                    "Adopted by Apple iMessage (PQ3) and Signal."),
            ]
        for term, definition in gloss_items:
            elements.append(
                Paragraph(
                    f'<b>{term}</b> — <font color="{COLOR_TEXT_DIM.hexval()}">{definition}</font>',
                    s["body_small"],
                )
            )

        return elements

    # ────────────────────────────────────────────────────────
    # v0.3.1: Competitor Selection Rationales
    # For each competitor, 3-5 line explanation of why they were chosen.
    # Placed AFTER competitive analysis charts, BEFORE the matrix —
    # so readers understand who is being compared and why.
    # ────────────────────────────────────────────────────────

    def _build_competitor_rationales_page(self, cr) -> list:
        """Competitor selection rationales (3-5 lines per competitor) + estimated score."""
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle

        t = self._t
        s = self._styles
        elements: list = []

        rationales = cr.competitor_rationales or []
        if not rationales:
            return elements

        elements.append(Paragraph(t["competitor_rationales"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=3 * mm)
        )
        elements.append(Paragraph(t["competitor_rationales_subtitle"], s["body_dim"]))
        elements.append(Spacer(1, 3 * mm))

        # Important disclaimer about estimated scores
        if self._lang == "ja":
            disclaimer = (
                "<b>⚠ 推定スコアについて</b><br/>"
                "各社の推定スコア（0-100 点）は <b>公開情報のみに基づく AI の推定値</b> です。"
                "公開情報（マーケページ・ホワイトペーパー・プレスリリース等）は概して好意的に"
                "書かれているため、<b>ソースコードレベルで DD した場合の実スコアはこれ以下になる"
                "可能性が高い</b>ことに留意してください。参考値としてご活用ください。"
            )
        else:
            disclaimer = (
                "<b>⚠ About Estimated Scores</b><br/>"
                "Each competitor's estimated score (0-100) is an <b>AI estimate based ONLY "
                "on publicly available information</b>. Public materials (marketing pages, "
                "whitepapers, press releases) skew positive — so the <b>actual score under "
                "source-code-level DD is likely LOWER</b> than shown. Use as a reference only."
            )
        # Rendered in a light blue callout box
        callout = RLTable(
            [[Paragraph(disclaimer, s["body_small"])]],
            colWidths=[160 * mm],
        )
        callout.setStyle(RLTableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_ACCENT_LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEABOVE", (0, 0), (-1, 0), 2, COLOR_ACCENT),
        ]))
        elements.append(callout)
        elements.append(Spacer(1, 5 * mm))

        for r in rationales:
            # Wrap each competitor block in KeepTogether to prevent orphans —
            # a header on one page with its body bleeding to the next looks broken.
            block: list = []

            # Header row: company name + category + estimated score
            header_bits: list[str] = [f'<b>{self._esc_text(r.name)}</b>']
            if r.category:
                header_bits.append(
                    f'<font color="{COLOR_ACCENT.hexval()}" size="9">[{self._esc_text(r.category)}]</font>'
                )
            # Estimated score — always shown (even if 0), clearly labeled as estimate
            score_label = "推定" if self._lang == "ja" else "est."
            header_bits.append(
                f'<font color="{COLOR_TEXT_DIM.hexval()}" size="10">'
                f'{score_label}: <b>{r.estimated_score:.0f}</b>/100</font>'
            )
            block.append(Paragraph("  ".join(header_bits), s["heading3"]))

            # Meta line: HQ + market position
            meta_parts: list[str] = []
            if r.hq_country:
                meta_parts.append(f'{t["rationale_hq"]}: {self._esc_text(r.hq_country)}')
            if r.market_position:
                meta_parts.append(f'{t["rationale_position"]}: {self._esc_text(r.market_position)}')
            if meta_parts:
                block.append(Paragraph(" · ".join(meta_parts), s["body_dim"]))

            # Rationale (3-5 line prose, language-appropriate)
            rationale_text = (r.rationale_ja if self._lang == "ja" and r.rationale_ja
                              else r.rationale_en)
            if rationale_text:
                block.append(Paragraph(self._esc_text(rationale_text), s["body"]))

            block.append(Spacer(1, 4 * mm))
            elements.append(KeepTogether(block))

        return elements

    # ────────────────────────────────────────────────────────
    # Task D: Implementation Capability Matrix (8th competitive chart)
    # ────────────────────────────────────────────────────────

    def _build_implementation_matrix_page(self, cr) -> list:
        """Implementation matrix — A4 portrait Table, ~30 items × 5-10 competitors.

        Uses ASCII status symbols (✓ △ ✗ ?) per inviolable rule (no emoji icons).
        Target company column highlighted with Arc sky (#5271FF) background.
        """
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle

        t = self._t
        s = self._styles
        elements: list = []

        im = cr.implementation_matrix
        if im is None or not im.items:
            return elements

        elements.append(PageBreak())
        elements.append(Paragraph(t["impl_matrix"], s["heading1"]))
        elements.append(
            HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=2 * mm)
        )
        elements.append(Paragraph(t["impl_matrix_subtitle"], s["body_dim"]))
        elements.append(Spacer(1, 2 * mm))

        # Legend — use ○△× (Japanese tech rating standard, universally rendered by CID fonts).
        legend_text_font = self._font_normal()
        legend_symbol_font = "HeiseiKakuGo-W5"  # has ○△× in both languages
        legend_text = (
            f'<font name="{legend_symbol_font}" size="10" color="#059669">○</font> '
            f'<font name="{legend_text_font}" size="8" color="#059669"><b>{t["impl_legend_verified"]}</b></font>'
            f'   '
            f'<font name="{legend_symbol_font}" size="10" color="#d97706">△</font> '
            f'<font name="{legend_text_font}" size="8" color="#d97706"><b>{t["impl_legend_claimed"]}</b></font>'
            f'   '
            f'<font name="{legend_symbol_font}" size="10" color="#e11d48">×</font> '
            f'<font name="{legend_text_font}" size="8" color="#e11d48"><b>{t["impl_legend_not_impl"]}</b></font>'
            f'   '
            f'<font name="{legend_symbol_font}" size="10" color="#64748b">?</font> '
            f'<font name="{legend_text_font}" size="8" color="#64748b">{t["impl_legend_unknown"]}</font>'
        )
        elements.append(Paragraph(legend_text, s["center"]))
        elements.append(Spacer(1, 3 * mm))

        # Build column structure: [Item, Target, Comp1, Comp2, ...]
        # Limit to 10 competitors (= 11 columns total) to fit A4 portrait (480pt printable width)
        all_companies = [im.target_company] + im.competitors[:10]

        # Header row
        font_header = self._font_bold()
        header_para_style = ParagraphStyle(
            "MatHeader", fontName=font_header, fontSize=6.8,
            textColor=COLOR_WHITE, alignment=1, leading=8.5,
        )

        header_row = [Paragraph("", header_para_style)]
        for c in all_companies:
            short_name = c[:12] + "…" if len(c) > 12 else c
            header_row.append(Paragraph(self._esc_text(short_name), header_para_style))

        # Group items by category
        category_order = [
            "performance", "stability", "lightweight", "encryption",
            "privacy", "posture", "comms", "layers",
        ]
        cat_label_map = {
            "performance": t.get("matcat_performance", "Performance"),
            "stability": t.get("matcat_stability", "Stability"),
            "lightweight": t.get("matcat_lightweight", "Lightweight"),
            "encryption": t.get("matcat_encryption", "Encryption"),
            "privacy": t.get("matcat_privacy", "Privacy"),
            "posture": t.get("matcat_posture", "Posture"),
            "comms": t.get("matcat_comms", "Comms"),
            "layers": t.get("matcat_layers", "Layers"),
        }

        items_by_cat: dict[str, list] = {}
        for item in im.items:
            items_by_cat.setdefault(item.category, []).append(item)

        # Build table rows: header + (category-row + items)*N
        font_body = self._font_normal()
        item_para_style = ParagraphStyle(
            "MatItem", fontName=font_body, fontSize=7.2,
            textColor=COLOR_TEXT, alignment=0, leading=9.5,
        )
        cat_para_style = ParagraphStyle(
            "MatCat", fontName=font_header, fontSize=8,
            textColor=COLOR_ACCENT, alignment=0, leading=10.5,
        )
        cell_symbol_font = "HeiseiKakuGo-W5"
        cell_style = ParagraphStyle(
            "MatCell", fontName=cell_symbol_font, fontSize=9.5,
            textColor=COLOR_TEXT, alignment=1, leading=11,
        )

        table_data = [header_row]
        cat_row_indices = []
        cell_bg_cmds = []

        # Status → (symbol, text_color, bg_color) — high-contrast Quiet Luxury palette
        status_glyph = {
            "verified": ("○", COLOR_GREEN, COLOR_EMERALD_BG),
            "implemented": ("○", COLOR_GREEN, COLOR_EMERALD_BG),
            "claimed": ("△", COLOR_YELLOW, COLOR_AMBER_BG),
            "partial": ("△", COLOR_YELLOW, COLOR_AMBER_BG),
            "not_implemented": ("×", COLOR_RED, COLOR_ROSE_BG),
            "unknown": ("?", COLOR_TEXT_DIM, COLOR_SLATE_BG),
        }

        all_cats = category_order + [c for c in items_by_cat if c not in category_order]
        for cat in all_cats:
            cat_items = items_by_cat.get(cat, [])
            if not cat_items:
                continue

            cat_label = cat_label_map.get(cat, cat)
            cat_row_index = len(table_data)
            cat_row = [Paragraph(f"<b>{self._esc_text(cat_label)}</b>", cat_para_style)] + [""] * len(all_companies)
            table_data.append(cat_row)
            cat_row_indices.append(cat_row_index)

            for item in cat_items:
                row_idx = len(table_data)
                item_label = item.item_ja if self._lang == "ja" and item.item_ja else item.item_en
                row = [Paragraph(self._esc_text(item_label), item_para_style)]
                status_by_company: dict[str, str] = {}
                for st in item.statuses:
                    status_by_company[st.company_name] = st.status.value if hasattr(st.status, "value") else str(st.status)

                for col_idx, company in enumerate(all_companies, start=1):
                    raw_status = status_by_company.get(company, "unknown")
                    glyph, glyph_color, bg_color = status_glyph.get(
                        raw_status, ("?", COLOR_TEXT_DIM, COLOR_SLATE_BG)
                    )
                    cell_para = Paragraph(
                        f'<font color="{glyph_color.hexval()}"><b>{glyph}</b></font>',
                        cell_style,
                    )
                    row.append(cell_para)
                    cell_bg_cmds.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), bg_color))
                table_data.append(row)

        # Column widths strictly bounded to 480pt (A4 printable frame = 481.89pt)
        item_col_w = 135
        comp_col_w = max(26, min(42, (480 - item_col_w) / max(1, len(all_companies))))
        col_widths = [item_col_w] + [comp_col_w] * len(all_companies)

        tbl = RLTable(table_data, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_SURFACE),
            ("BACKGROUND", (1, 0), (1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_WHITE),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.35, COLOR_BORDER),
            ("BOX", (1, 0), (1, -1), 1.0, COLOR_ACCENT),
            *cell_bg_cmds,
        ]
        for idx in cat_row_indices:
            style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), COLOR_ACCENT_LIGHT))
            style_cmds.append(("SPAN", (0, idx), (-1, idx)))

        tbl.setStyle(RLTableStyle(style_cmds))
        elements.append(tbl)

        return elements

    def _build_competitive_analysis_pages(self, cr) -> list:
        """Competitive analysis: 5 chart types × 2×3 Table grid (6 markets).

        Uses ReportLab Table layout (not Drawing.shift) for reliable positioning.
        Each page: heading + 3-row × 2-col Table of mini-chart Drawings.
        Row 1: Global | US
        Row 2: EMEA  | LATAM
        Row 3: Japan  | SEA
        """
        from reportlab.platypus import Table as RLTable, TableStyle as RLTableStyle

        t = self._t
        s = self._styles
        elements: list = []

        ca = cr.competitive_analysis
        if not ca or not ca.markets:
            return elements

        # Lookup: market_name → {chart_type → MarketChart}
        market_charts: dict[str, dict[str, object]] = {}
        for market in ca.markets:
            market_charts[market.market_name] = {
                c.chart_type: c for c in market.charts
            }

        chart_types = [
            "magic_quadrant", "bcg_matrix", "mckinsey_moat",
            "security_posture", "data_governance",
            "gs_risk_return", "bubble_3d",
        ]
        chart_title_map = {
            "magic_quadrant": "chart_magic_quadrant",
            "bcg_matrix": "chart_bcg_matrix",
            "mckinsey_moat": "chart_mckinsey_moat",
            "security_posture": "chart_security_posture",
            "data_governance": "chart_data_governance",
            "gs_risk_return": "chart_gs_risk_return",
            "bubble_3d": "chart_bubble_3d",
        }
        quadrant_map = {
            "magic_quadrant": ["challengers", "leaders", "niche_players", "visionaries"],
            "bcg_matrix": ["question_marks", "stars", "dogs", "cash_cows"],
            "mckinsey_moat": ["innovator", "fortress", "fast_follower", "commodity"],
            "security_posture": ["compliance_risk", "privacy_leader", "exposed", "security_fortress"],
            "data_governance": ["transparent_vuln", "trust_leader", "high_risk", "opaque_fortress"],
        }

        # Grid: 3 rows × 2 cols
        grid_rows = [
            ("Global", "US"),
            ("EMEA", "LATAM"),
            ("Japan" if "Japan" in market_charts else next(iter(market_charts)), "SEA"),
        ]

        cw = self._CELL_W
        ch = self._CELL_H
        label_h = 14  # height for market name label row

        for ctype in chart_types:
            has_data = any(
                ctype in market_charts.get(mn, {})
                for row in grid_rows for mn in row
            )
            if not has_data:
                continue

            elements.append(PageBreak())

            # Page heading
            title_key = chart_title_map.get(ctype, ctype)
            page_title = t.get(title_key, ctype)
            elements.append(
                Paragraph(f"{t['competitive_analysis']} — {page_title}", s["heading1"])
            )
            elements.append(
                HRFlowable(width="100%", thickness=1, color=COLOR_BORDER, spaceAfter=2 * mm)
            )

            # Extract axis rationale from first available chart of this type
            sample_chart = None
            for market in ca.markets:
                for ch_obj in market.charts:
                    if ch_obj.chart_type == ctype:
                        sample_chart = ch_obj
                        break
                if sample_chart:
                    break

            # Axis rationale captions
            if sample_chart:
                x_rat = (sample_chart.x_axis_rationale_ja if self._lang == "ja" and sample_chart.x_axis_rationale_ja
                         else sample_chart.x_axis_rationale)
                y_rat = (sample_chart.y_axis_rationale_ja if self._lang == "ja" and sample_chart.y_axis_rationale_ja
                         else sample_chart.y_axis_rationale)
                x_label = (sample_chart.x_axis_label_ja if self._lang == "ja" and sample_chart.x_axis_label_ja
                           else sample_chart.x_axis_label)
                y_label = (sample_chart.y_axis_label_ja if self._lang == "ja" and sample_chart.y_axis_label_ja
                           else sample_chart.y_axis_label)
                cap_font = self._font_normal()
                cap_bold = self._font_bold()
                if x_rat or y_rat:
                    cap_parts = []
                    if x_label and x_rat:
                        cap_parts.append(
                            f'<font name="{cap_bold}" size="7" color="#5271FF">X: {self._esc_text(x_label)}</font>'
                            f'<font name="{cap_font}" size="7" color="#6b7280"> — {self._esc_text(x_rat)}</font>'
                        )
                    if y_label and y_rat:
                        cap_parts.append(
                            f'<font name="{cap_bold}" size="7" color="#5271FF">Y: {self._esc_text(y_label)}</font>'
                            f'<font name="{cap_font}" size="7" color="#6b7280"> — {self._esc_text(y_rat)}</font>'
                        )
                    for cap in cap_parts:
                        elements.append(Paragraph(cap, s["body"]))
                else:
                    elements.append(Paragraph(t["competitive_subtitle"], s["body_dim"]))
            else:
                elements.append(Paragraph(t["competitive_subtitle"], s["body_dim"]))
            elements.append(Spacer(1, 1.5 * mm))

            # Build Table data: 3 rows × 2 cols, each cell has [Paragraph(market_label), chart_drawing]
            table_data = []
            body_font = self._font_bold()

            for m_left, m_right in grid_rows:
                row_cells = []
                for mname in (m_left, m_right):
                    label = self._MARKET_ORDER_JA.get(mname, mname) if self._lang == "ja" else mname
                    label_para = Paragraph(
                        f'<font name="{body_font}" size="8" color="#5271FF">{self._esc_text(label)}</font>',
                        s["body"],
                    )
                    chart = market_charts.get(mname, {}).get(ctype)
                    if chart is None:
                        # Empty placeholder drawing
                        placeholder = Drawing(cw, ch)
                        placeholder.add(Rect(0, 0, cw, ch,
                                             fillColor=colors.HexColor("#f5f5f5"),
                                             strokeColor=COLOR_BORDER, strokeWidth=0.3))
                        nf = self._font_normal()
                        placeholder.add(String(cw / 2 - 12, ch / 2, "No data",
                                               fontName=nf, fontSize=7, fillColor=COLOR_TEXT_DIM))
                        chart_drawing = placeholder
                    else:
                        qlabels = None
                        if ctype in quadrant_map:
                            qlabels = [t.get(k, k) for k in quadrant_map[ctype]]
                        chart_drawing = self._mini_chart(chart, ctype, qlabels)

                    row_cells.append([label_para, chart_drawing])
                table_data.append(row_cells)

            tbl = RLTable(table_data, colWidths=[cw, cw])
            tbl.setStyle(RLTableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))
            elements.append(tbl)

        return elements
