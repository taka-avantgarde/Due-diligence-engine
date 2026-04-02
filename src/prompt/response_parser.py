"""Parse AI-generated consulting report JSON into ConsultingReport model.

Used by ``dde report --consulting result.json`` to load and validate
the structured JSON output produced by IDE AI (Claude Code, Cursor, etc.).
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from src.models import (
    ConsultingReport,
    EnhancedDimensionScore,
    FutureOutlook,
    InvestmentThesis,
    StrategicAction,
    StrategicAdvice,
    SWOTAnalysis,
    SWOTItem,
    YearProjection,
)

logger = logging.getLogger(__name__)


def parse_consulting_json(file_path: str | Path) -> ConsultingReport:
    """Load a consulting report JSON file and return a validated model.

    Args:
        file_path: Path to the JSON file produced by the IDE AI.

    Returns:
        A validated ``ConsultingReport`` instance with missing fields
        filled with safe defaults and scores clamped to valid ranges.
    """
    path = Path(file_path)
    raw_text = path.read_text(encoding="utf-8")
    data = _extract_json(raw_text)
    return _build_report(data)


def parse_consulting_dict(data: dict[str, Any]) -> ConsultingReport:
    """Build a ConsultingReport from an already-parsed dict."""
    return _build_report(data)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from raw text, handling markdown code blocks."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    match = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding the outermost { ... }
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start : brace_end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Could not parse consulting report JSON. "
        "Ensure the AI output is valid JSON."
    )


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _build_report(data: dict[str, Any]) -> ConsultingReport:
    """Build and validate a ConsultingReport from a raw dict."""

    # --- dimension scores ---
    raw_dims = data.get("dimension_scores", {})
    dimension_scores: dict[str, EnhancedDimensionScore] = {}
    for key, val in raw_dims.items():
        if isinstance(val, dict):
            dimension_scores[key] = EnhancedDimensionScore(
                score=_clamp(float(val.get("score", 0)), 0, 100),
                level=int(_clamp(float(val.get("level", 1)), 1, 10)),
                label=str(val.get("label", "")),
                rationale=str(val.get("rationale", "")),
                business_explanation=str(val.get("business_explanation", "")),
                enables=str(val.get("enables", "")),
            )

    # --- SWOT ---
    raw_swot = data.get("swot", {})
    swot = SWOTAnalysis(
        strengths=[SWOTItem(**s) for s in raw_swot.get("strengths", []) if isinstance(s, dict)],
        weaknesses=[SWOTItem(**s) for s in raw_swot.get("weaknesses", []) if isinstance(s, dict)],
        opportunities=[SWOTItem(**s) for s in raw_swot.get("opportunities", []) if isinstance(s, dict)],
        threats=[SWOTItem(**s) for s in raw_swot.get("threats", []) if isinstance(s, dict)],
    )

    # --- Future outlook ---
    raw_outlook = data.get("future_outlook", {})
    future_outlook = FutureOutlook(
        product_vision=str(raw_outlook.get("product_vision", "")),
        viability_assessment=str(raw_outlook.get("viability_assessment", "")),
        year_1=_parse_projection(raw_outlook.get("year_1")),
        year_3=_parse_projection(raw_outlook.get("year_3")),
        year_5=_parse_projection(raw_outlook.get("year_5")),
    )

    # --- Strategic advice ---
    raw_advice = data.get("strategic_advice", {})
    strategic_advice = StrategicAdvice(
        immediate_actions=[
            StrategicAction(**a)
            for a in raw_advice.get("immediate_actions", [])
            if isinstance(a, dict)
        ],
        medium_term=[
            StrategicAction(**a)
            for a in raw_advice.get("medium_term", [])
            if isinstance(a, dict)
        ],
        long_term_vision=str(raw_advice.get("long_term_vision", "")),
    )

    # --- Investment thesis ---
    raw_thesis = data.get("investment_thesis", {})
    investment_thesis = InvestmentThesis(
        recommendation=str(raw_thesis.get("recommendation", "")),
        rationale=str(raw_thesis.get("rationale", "")),
        key_risks=_ensure_str_list(raw_thesis.get("key_risks", [])),
        key_upside=_ensure_str_list(raw_thesis.get("key_upside", [])),
        comparable_companies=_ensure_str_list(raw_thesis.get("comparable_companies", [])),
        suggested_valuation_factors=str(raw_thesis.get("suggested_valuation_factors", "")),
    )

    return ConsultingReport(
        executive_summary=str(data.get("executive_summary", "")),
        executive_summary_business=str(data.get("executive_summary_business", "")),
        dimension_scores=dimension_scores,
        overall_score=_clamp(float(data.get("overall_score", 0)), 0, 100),
        grade=str(data.get("grade", "")),
        swot=swot,
        future_outlook=future_outlook,
        strategic_advice=strategic_advice,
        investment_thesis=investment_thesis,
        red_flags=data.get("red_flags", []),
        tech_level_summary=data.get("tech_level_summary", {}),
        glossary_additions=data.get("glossary_additions", []),
        ai_model_used=str(data.get("ai_model_used", "")),
        analysis_id=str(data.get("analysis_id", "")),
        project_name=str(data.get("project_name", "")),
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
    if not isinstance(val, list):
        return []
    return [str(item) for item in val]
