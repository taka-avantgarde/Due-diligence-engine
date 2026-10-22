"""Guard the Claude model registry in ``config.MODELS`` against drift.

Model IDs must be real, dateless, current-generation IDs from the official
model overview (https://platform.claude.com/docs/en/about-claude/models/overview)
and every call site must read them from ``config.MODELS`` rather than
hardcoding a string.
"""

from __future__ import annotations

import re
from pathlib import Path

from due_diligence_engine.ai import providers
from due_diligence_engine.config import MODELS

_PKG = Path(__file__).resolve().parent.parent / "due_diligence_engine"


def test_three_tiers_present():
    assert set(MODELS) == {"haiku", "sonnet", "fable"}
    assert MODELS["haiku"].purpose == "scan"
    assert MODELS["sonnet"].purpose == "analyze"
    assert MODELS["fable"].purpose == "judge"


def test_model_ids_are_current_dateless_ids():
    # 4.6 世代以降の ID は日付なしスナップショット。日付サフィックス禁止。
    for tier, cfg in MODELS.items():
        assert re.fullmatch(r"claude-[a-z]+-\d+(-\d+)?", cfg.model_id), (tier, cfg.model_id)
        assert not re.search(r"-\d{8}$", cfg.model_id), f"{tier} uses a dated snapshot"
    assert MODELS["haiku"].model_id == "claude-haiku-5-5"
    assert MODELS["sonnet"].model_id == "claude-sonnet-5-5"
    assert MODELS["fable"].model_id == "claude-fable-5-1"


def test_pricing_is_positive_and_ordered_by_tier():
    h, s, f = MODELS["haiku"], MODELS["sonnet"], MODELS["fable"]
    for cfg in (h, s, f):
        assert cfg.input_cost_per_mtok > 0 and cfg.output_cost_per_mtok > 0
        assert cfg.output_cost_per_mtok >= cfg.input_cost_per_mtok
    assert h.input_cost_per_mtok < s.input_cost_per_mtok < f.input_cost_per_mtok


def test_byok_claude_default_follows_registry():
    assert providers._DEFAULT_MODELS["claude"] == MODELS["sonnet"].model_id
    assert providers.PROVIDER_COSTS["claude"]["input"] == MODELS["sonnet"].input_cost_per_mtok
    assert providers.PROVIDER_COSTS["claude"]["output"] == MODELS["sonnet"].output_cost_per_mtok


def test_byok_defaults_are_current():
    assert providers._DEFAULT_MODELS["gemini"] == "gemini-4-argon"
    assert providers._DEFAULT_MODELS["chatgpt"] == "gpt-6.1-sol"
    assert providers._BYOK_MODULE_TO_PACKAGE["google.genai"] == "google-genai"
    assert ("google" + ".generativeai") not in providers._BYOK_MODULE_TO_PACKAGE


def test_no_hardcoded_claude_model_ids_outside_config():
    pattern = re.compile(r"""["']claude-(haiku|sonnet|opus|fable)-\d""")
    offenders = []
    for py in _PKG.rglob("*.py"):
        if py.name == "config.py":
            continue
        for lineno, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                offenders.append(f"{py.relative_to(_PKG)}:{lineno}")
    assert not offenders, f"hardcoded Claude model IDs: {offenders}"
