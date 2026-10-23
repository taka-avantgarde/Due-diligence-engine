"""Zero-Drift & Zero-Defect Invariant Test Suite.

Guarantees that:
1. Version SSOT across __version__, pyproject.toml, 6 READMEs, and HTML templates never drifts.
2. Model & pricing SSOT across config.py and providers.py remains in sync, with fail-closed bounds.
3. Prompt & schema contain zero legacy references (e.g. 6 dimensions, 25% originality).
4. 6-Language README parity is strictly maintained (localized flags, modern models, zero stale strings).
5. 14-Language PDF dictionaries (_PDF_I18N, _DIM_NAME_MAPS, _PDF_GRADE_REC) have identical key sets.
6. Edge-case regressions (score=0.0 cover, PDF i18n leaks, Arabic/Thai Helvetica wrapping,
   JSON parser resilience, RFC 6598 SSRF blocking, claim level monotonicity) are prevented.
"""

from __future__ import annotations

import ipaddress
import json
import re
from pathlib import Path

import pytest

import due_diligence_engine
from due_diligence_engine import config
from due_diligence_engine.ai import providers
from due_diligence_engine.analyze.site_analyzer import _is_ip_safe
from due_diligence_engine.prompt.response_parser import parse_consulting_json
from types import SimpleNamespace

from due_diligence_engine.report.pdf_generator import (
    _DIM_NAME_MAPS,
    _PDF_GRADE_REC,
    _PDF_I18N,
    PDFReportGenerator,
    _build_styles,
)
from due_diligence_engine.score.scorer import Scorer
from tests.test_consulting_pdf import (
    ALL_REPORT_LANGS,
    _make_analysis_result,
    _make_consulting_report,
)

_ROOT = Path(__file__).resolve().parent.parent
_PKG = _ROOT / "due_diligence_engine"


def _make_generator(lang: str = "en") -> PDFReportGenerator:
    gen = PDFReportGenerator()
    gen._lang = lang if lang in _PDF_I18N else "en"
    gen._styles = _build_styles(gen._lang)
    gen._t = _PDF_I18N.get(gen._lang, _PDF_I18N["en"])
    return gen


# ==============================================================================
# 1. Version SSOT Invariant
# ==============================================================================
def test_version_ssot_invariant():
    """Verify that due_diligence_engine.__version__ is the single source of truth."""
    version = due_diligence_engine.__version__
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), f"Invalid version format: {version}"

    # pyproject.toml
    pyproject_text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
    assert m is not None, "pyproject.toml missing version"
    assert m.group(1) == version, f"pyproject.toml version {m.group(1)} != {version}"

    # All 6 READMEs: check version badge and footer
    readmes = ["README.md", "README.ja.md", "README.es.md", "README.ar.md", "README.fr.md", "README.de.md"]
    badge_pattern = f"version-v{version}-"
    for r_name in readmes:
        content = (_ROOT / r_name).read_text(encoding="utf-8")
        assert badge_pattern in content or f"version-v{version}" in content, (
            f"{r_name} missing version badge for v{version}"
        )
        assert f"v{version}" in content, f"{r_name} missing v{version} mention"

    # Scorecard HTML template parity and zero legacy version
    tpl_root = (_ROOT / "templates" / "scorecard.html").read_text(encoding="utf-8")
    tpl_pkg = (_PKG / "report" / "templates" / "scorecard.html").read_text(encoding="utf-8")
    assert tpl_root == tpl_pkg, "Root and package scorecard.html templates must be byte-for-byte identical"
    assert "v0.1.0" not in tpl_root, "scorecard.html template contains stale hardcoded v0.1.0"


# ==============================================================================
# 2. Model & Pricing SSOT Invariant
# ==============================================================================
def test_model_and_pricing_ssot_invariant():
    """Verify model IDs and cost structures derive strictly from SSOT in config.py."""
    # BYOK Defaults match SSOT
    assert config.BYOK_DEFAULT_MODELS == providers._DEFAULT_MODELS
    assert providers._DEFAULT_MODELS["claude"] == config.MODELS["sonnet"].model_id
    assert providers._DEFAULT_MODELS["gemini"] == "gemini-4-argon"
    assert providers._DEFAULT_MODELS["chatgpt"] == "gpt-6.1-sol"

    # Required modern models in PROVIDER_MODEL_COSTS
    required_models = {
        "claude-haiku-5-5",
        "claude-sonnet-5-5",
        "claude-fable-5-1",
        "gemini-4-argon",
        "gpt-6.1-sol",
        "gpt-6-astra",
        "gpt-5",
    }
    for model_id in required_models:
        assert model_id in config.PROVIDER_MODEL_COSTS, f"Missing {model_id} in PROVIDER_MODEL_COSTS"
        costs = config.PROVIDER_MODEL_COSTS[model_id]
        assert costs["input"] > 0 and costs["output"] > 0

    # No legacy 'Haiku→Sonnet→Opus' references in codebase
    for py in _PKG.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "Haiku→Sonnet→Opus" not in text, f"Legacy model pipeline found in {py}"
        assert "Haiku->Sonnet->Opus" not in text, f"Legacy model pipeline found in {py}"

    # Haiku pricing: >100k tier rate applied
    cost_under_100k = config.estimate_cost("haiku", 50_000, 10_000)
    assert abs(cost_under_100k - (50_000 * 0.10 / 1e6 + 10_000 * 0.50 / 1e6)) < 1e-6

    cost_over_100k = config.estimate_cost("haiku", 200_000, 10_000)
    # Tier rate >100k input: $0.50 input, $2.50 output per MTok
    expected_over_100k = 200_000 * 0.50 / 1e6 + 10_000 * 2.50 / 1e6
    assert abs(cost_over_100k - expected_over_100k) < 1e-6
    assert cost_over_100k > cost_under_100k

    # Negative tokens clamped to 0
    assert config.estimate_cost("sonnet", -100, -50) == 0.0
    assert providers.estimate_provider_cost("claude", -10, -10, model_id="claude-sonnet-5-5") == 0.0


# ==============================================================================
# 3. Prompt & Schema Invariant
# ==============================================================================
def test_prompt_and_schema_invariant():
    """Verify consulting prompt generator contains zero legacy dimensions or outdated weights."""
    prompt_txt = (_PKG / "prompt" / "generator.py").read_text(encoding="utf-8")

    assert "6 dimensions" not in prompt_txt, "Found legacy '6 dimensions' in generator.py"
    assert "6次元" not in prompt_txt, "Found legacy '6次元' in generator.py"
    assert "Technical Originality (25%)" not in prompt_txt, "Found legacy 25% originality weight"
    assert "技術独自性（25%）" not in prompt_txt, "Found legacy 25% originality weight (JA)"
    assert "mean of all 9 scores" not in prompt_txt, "Found legacy 9 scores calculation"
    assert "average of all 9 scores" not in prompt_txt, "Found legacy 9 scores calculation"


# ==============================================================================
# 4. 6-Language README Parity Invariant
# ==============================================================================
def test_six_language_readme_parity_invariant():
    """Verify all 6 README files have localized flags, modern models, and zero stale text."""
    configs = {
        "README.md": ("", "en"),
        "README.ja.md": ("--lang ja", "ja"),
        "README.es.md": ("--lang es", "es"),
        "README.ar.md": ("--lang ar", "ar"),
        "README.fr.md": ("--lang fr", "fr"),
        "README.de.md": ("--lang de", "de"),
    }

    for fname, (lang_flag, lang_code) in configs.items():
        content = (_ROOT / fname).read_text(encoding="utf-8")

        # Localized command in Quick Start and ASCII diagram
        if lang_flag:
            assert f"dde prompt --pdf {lang_flag}" in content, f"Missing '{lang_flag}' in {fname}"
        else:
            assert "dde prompt --pdf" in content, f"Missing base command in {fname}"

        # Modern AI model tier references present in all 6 files
        assert "Astra" in content or "GPT-6.1-Sol" in content, f"Missing Astra / GPT-6.1-Sol in {fname}"
        assert "Claude Fable 5.1" in content, f"Missing Claude Fable 5.1 in {fname}"
        assert "Gemini 4 Argon" in content, f"Missing Gemini 4 Argon in {fname}"

        # Zero stale strings
        assert "22 ページ" not in content, f"Found stale '22 ページ' in {fname}"
        assert "v0.3.x+" not in content, f"Found stale roadmap header 'v0.3.x+' in {fname}"
        assert "(v0.4.0+)" not in content, f"Found stale roadmap header '(v0.4.0+)' in {fname}"


# ==============================================================================
# 5. 14-Language PDF Dictionary Parity Invariant
# ==============================================================================
def test_fourteen_language_pdf_dictionary_parity_invariant():
    """Verify that all 14 supported report languages have complete, identical translation keys."""
    en_i18n_keys = set(_PDF_I18N["en"].keys())
    en_grade_keys = set(_PDF_GRADE_REC["en"].keys())

    for lang in ALL_REPORT_LANGS:
        assert lang in _PDF_I18N, f"Missing {lang} in _PDF_I18N"
        diff_i18n = en_i18n_keys ^ set(_PDF_I18N[lang].keys())
        assert not diff_i18n, f"Key mismatch in _PDF_I18N[{lang}]: {diff_i18n}"

        assert lang in _PDF_GRADE_REC, f"Missing {lang} in _PDF_GRADE_REC"
        diff_grades = en_grade_keys ^ set(_PDF_GRADE_REC[lang].keys())
        assert not diff_grades, f"Key mismatch in _PDF_GRADE_REC[{lang}]: {diff_grades}"

    # _DIM_NAME_MAPS has 13 non-en languages; verify all share identical keys
    ja_dim_keys = set(_DIM_NAME_MAPS["ja"].keys())
    for lang in ALL_REPORT_LANGS:
        if lang == "en":
            continue
        assert lang in _DIM_NAME_MAPS, f"Missing {lang} in _DIM_NAME_MAPS"
        diff_dims = ja_dim_keys ^ set(_DIM_NAME_MAPS[lang].keys())
        assert not diff_dims, f"Key mismatch in _DIM_NAME_MAPS[{lang}]: {diff_dims}"


# ==============================================================================
# 6. Edge-Case Regression Invariants
# ==============================================================================
def test_edge_case_cover_page_renders_zero_score():
    """Cover page must render '0 / 100' when overall_score == 0.0."""
    cr = _make_consulting_report()
    cr.overall_score = 0.0
    ar = _make_analysis_result(cr)
    gen = _make_generator("en")

    flowables = gen._build_cover_page(ar)
    # Check that score Paragraph is produced with 0
    score_paras = [getattr(el, "text", "") for el in flowables if "/ 100" in getattr(el, "text", "")]
    assert len(score_paras) == 1, "Cover page should render score when overall_score == 0.0"
    assert ">0</font>" in score_paras[0] or ">0.0</font>" in score_paras[0] or ">0 <" in score_paras[0]


def test_edge_case_non_ja_pdf_does_not_leak_japanese():
    """Non-Japanese PDFs (es, fr, de) must not leak Japanese fallback strings."""
    cr = _make_consulting_report()
    ar = _make_analysis_result(cr)

    for test_lang in ("es", "fr", "de"):
        gen = _make_generator(test_lang)
        flowables = gen._build_ai_provider_section(ar)

        texts = []
        for el in flowables:
            if hasattr(el, "text"):
                texts.append(el.text)
            elif hasattr(el, "_cellvalues"):
                for row in el._cellvalues:
                    for cell in row:
                        if hasattr(cell, "text"):
                            texts.append(cell.text)
                        elif isinstance(cell, str):
                            texts.append(cell)

        combined = " ".join(texts)
        assert "AIプロバイダー分析" not in combined, f"Leaked Japanese string in {test_lang} PDF"
        assert "プロバイダースコア比較" not in combined, f"Leaked Japanese string in {test_lang} PDF"
        assert "コスト (USD)" not in combined, f"Leaked Japanese string in {test_lang} PDF"


def test_edge_case_esc_text_wraps_helvetica_for_ar_and_th():
    """_esc_text must wrap ASCII/Latin/digit runs in Helvetica for ar and th, but not en/es."""
    gen_ar = _make_generator("ar")
    gen_th = _make_generator("th")
    gen_en = _make_generator("en")

    assert '<font name="Helvetica">' in gen_ar._esc_text("Test 123")
    assert '<font name="Helvetica">' in gen_th._esc_text("Test 123")
    assert '<font name="Helvetica">' not in gen_en._esc_text("Test 123")


def test_edge_case_parse_consulting_json_resilience():
    """parse_consulting_json must handle root lists, boolean strings, and string URL sources."""
    payload = json.dumps([
        {
            "project_name": "ResilienceApp",
            "executive_summary": "Testing resilient parsing",
            "dimension_scores": {
                "technical_originality": {"score": 8.0, "reasoning": "ok"},
                "technology_advancement": {"score": 8.0, "reasoning": "ok"},
                "architecture_quality": {"score": 8.0, "reasoning": "ok"},
                "implementation_capability": {"score": 8.0, "reasoning": "ok"},
                "market_readiness": {"score": 8.0, "reasoning": "ok"},
            },
            "overall_score": 80.0,
            "data_freshness": {
                "web_search_performed": "false",
                "sources_consulted": "https://example.com/source1",
            },
        }
    ])

    report = parse_consulting_json(payload)
    assert report.project_name == "ResilienceApp"
    assert report.data_freshness is not None
    assert report.data_freshness.web_search_performed is False
    assert report.data_freshness.sources_consulted == ["https://example.com/source1"]


def test_edge_case_site_analyzer_is_ip_safe_blocks_rfc6598():
    """_is_ip_safe must block RFC 6598 carrier-grade NAT space (100.64.0.0/10)."""
    assert not _is_ip_safe(ipaddress.ip_address("100.64.0.1"))
    assert not _is_ip_safe(ipaddress.ip_address("100.100.100.200"))
    assert not _is_ip_safe(ipaddress.ip_address("100.127.255.254"))
    # Standard private / loopback / link-local
    assert not _is_ip_safe(ipaddress.ip_address("127.0.0.1"))
    assert not _is_ip_safe(ipaddress.ip_address("10.0.0.1"))
    assert not _is_ip_safe(ipaddress.ip_address("172.16.0.1"))
    assert not _is_ip_safe(ipaddress.ip_address("192.168.1.1"))
    assert not _is_ip_safe(ipaddress.ip_address("169.254.169.254"))
    # Public routable IPs
    assert _is_ip_safe(ipaddress.ip_address("8.8.8.8"))
    assert _is_ip_safe(ipaddress.ip_address("1.1.1.1"))


def test_edge_case_scorer_determine_claim_level_monotonic():
    """Scorer._determine_claim_level must be monotonically non-increasing as contradictions rise."""
    scorer = Scorer()

    def _call_claim_level(score: float, num_contradictions: int) -> int:
        res = SimpleNamespace(
            consistency=SimpleNamespace(
                consistency_score=score,
                contradictions=["contra"] * num_contradictions,
            )
        )
        return scorer._determine_claim_level(res)  # type: ignore[arg-type]

    for score_val in (95.0, 80.0, 60.0, 40.0, 20.0, 10.0):
        l0 = _call_claim_level(score_val, 0)
        l2 = _call_claim_level(score_val, 2)
        l3 = _call_claim_level(score_val, 3)
        l6 = _call_claim_level(score_val, 6)
        assert l0 >= l2 >= l3 >= l6, (
            f"Monotonicity violation at score {score_val}: 0 c={l0}, 2 c={l2}, 3 c={l3}, 6 c={l6}"
        )

    # Low score (10.0) with contradictions must not be elevated
    assert _call_claim_level(10.0, 3) == 1
    assert _call_claim_level(10.0, 6) == 1
