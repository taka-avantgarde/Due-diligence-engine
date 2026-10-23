"""Parse AI-generated consulting report JSON into ConsultingReport model.

Used by ``dde report --consulting result.json`` to load and validate
the structured JSON output produced by IDE AI (Claude Code, Cursor, etc.).
"""

from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path
from typing import Any

from due_diligence_engine.models import (
    AtlasAxisScore,
    AtlasAxisSubItem,
    AtlasFourAxisEvaluation,
    CompanyImplementationStatus,
    CompetitiveAnalysis,
    CompetitorDataPoint,
    CompetitorRationale,
    ConsultingReport,
    DataFreshness,
    EnhancedDimensionScore,
    FutureOutlook,
    ImplementationMatrix,
    ImplementationStatus,
    InvestmentThesis,
    MarketChart,
    MarketPosition,
    MatrixItem,
    SiteVerificationItem,
    SiteVerificationReport,
    StrategicAction,
    StrategicAdvice,
    SWOTAnalysis,
    SWOTItem,
    YearProjection,
)

logger = logging.getLogger(__name__)


def parse_consulting_json(file_path: str | Path) -> ConsultingReport:
    """Load a consulting report JSON file (or raw JSON string) and return a validated model.

    Args:
        file_path: Path to the JSON file produced by the IDE AI, or raw JSON text.

    Returns:
        A validated ``ConsultingReport`` instance with missing fields
        filled with safe defaults and scores clamped to valid ranges.
    """
    if isinstance(file_path, Path):
        raw_text = file_path.read_text(encoding="utf-8")
    else:
        s = str(file_path).strip()
        p = Path(s)
        try:
            if p.is_file():
                raw_text = p.read_text(encoding="utf-8")
            else:
                raw_text = s
        except OSError:
            raw_text = s
    data = _extract_json(raw_text)
    return _build_report(data)


def parse_consulting_dict(data: dict[str, Any]) -> ConsultingReport:
    """Build a ConsultingReport from an already-parsed dict."""
    return _build_report(data)


def parse_consulting_response(raw: str | dict[str, Any] | Path) -> ConsultingReport:
    """Parse consulting response from raw JSON string, dict, or file path."""
    if isinstance(raw, dict):
        return parse_consulting_dict(raw)
    if isinstance(raw, Path):
        return parse_consulting_json(raw)
    stripped = raw.strip()
    if stripped.startswith("{") or stripped.startswith("[") or stripped.startswith("```"):
        return parse_consulting_dict(_extract_json(stripped))
    return parse_consulting_json(raw)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from raw text, handling markdown code blocks."""
    def _unwrap_obj(obj: Any) -> dict[str, Any] | None:
        if isinstance(obj, dict):
            return obj
        if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
            return obj[0]
        return None

    # Try direct parse first
    text = text.strip()
    try:
        loaded = json.loads(text)
        res = _unwrap_obj(loaded)
        if res is not None:
            return res
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        try:
            loaded = json.loads(match.group(1).strip())
            res = _unwrap_obj(loaded)
            if res is not None:
                return res
        except json.JSONDecodeError:
            pass

    # Try finding the outermost { ... }
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            loaded = json.loads(text[brace_start : brace_end + 1])
            res = _unwrap_obj(loaded)
            if res is not None:
                return res
        except json.JSONDecodeError:
            pass

    # Try finding the outermost [ ... ] (in case JSON root is a list of objects)
    bracket_start = text.find("[")
    bracket_end = text.rfind("]")
    if bracket_start != -1 and bracket_end > bracket_start:
        try:
            loaded = json.loads(text[bracket_start : bracket_end + 1])
            res = _unwrap_obj(loaded)
            if res is not None:
                return res
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Could not parse consulting report JSON: root must be a JSON object."
    )


def _clamp(value: Any, lo: float, hi: float, default: float = 0.0) -> float:
    fallback = max(lo, min(hi, default))
    if value is None:
        return fallback
    try:
        f = float(value)
        if not math.isfinite(f):
            return fallback
        return max(lo, min(hi, f))
    except (ValueError, TypeError):
        return fallback


_FALSE_POSITIVE_PATTERNS = (
    "[dismissed]",
    "[false positive]",
    "[false-positive]",
    "(false positive)",
    "(false-positive)",
    "dismissed as false",
    "heuristic false positive",
    "heuristic false-positive",
    "no actual risk",
    "誤検知・無効化",
    "誤検知/無効化",
    "無効化済",
    "実質的なリスクなし",
    "実質的リスクなし",
    "this is a false positive",
    "is a false positive",
    "this is a false-positive",
    "is a false-positive",
)

_DISMISSED_FALSE_POSITIVE_RE = re.compile(
    r"(?:"
    r"\[dismissed\]"
    r"|\[false[ -]positive\]"
    r"|\(false[ -]positive\)"
    r"|\bheuristic false[ -]positive\b"
    r"|\bdismissed as false\b"
    r"|\bno actual risk\b"
    r"|\b(?:this|it)\s+is\s+a\s+false[ -]positive\b"
    r"|\bis\s+a\s+false[ -]positive\b"
    r"|\bconsidered\s+(?:a\s+)?false[ -]positive\b"
    r"|\btreated\s+as\s+(?:a\s+)?false[ -]positive\b"
    r"|\bmarked\s+as\s+(?:a\s+)?false[ -]positive\b"
    r"|false[ -]positive\s+(?:discrepancy|alarm|noise|warning)"
    r"|false[ -]positive\s+(?:caused\s+by|due\s+to)"
    r"|^\[?false[ -]positive\]?\s*[:\-]"
    r"|誤検知[・/、\s]*(?:無効化|除外|無視|対象外)"
    r"|無効化済"
    r"|実質的(?:な)?リスクなし"
    r"|リスク(?:は)?ありません"
    r"|誤検知(?:と判定|として除外|として無視)"
    r"|^\[?誤検知\]?\s*[:\-・]"
    r")",
    re.IGNORECASE,
)

_NEGATION_PATTERNS = (
    "not a false positive",
    "not a false-positive",
    "no false positive",
    "no false-positive",
    "isn't a false positive",
    "isn't a false-positive",
    "not false positive",
    "誤検知ではない",
    "誤検知ではなく",
    "誤検知ではありません",
)


def _filter_red_flags(raw_flags: Any) -> list[dict[str, Any]]:
    """Filter out heuristic false-positive / dismissed items from red_flags."""
    if not isinstance(raw_flags, list):
        return []
    filtered: list[dict[str, Any]] = []
    for item in raw_flags:
        if not isinstance(item, dict):
            continue
        norm_item = dict(item)
        for k in ("title", "description", "severity", "business_impact"):
            if k in norm_item:
                norm_item[k] = str(norm_item[k] if norm_item[k] is not None else "")
        title = str(norm_item.get("title", "")).lower()
        desc = str(norm_item.get("description", "")).lower()
        combined = f"{title} {desc}"
        if any(neg in combined for neg in _NEGATION_PATTERNS):
            filtered.append(norm_item)
            continue
        if any(pat in combined for pat in _FALSE_POSITIVE_PATTERNS) or _DISMISSED_FALSE_POSITIVE_RE.search(combined):
            continue
        filtered.append(norm_item)
    return filtered


def _build_report(data: dict[str, Any]) -> ConsultingReport:
    """Build and validate a ConsultingReport from a raw dict."""

    # --- dimension scores ---
    raw_dims = data.get("dimension_scores") if isinstance(data.get("dimension_scores"), dict) else {}
    dimension_scores: dict[str, EnhancedDimensionScore] = {}
    for key, val in raw_dims.items():
        if isinstance(val, dict):
            dimension_scores[key] = EnhancedDimensionScore(
                score=_clamp(val.get("score", 0), 0, 100),
                level=int(_clamp(val.get("level", 1), 1, 10, default=1)),
                label=str(val.get("label", "")),
                rationale=str(val.get("rationale", "")),
                business_explanation=str(val.get("business_explanation", "")),
                enables=str(val.get("enables", "")),
            )

    # --- SWOT ---
    raw_swot = data.get("swot") if isinstance(data.get("swot"), dict) else {}
    swot = SWOTAnalysis(
        strengths=[SWOTItem(**s) for s in (raw_swot.get("strengths") or []) if isinstance(s, dict)],
        weaknesses=[SWOTItem(**s) for s in (raw_swot.get("weaknesses") or []) if isinstance(s, dict)],
        opportunities=[SWOTItem(**s) for s in (raw_swot.get("opportunities") or []) if isinstance(s, dict)],
        threats=[SWOTItem(**s) for s in (raw_swot.get("threats") or []) if isinstance(s, dict)],
    )

    # --- Future outlook ---
    raw_outlook = data.get("future_outlook") if isinstance(data.get("future_outlook"), dict) else {}
    future_outlook = FutureOutlook(
        product_vision=str(raw_outlook.get("product_vision", "")),
        viability_assessment=str(raw_outlook.get("viability_assessment", "")),
        year_1=_parse_projection(raw_outlook.get("year_1")),
        year_3=_parse_projection(raw_outlook.get("year_3")),
        year_5=_parse_projection(raw_outlook.get("year_5")),
    )

    # --- Strategic advice ---
    raw_advice = data.get("strategic_advice") if isinstance(data.get("strategic_advice"), dict) else {}
    strategic_advice = StrategicAdvice(
        immediate_actions=[
            StrategicAction(**a)
            for a in (raw_advice.get("immediate_actions") or [])
            if isinstance(a, dict)
        ],
        medium_term=[
            StrategicAction(**a)
            for a in (raw_advice.get("medium_term") or [])
            if isinstance(a, dict)
        ],
        long_term_vision=str(raw_advice.get("long_term_vision", "")),
    )

    # --- Investment thesis ---
    raw_thesis = data.get("investment_thesis") if isinstance(data.get("investment_thesis"), dict) else {}
    investment_thesis = InvestmentThesis(
        recommendation=str(raw_thesis.get("recommendation", "")),
        rationale=str(raw_thesis.get("rationale", "")),
        key_risks=_ensure_str_list(raw_thesis.get("key_risks", [])),
        key_upside=_ensure_str_list(raw_thesis.get("key_upside", [])),
        comparable_companies=_ensure_str_list(raw_thesis.get("comparable_companies", [])),
        suggested_valuation_factors=str(raw_thesis.get("suggested_valuation_factors", "")),
    )

    # --- Site verification ---
    site_verification: SiteVerificationReport | None = None
    raw_sv = data.get("site_verification")
    if isinstance(raw_sv, dict):
        sv_items: list[SiteVerificationItem] = []
        for item in (raw_sv.get("items") or []):
            if isinstance(item, dict):
                sv_items.append(SiteVerificationItem(
                    item_key=str(item.get("item_key", "")),
                    item_name=str(item.get("item_name", "")),
                    item_name_ja=str(item.get("item_name_ja", "")),
                    score=_clamp(item.get("score", 0), 0, 100),
                    confidence=str(item.get("confidence", "medium")),
                    rationale=str(item.get("rationale", "")),
                    evidence=_ensure_str_list(item.get("evidence", [])),
                ))
        site_verification = SiteVerificationReport(
            urls_analyzed=_ensure_str_list(raw_sv.get("urls_analyzed") or []),
            items=sv_items,
            overall_credibility=_clamp(raw_sv.get("overall_credibility", 0), 0, 100),
            summary=str(raw_sv.get("summary", "")),
        )

    # --- Competitive analysis ---
    competitive_analysis: CompetitiveAnalysis | None = None
    raw_ca = data.get("competitive_analysis")
    if isinstance(raw_ca, dict):
        markets: list[MarketPosition] = []
        for mkt in (raw_ca.get("markets") or []):
            if not isinstance(mkt, dict):
                continue
            charts: list[MarketChart] = []
            for ch in (mkt.get("charts") or []):
                if not isinstance(ch, dict):
                    continue
                data_points: list[CompetitorDataPoint] = []
                for dp in (ch.get("data_points") or []):
                    if not isinstance(dp, dict):
                        continue
                    data_points.append(CompetitorDataPoint(
                        name=str(dp.get("name", "")),
                        x=_clamp(dp.get("x", 0), 0, 100),
                        y=_clamp(dp.get("y", 0), 0, 100),
                        z=_clamp(dp.get("z", 0), 0, 100),
                        is_target=bool(dp.get("is_target", False)),
                        sources=_ensure_str_list(dp.get("sources", [])),
                        last_verified=str(dp.get("last_verified", "") or ""),
                    ))
                charts.append(MarketChart(
                    chart_type=str(ch.get("chart_type", "")),
                    title=str(ch.get("title", "")),
                    title_ja=str(ch.get("title_ja", "")),
                    x_axis_label=str(ch.get("x_axis_label", "")),
                    x_axis_label_ja=str(ch.get("x_axis_label_ja", "")),
                    y_axis_label=str(ch.get("y_axis_label", "")),
                    y_axis_label_ja=str(ch.get("y_axis_label_ja", "")),
                    x_axis_rationale=str(ch.get("x_axis_rationale", "")),
                    x_axis_rationale_ja=str(ch.get("x_axis_rationale_ja", "")),
                    y_axis_rationale=str(ch.get("y_axis_rationale", "")),
                    y_axis_rationale_ja=str(ch.get("y_axis_rationale_ja", "")),
                    data_points=data_points,
                ))
            markets.append(MarketPosition(
                market_name=str(mkt.get("market_name", "")),
                market_name_ja=str(mkt.get("market_name_ja", "")),
                charts=charts,
            ))
        competitive_analysis = CompetitiveAnalysis(
            target_company=str(raw_ca.get("target_company", "")),
            home_country=str(raw_ca.get("home_country", "")),
            markets=markets,
        )

    atlas_four_axis = _parse_atlas_four_axis(data.get("atlas_four_axis"))
    implementation_matrix = _parse_implementation_matrix(data.get("implementation_matrix"))
    competitor_rationales = _parse_competitor_rationales(data.get("competitor_rationales"))

    overall_score = _clamp(data.get("overall_score", 0), 0, 100)
    grade = str(data.get("grade", "") or "").strip().upper()

    if dimension_scores:
        dim_mean = sum(d.score for d in dimension_scores.values()) / len(dimension_scores)
        if abs(dim_mean - overall_score) > 40:
            overall_score = round(dim_mean, 1)
            if overall_score >= 90:
                grade = "A"
            elif overall_score >= 75:
                grade = "B"
            elif overall_score >= 60:
                grade = "C"
            elif overall_score >= 40:
                grade = "D"
            else:
                grade = "F"
    if not grade:
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 75:
            grade = "B"
        elif overall_score >= 60:
            grade = "C"
        elif overall_score >= 40:
            grade = "D"
        else:
            grade = "F"

    tech_level_summary = data.get("tech_level_summary") if isinstance(data.get("tech_level_summary"), dict) else {}
    glossary_additions = data.get("glossary_additions") if isinstance(data.get("glossary_additions"), list) else []

    return ConsultingReport(
        executive_summary=str(data.get("executive_summary", "")),
        executive_summary_business=str(data.get("executive_summary_business", "")),
        dimension_scores=dimension_scores,
        overall_score=overall_score,
        grade=grade,
        swot=swot,
        future_outlook=future_outlook,
        strategic_advice=strategic_advice,
        investment_thesis=investment_thesis,
        red_flags=_filter_red_flags(data.get("red_flags", [])),
        tech_level_summary=tech_level_summary,
        glossary_additions=glossary_additions,
        ai_model_used=str(data.get("ai_model_used", "")),
        analysis_id=str(data.get("analysis_id", "")),
        project_name=str(data.get("project_name", "")),
        site_verification=site_verification,
        competitive_analysis=competitive_analysis,
        atlas_four_axis=atlas_four_axis,
        implementation_matrix=implementation_matrix,
        competitor_rationales=competitor_rationales,
        data_freshness=_parse_data_freshness(data.get("data_freshness")),
    )


def _parse_data_freshness(raw: Any) -> DataFreshness | None:
    """Parse the STEP 0 web-research provenance block (v0.3.2 schema)."""
    if not isinstance(raw, dict):
        return None
    warning = raw.get("data_cutoff_warning")
    wsp = raw.get("web_search_performed", False)
    if isinstance(wsp, str):
        wsp_bool = wsp.strip().lower() in ("true", "1", "yes")
    else:
        wsp_bool = bool(wsp)
    return DataFreshness(
        web_search_performed=wsp_bool,
        search_date=str(raw.get("search_date", "") or ""),
        queries_executed=_ensure_str_list(raw.get("queries_executed")),
        sources_consulted=_ensure_str_list(raw.get("sources_consulted")),
        data_cutoff_warning=str(warning) if warning else None,
    )


def _parse_competitor_rationales(data: Any) -> list[CompetitorRationale]:
    """Parse competitor selection rationales (3-5 lines each) — v0.3.1."""
    if not isinstance(data, list):
        return []
    out: list[CompetitorRationale] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        out.append(
            CompetitorRationale(
                name=str(item.get("name", "")),
                category=str(item.get("category", "")),
                rationale_en=str(item.get("rationale_en", "")),
                rationale_ja=str(item.get("rationale_ja", "")),
                hq_country=str(item.get("hq_country", "")),
                market_position=str(item.get("market_position", "")),
                estimated_score=_clamp(item.get("estimated_score", 0), 0, 100),
            )
        )
    return out


def _parse_atlas_four_axis(data: Any) -> AtlasFourAxisEvaluation | None:
    """Parse Atlas 4-axis evaluation block (Task C)."""
    if not isinstance(data, dict):
        return None

    axes: list[AtlasAxisScore] = []
    for axis_data in data.get("axes", []) or []:
        if not isinstance(axis_data, dict):
            continue
        sub_items: list[AtlasAxisSubItem] = []
        for si in axis_data.get("sub_items", []) or []:
            if not isinstance(si, dict):
                continue
            sub_items.append(
                AtlasAxisSubItem(
                    key=str(si.get("key", "")),
                    name_en=str(si.get("name_en", "")),
                    name_ja=str(si.get("name_ja", "")),
                    score=_clamp(si.get("score", 0), 0, 100),
                    level=int(_clamp(si.get("level", 1), 1, 10)),
                    weight_pct=_clamp(si.get("weight_pct", 0), 0, 100),
                    rationale=str(si.get("rationale", "")),
                )
            )
        axes.append(
            AtlasAxisScore(
                axis_key=str(axis_data.get("axis_key", "")),
                name_en=str(axis_data.get("name_en", "")),
                name_ja=str(axis_data.get("name_ja", "")),
                weight_pct=_clamp(axis_data.get("weight_pct", 0), 0, 100),
                score=_clamp(axis_data.get("score", 0), 0, 100),
                level=int(_clamp(axis_data.get("level", 1), 1, 10)),
                rationale=str(axis_data.get("rationale", "")),
                sub_items=sub_items,
            )
        )

    return AtlasFourAxisEvaluation(
        axes=axes,
        overall_score=_clamp(data.get("overall_score", 0), 0, 100),
        industry_context=str(data.get("industry_context", "")),
        summary=str(data.get("summary", "")),
        summary_ja=str(data.get("summary_ja", "")),
    )


def _parse_implementation_matrix(data: Any) -> ImplementationMatrix | None:
    """Parse Implementation Capability Matrix (Task D)."""
    if not isinstance(data, dict):
        return None

    items: list[MatrixItem] = []
    for item_data in data.get("items", []) or []:
        if not isinstance(item_data, dict):
            continue
        statuses: list[CompanyImplementationStatus] = []
        for s in item_data.get("statuses", []) or []:
            if not isinstance(s, dict):
                continue
            # Parse status enum with safe fallback to UNKNOWN
            raw_status = str(s.get("status", "unknown")).lower()
            try:
                status_enum = ImplementationStatus(raw_status)
            except ValueError:
                status_enum = ImplementationStatus.UNKNOWN
            statuses.append(
                CompanyImplementationStatus(
                    company_name=str(s.get("company_name", "")),
                    status=status_enum,
                    evidence=str(s.get("evidence", "")),
                    sources=_ensure_str_list(s.get("sources", [])),
                    last_verified=str(s.get("last_verified", "") or ""),
                )
            )
        items.append(
            MatrixItem(
                category=str(item_data.get("category", "")),
                item_key=str(item_data.get("item_key", "")),
                item_en=str(item_data.get("item_en", "")),
                item_ja=str(item_data.get("item_ja", "")),
                statuses=statuses,
            )
        )

    return ImplementationMatrix(
        target_company=str(data.get("target_company", "")),
        competitors=[str(c) for c in (data.get("competitors", []) or [])],
        items=items,
    )


def _parse_projection(raw: Any) -> YearProjection | None:
    if not isinstance(raw, dict):
        return None
    return YearProjection(
        projection=str(raw.get("projection", "")),
        confidence=str(raw.get("confidence", "medium")),
        key_milestones=_ensure_str_list(raw.get("key_milestones", [])),
    )


def _ensure_str_list(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, str):
        s = val.strip()
        return [s] if s else []
    if isinstance(val, (list, tuple, set)):
        return [str(item) for item in val if item is not None and str(item).strip()]
    return []
