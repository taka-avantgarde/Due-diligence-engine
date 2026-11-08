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
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

import due_diligence_engine
from due_diligence_engine import config
from due_diligence_engine.ai import providers
from due_diligence_engine.analyze.site_analyzer import _is_ip_safe
from due_diligence_engine.prompt.response_parser import parse_consulting_json
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

    # Scorecard HTML template single SSOT and zero legacy version
    assert not (_ROOT / "templates" / "scorecard.html").exists(), (
        "Duplicate root templates/scorecard.html must not exist; package template is sole SSOT"
    )
    tpl_pkg = (_PKG / "report" / "templates" / "scorecard.html").read_text(encoding="utf-8")
    assert "v0.1.0" not in tpl_pkg, "scorecard.html template contains stale hardcoded v0.1.0"
    assert "{{ version" in tpl_pkg, "scorecard.html must render dynamic version"


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


def test_dependency_and_sdk_contract_invariant():
    """Verify pyproject.toml dependency hygiene, Rust bidi fast-path, and live SDK contracts."""
    import importlib.util
    import inspect
    import tomllib

    pyproject_data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject_data["project"]

    # PEP 639 license string + no deprecated license classifier
    assert project["license"] == "Apache-2.0"
    assert "License :: OSI Approved :: Apache Software License" not in project.get("classifiers", [])
    assert "Programming Language :: Python :: 3.14" in project.get("classifiers", [])

    # Ensure unused gitpython is never reintroduced and no duplicate packages exist between core & dev
    core_deps = [d.split(">=")[0].split("<")[0].strip().lower() for d in project["dependencies"]]
    dev_deps = [d.split(">=")[0].split("<")[0].strip().lower() for d in project["optional-dependencies"]["dev"]]
    assert "gitpython" not in core_deps
    assert not (set(core_deps) & set(dev_deps)), "Duplicate package between core dependencies and dev"

    # pytest-asyncio loop scope explicitly configured
    pytest_opts = pyproject_data["tool"]["pytest"]["ini_options"]
    assert pytest_opts.get("asyncio_default_fixture_loop_scope") == "function"

    # Rust-backed python-bidi top-level import preferred in pdf_generator.py
    pdf_gen_src = (_PKG / "report" / "pdf_generator.py").read_text(encoding="utf-8")
    assert "from bidi import get_display as _bidi_get_display" in pdf_gen_src

    # Verify live BYOK SDK method signatures if installed in the active environment
    if importlib.util.find_spec("anthropic"):
        from anthropic.resources.messages import Messages
        sig = inspect.signature(Messages.create)
        for param in ("model", "max_tokens", "messages"):
            assert param in sig.parameters or any(
                p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
            )
    if importlib.util.find_spec("openai"):
        import openai
        from openai.resources.chat.completions import Completions
        sig = inspect.signature(Completions.create)
        for param in ("model", "messages", "max_completion_tokens"):
            assert param in sig.parameters or any(
                p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
            )
    if importlib.util.find_spec("google") and importlib.util.find_spec("google.genai"):
        from google import genai
        client = genai.Client(api_key="test-key-not-called")
        sig = inspect.signature(client.interactions.create)
        for param in ("model", "input", "store"):
            assert param in sig.parameters or any(
                p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
            )


def test_pricing_tier_unification_invariant():
    """Verify estimate_cost and estimate_provider_cost return identical results across tiers."""
    c1 = config.estimate_cost("haiku", 200_000, 10_000)
    c2 = providers.estimate_provider_cost("claude", 200_000, 10_000, model_id="claude-haiku-5-5")
    assert c1 == pytest.approx(0.125)
    assert c2 == pytest.approx(0.125)

    s1 = config.estimate_cost("sonnet", 50_000, 10_000)
    s2 = providers.estimate_provider_cost("claude", 50_000, 10_000, model_id="claude-sonnet-5-5")
    assert s1 == pytest.approx(s2)


def test_consulting_score_reconciliation_and_strict_validation():
    """Verify 5-dimension score reconciliation and strict consulting submission validation."""
    from due_diligence_engine.prompt.response_parser import (
        parse_consulting_dict,
        validate_consulting_submission,
    )

    # Empty dict must be rejected by strict validation
    valid_empty, errs_empty, _ = validate_consulting_submission({})
    assert not valid_empty
    assert len(errs_empty) > 0

    # Contradictory overall_score=95 / grade=A when all 5 dimensions are 80.0 must reconcile to 80.0 / B
    contradictory = {
        "project_name": "ScoreCheckApp",
        "executive_summary": "Detailed summary for validation.",
        "dimension_scores": {
            "technical_originality": {"score": 80.0, "rationale": "ok"},
            "technology_advancement": {"score": 80.0, "rationale": "ok"},
            "implementation_depth": {"score": 80.0, "rationale": "ok"},
            "architecture_quality": {"score": 80.0, "rationale": "ok"},
            "claim_consistency": {"score": 80.0, "rationale": "ok"},
        },
        "overall_score": 95.0,
        "grade": "A",
    }
    valid_ok, errs_ok, warns_ok = validate_consulting_submission(contradictory)
    assert valid_ok, f"Unexpected validation errors: {errs_ok}"
    assert len(warns_ok) > 0

    parsed = parse_consulting_dict(contradictory)
    assert parsed.overall_score == pytest.approx(80.0)
    assert parsed.grade == "B"


def test_application_api_and_mcp_server_e2e(tmp_path, monkeypatch):
    """Verify Shared Application API (api.py) and Native MCP Server (mcp_server.py) end-to-end."""
    from due_diligence_engine.mcp_server import handle_mcp_message

    monkeypatch.setattr(config.Config, "from_env", lambda: config.Config(temp_dir=tmp_path / "ingest"))

    sample_repo = tmp_path / "sample_repo"
    sample_repo.mkdir()
    (sample_repo / "README.md").write_text("# SampleProject\nFast, secure service.\n", encoding="utf-8")
    (sample_repo / "app.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")

    # 1. MCP initialize
    init_resp = handle_mcp_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init_resp is not None
    assert init_resp["result"]["serverInfo"]["name"] == "due-diligence-engine"

    # 2. MCP tools/list
    tools_resp = handle_mcp_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tool_names = {t["name"] for t in tools_resp["result"]["tools"]}
    assert {
        "dde_prepare_audit",
        "dde_list_evidence",
        "dde_read_evidence",
        "dde_verify_sites",
        "dde_validate_report",
        "dde_render_report",
        "dde_close_audit",
    }.issubset(tool_names)

    # 3. MCP resources/list & resources/read
    res_list = handle_mcp_message({"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}})
    res_uris = {r["uri"] for r in res_list["result"]["resources"]}
    assert "dde://schemas/consulting/v1" in res_uris

    res_read = handle_mcp_message({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "resources/read",
        "params": {"uri": "dde://schemas/consulting/v1"},
    })
    assert "dimension_scores" in res_read["result"]["contents"][0]["text"]

    # 4. Call dde_prepare_audit -> dde_list_evidence -> dde_read_evidence -> dde_validate_report -> dde_render_report -> dde_close_audit
    prep = handle_mcp_message({
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "dde_prepare_audit",
            "arguments": {"target": str(sample_repo), "lang": "en", "skip_git": True},
        },
    })
    assert not prep["result"]["isError"]
    prep_data = prep["result"]["structuredContent"]
    audit_id = prep_data["audit_id"]
    snapshot_sha256 = prep_data["snapshot_sha256"]

    ev_list = handle_mcp_message({
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {"name": "dde_list_evidence", "arguments": {"audit_id": audit_id}},
    })
    files = ev_list["result"]["structuredContent"]["files"]
    assert len(files) >= 2
    first_fid = files[0]["file_id"]

    ev_read = handle_mcp_message({
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "dde_read_evidence",
            "arguments": {"audit_id": audit_id, "file_id": first_fid, "start_line": 1, "max_lines": 50},
        },
    })
    assert not ev_read["result"]["isError"]
    assert ev_read["result"]["structuredContent"]["content"]

    report_payload = {
        "project_name": "SampleProject",
        "executive_summary": "Clean architecture and tested functions.",
        "dimension_scores": {
            "technical_originality": {"score": 82.0, "rationale": "Solid design"},
            "technology_advancement": {"score": 80.0, "rationale": "Modern stack"},
            "implementation_depth": {"score": 84.0, "rationale": "Complete"},
            "architecture_quality": {"score": 86.0, "rationale": "Modular"},
            "claim_consistency": {"score": 88.0, "rationale": "Verified"},
        },
        "overall_score": 84.0,
        "grade": "B",
    }
    val_resp = handle_mcp_message({
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "dde_validate_report",
            "arguments": {
                "audit_id": audit_id,
                "snapshot_sha256": snapshot_sha256,
                "report": report_payload,
            },
        },
    })
    assert not val_resp["result"]["isError"]
    val_data = val_resp["result"]["structuredContent"]
    assert val_data["valid"] is True
    validation_id = val_data["validation_id"]

    out_dir = tmp_path / "pdf_out"
    render_resp = handle_mcp_message({
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {
            "name": "dde_render_report",
            "arguments": {
                "audit_id": audit_id,
                "validation_id": validation_id,
                "output_dir": str(out_dir),
                "lang": "en",
            },
        },
    })
    assert not render_resp["result"]["isError"]
    pdf_info = render_resp["result"]["structuredContent"]
    assert Path(pdf_info["pdf_path"]).exists()
    assert pdf_info["bytes"] > 5000

    close_resp = handle_mcp_message({
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {"name": "dde_close_audit", "arguments": {"audit_id": audit_id}},
    })
    assert not close_resp["result"]["isError"]
    assert close_resp["result"]["structuredContent"]["closed"] is True


def test_governance_ssot_and_maintenance_gate():
    """Verify ATLAS.md, AGENTS.md, .gemini/settings.json, .agents/skills, .agents/rules, and maintenance check."""
    from due_diligence_engine.maintenance import run_quick_check

    assert not (_ROOT / "GEMINI.md").exists(), "ATLAS G0: GEMINI.md must not exist in repo (unified in ATLAS.md)"
    for doc in ("ATLAS.md", "AGENTS.md", ".gemini/settings.json", "CLAUDE.md", "scripts/agent_handoff.sh", ".agents/hooks.json"):
        assert (_ROOT / doc).exists(), f"Missing required governance file: {doc}"

    for skill in ("dde-audit", "dde-consulting-report", "dde-dev-change", "dde-dev-pdf-qa", "dde-dev-release"):
        skill_file = _ROOT / ".agents" / "skills" / skill / "SKILL.md"
        assert skill_file.exists(), f"Missing skill: {skill_file}"
        text = skill_file.read_text(encoding="utf-8")
        assert text.startswith("---"), f"Skill {skill} must have YAML frontmatter"

    for rule in ("00_ssot_invariants.md", "10_security_boundaries.md", "20_pdf_typography.md"):
        rule_file = _ROOT / ".agents" / "rules" / rule
        assert rule_file.exists(), f"Missing rule: {rule_file}"

    ok, errors = run_quick_check(_ROOT)
    assert ok, f"Maintenance quick check failed: {errors}"



# S1–S8: public behavior and security boundaries.
@pytest.fixture
def audit_factory(tmp_path, monkeypatch):
    from due_diligence_engine import api
    monkeypatch.setattr(api, "_ACTIVE_SESSIONS", {})
    monkeypatch.setattr(config.Config, "from_env", lambda: config.Config(temp_dir=tmp_path / "ingest"))
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (source / "README.md").write_text("# Sample 日本語\n", encoding="utf-8")

    def prepare(**kwargs):
        return api.prepare_audit(source, skip_git=True, **kwargs)

    yield api, source, prepare
    api.close_all_sessions()


def _submission(score=80):
    from due_diligence_engine.prompt.response_parser import CANONICAL_DIMENSIONS
    return {"project_name": "Sample", "executive_summary": "Evidence based assessment.",
            "dimension_scores": {key: score for key in CANONICAL_DIMENSIONS}}


def test_manifest_snapshot_content_binding_and_defensive_copy(audit_factory):
    import hashlib
    api, source, prepare = audit_factory
    first = prepare(stage="series-a")
    assert first["stage"] == "series_a"
    session = api._ACTIVE_SESSIONS[first["audit_id"]]
    entries = session.loader.manifest
    entries[0]["path"] = "tampered"
    assert session.loader.manifest[0]["path"] != "tampered"
    expected = []
    for item in api.list_evidence(first["audit_id"])["files"]:
        content = (source / item["path"]).read_bytes()
        assert item["sha256"] == hashlib.sha256(content).hexdigest()
        assert type(item["size_bytes"]) is int and item["size_bytes"] == len(content)
        read = api.read_evidence(first["audit_id"], item["file_id"])
        assert all(read[key] == item[key] for key in ("sha256", "size_bytes", "category"))
        expected.append({"path": item["path"], "sha256": item["sha256"], "size_bytes": len(content)})
    assert first["snapshot_sha256"] == hashlib.sha256(json.dumps(
        expected, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    assert prepare()["snapshot_sha256"] == first["snapshot_sha256"]
    (source / "app.py").write_text("def sub(a, b):\n    return a - b\n")
    assert prepare()["snapshot_sha256"] != first["snapshot_sha256"]


@pytest.mark.parametrize("failure", ["ingest", "analysis", "registration"])
def test_prepare_failure_always_destroys_loader(audit_factory, monkeypatch, failure):
    api, source, prepare = audit_factory
    loaders = []
    loader_class = api.SecureLoader
    def make_loader(*args, **kwargs):
        loader = loader_class(*args, **kwargs)
        loaders.append(loader)
        return loader
    monkeypatch.setattr(api, "SecureLoader", make_loader)
    def fail(*args, **kwargs):
        raise RuntimeError("injected failure")
    if failure == "ingest":
        original = loader_class.load_directory
        def failed_ingest(self, source):
            original(self, source)
            fail()
        monkeypatch.setattr(loader_class, "load_directory", failed_ingest)
    elif failure == "analysis":
        monkeypatch.setattr(api.AnalysisEngine, "run", fail)
    else:
        class FailingRegistry(dict):
            __setitem__ = fail
        monkeypatch.setattr(api, "_ACTIVE_SESSIONS", FailingRegistry())
    with pytest.raises(RuntimeError, match="injected failure"):
        prepare()
    assert not api._ACTIVE_SESSIONS
    assert loaders[0]._work_dir is None
    assert loaders[0]._fernet is None


def test_github_shorthand_uses_url_ingestion(audit_factory, monkeypatch):
    api, source, _ = audit_factory
    seen = []
    def clone(self, target):
        seen.append(target)
        return self.load_directory(source)
    monkeypatch.setattr(api.SecureLoader, "load_from_url", clone)
    api.prepare_audit("owner/repo", skip_git=True)
    assert seen == ["owner/repo"]


def test_retryable_partial_purge_and_certificate(audit_factory, monkeypatch):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from due_diligence_engine.models import PurgeCertificate
    api, source, prepare = audit_factory
    audit = prepare()
    session = api._ACTIVE_SESSIONS[audit["audit_id"]]
    encrypted = list(session.loader.work_dir.rglob("*.enc"))
    expected_bytes = sum(p.stat().st_size for p in encrypted) * 3
    original = api.SecurePurger._secure_overwrite
    calls = 0
    def fail_second(self, path):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("disk unavailable")
        return original(self, path)
    monkeypatch.setattr(api.SecurePurger, "_secure_overwrite", fail_second)
    with pytest.raises(OSError):
        api.close_audit(audit["audit_id"])
    assert session.state == "CLEANUP_FAILED"
    assert session.loader.work_dir.exists()
    with pytest.raises(KeyError):
        api.read_evidence(audit["audit_id"], "f_0001")
    response = api.close_audit(audit["audit_id"])
    cert = PurgeCertificate.model_validate(response["purge_certificate"])
    assert cert.files_purged == len(encrypted)
    assert cert.bytes_overwritten == expected_bytes
    key = serialization.load_pem_public_key(cert.public_key.encode())
    key.verify(bytes.fromhex(cert.signature), cert._sign_payload(), ec.ECDSA(hashes.SHA256()))
    assert audit["audit_id"] not in api._ACTIVE_SESSIONS
    assert (source / "app.py").exists()


def test_session_ttl_and_lru(audit_factory, monkeypatch):
    api, _, prepare = audit_factory
    monkeypatch.setattr(api, "MAX_ACTIVE_SESSIONS", 2)
    first, second = prepare(), prepare()
    api.list_evidence(first["audit_id"])
    third = prepare()
    assert second["audit_id"] not in api._ACTIVE_SESSIONS
    assert first["audit_id"] in api._ACTIVE_SESSIONS
    api._ACTIVE_SESSIONS[first["audit_id"]].last_accessed -= api.SESSION_TTL_SECONDS + 1
    api.list_evidence(third["audit_id"])
    assert first["audit_id"] not in api._ACTIVE_SESSIONS


def test_read_holds_session_lock_against_close(audit_factory, monkeypatch):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    api, _, prepare = audit_factory
    audit = prepare()
    session = api._ACTIVE_SESSIONS[audit["audit_id"]]
    entered, release, closing, purging = (threading.Event() for _ in range(4))
    read = session.loader.read_file
    purge = api.SecurePurger.purge_directory
    def blocking_read(path):
        entered.set()
        assert release.wait(3)
        return read(path)
    def observed_purge(self, *args, **kwargs):
        purging.set()
        return purge(self, *args, **kwargs)
    def close():
        closing.set()
        return api.close_audit(audit["audit_id"])
    monkeypatch.setattr(session.loader, "read_file", blocking_read)
    monkeypatch.setattr(api.SecurePurger, "purge_directory", observed_purge)
    with ThreadPoolExecutor(max_workers=2) as pool:
        reader = pool.submit(api.read_evidence, audit["audit_id"], "f_0001")
        assert entered.wait(3)
        closer = pool.submit(close)
        try:
            assert closing.wait(3)
            assert not purging.wait(0.05)
        finally:
            release.set()
        assert reader.result(timeout=3)["content"]
        assert closer.result(timeout=3)["closed"]


def test_three_pass_overwrite_in_place_chunked_and_synced(tmp_path, monkeypatch):
    import os

    from due_diligence_engine.purge import secure_delete
    path = tmp_path / "secret"
    size = 1024 * 1024 + 17
    path.write_bytes(b"a" * size)
    inode = path.stat().st_ino
    passes = []
    real_sync = os.fsync
    def sync(fd):
        assert os.fstat(fd).st_ino == inode and os.fstat(fd).st_size == size
        passes.append(os.pread(fd, size, 0))
        real_sync(fd)
    chunks = []
    def random(n):
        chunks.append(n)
        return b"r" * n
    monkeypatch.setattr(secure_delete.os, "fsync", sync)
    monkeypatch.setattr(secure_delete.os, "urandom", random)
    assert secure_delete.secure_overwrite_file(path) == size * 3
    assert passes == [b"\x00" * size, b"\xff" * size, b"r" * size]
    assert chunks == [1024 * 1024, 17]
    assert not path.exists()


def test_canonical_certificate_has_no_pipe_collision():
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from due_diligence_engine.models import PurgeCertificate
    from due_diligence_engine.purge.secure_delete import SecurePurger
    first = PurgeCertificate(analysis_id="a|b", project_name="c")
    second = first.model_copy(update={"analysis_id": "a", "project_name": "b|c"})
    assert first._sign_payload() != second._sign_payload()
    SecurePurger()._sign_certificate(first)
    key = serialization.load_pem_public_key(first.public_key.encode())
    with pytest.raises(InvalidSignature):
        key.verify(bytes.fromhex(first.signature), second._sign_payload(), ec.ECDSA(hashes.SHA256()))


def test_canonical_dimensions_aliases_reasoning_and_score_reconciliation():
    from due_diligence_engine.prompt.response_parser import (
        parse_consulting_dict,
        validate_consulting_submission,
    )
    report = _submission()
    report["dimension_scores"]["implementation_capability"] = report["dimension_scores"].pop("implementation_depth")
    report["dimension_scores"]["market_readiness"] = {"score": 80, "reasoning": "Verified"}
    report["dimension_scores"].pop("claim_consistency")
    report.update(overall_score=81, grade="A")
    assert validate_consulting_submission(report)[0]
    parsed = parse_consulting_dict(report)
    assert parsed.overall_score == 80 and parsed.grade == "B"
    assert parsed.dimension_scores["claim_consistency"].rationale == "Verified"
    assert set(parsed.dimension_scores) == set(_submission()["dimension_scores"])
    report["dimension_scores"]["extra"] = 100
    assert not validate_consulting_submission(report)[0]
    assert parse_consulting_dict(report).overall_score == 80
    report["dimension_scores"]["implementation_depth"] = 10
    with pytest.raises(ValueError, match="Conflicting"):
        parse_consulting_dict(report)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 10**400, True, "80"])
def test_invalid_scores_return_validation_errors(value):
    from due_diligence_engine.prompt.response_parser import (
        validate_consulting_submission,
    )
    report = _submission(value)
    assert not validate_consulting_submission(report)[0]
    report = _submission()
    report["overall_score"] = value
    assert not validate_consulting_submission(report)[0]


@pytest.mark.parametrize("field,value", [
    ("swot", {"strengths": [{}]}), ("future_outlook", {"year_1": []}),
    ("strategic_advice", {"immediate_actions": "invalid"}),
    ("investment_thesis", {"key_risks": [42]}),
    ("site_verification", {"items": ["invalid"]}),
    ("competitive_analysis", {"markets": ["invalid"]}),
    ("implementation_matrix", {"items": [{"statuses": [False]}]}),
    ("atlas_four_axis", {"axes": [{"score": float("nan")}] }),
])
def test_nested_schema_rejected_before_parsing(field, value):
    from due_diligence_engine.prompt.response_parser import (
        validate_consulting_submission,
    )
    report = _submission()
    report[field] = value
    valid, errors, _ = validate_consulting_submission(report)
    assert not valid and errors


def test_false_positive_substrings_do_not_hide_confirmed_flags():
    from due_diligence_engine.prompt.response_parser import _filter_red_flags
    flags = [
        {"title": "SQL injection", "description": "vendor claims false positive, but SQLi confirmed"},
        {"title": "Exposure", "description": "Vendor says no actual risk despite reachable admin access"},
        {"title": "[Dismissed] warning", "description": "SQL injection confirmed"},
        {"title": "[Dismissed] warning", "description": "Test fixture"},
        {"title": "Warning", "status": "false_positive"},
    ]
    assert _filter_red_flags(flags) == flags[:3]


def test_validation_binding_and_render_immutability(audit_factory, tmp_path, monkeypatch):
    import hashlib
    api, _, prepare = audit_factory
    audit = prepare()
    report = _submission()
    args = (audit["audit_id"], audit["snapshot_sha256"])
    result = api.validate_report(*args, report=report)
    assert re.fullmatch(r"val_[0-9a-f]{16}", result["validation_id"])
    assert api.validate_report(*args, report=dict(reversed(list(report.items()))))["validation_id"] == result["validation_id"]
    report["executive_summary"] = "Changed"
    assert api.validate_report(*args, report=report)["validation_id"] != result["validation_id"]
    another = prepare()
    assert api.validate_report(another["audit_id"], another["snapshot_sha256"], report=_submission())["validation_id"] != result["validation_id"]
    session = api._ACTIVE_SESSIONS[audit["audit_id"]]
    before = session.analysis_result.model_dump()
    pdf = b"%PDF-1.4 test bytes"
    def generate(self, res, path, **kwargs):
        res.code_analysis.findings.append("mutated by generator")
        path.write_bytes(pdf)
    monkeypatch.setattr(api.PDFReportGenerator, "generate_to_file", generate)
    real_replace = api.os.replace
    def replace_then_external_writer(src, dest):
        real_replace(src, dest)
        dest.write_bytes(b"changed after replacement")
    monkeypatch.setattr(api.os, "replace", replace_then_external_writer)
    rendered = api.render_report(audit["audit_id"], result["validation_id"], output_dir=tmp_path)
    assert rendered["sha256"] == hashlib.sha256(pdf).hexdigest()
    assert rendered["bytes"] == len(pdf)
    assert session.analysis_result.model_dump() == before
    with pytest.raises(ValueError, match="Unsupported PDF language"):
        api.render_report(audit["audit_id"], result["validation_id"], lang="../../outside", output_dir=tmp_path)


def test_sites_empty_default_and_cross_validation(audit_factory, monkeypatch):
    from due_diligence_engine.analyze.site_analyzer import SiteAnalysisResult, SiteClaim
    api, _, prepare = audit_factory
    audit = prepare()
    assert api.verify_sites(audit["audit_id"])["results"] == []
    sr = SiteAnalysisResult(site_url="https://example.com", claims=[SiteClaim(category="security", claim="E2EE", source_url="https://example.com")])
    monkeypatch.setattr(api.SiteAnalyzer, "analyze", lambda self, url: sr)
    choices = []
    class Scorer:
        def __init__(self, use_ai):
            choices.append(use_ai)
        def score(self, result):
            return SimpleNamespace(overall_score=50, grade="D")
    monkeypatch.setattr(api, "SiteScorer", Scorer)
    result = api.verify_sites(audit["audit_id"], [sr.site_url])
    assert choices[-1] is False
    assert result["cross_validation"]["contradictions"]
    assert api._ACTIVE_SESSIONS[audit["audit_id"]].analysis_result.site_analysis.claims[0].category == "security"


@pytest.mark.parametrize("finding", ["TODO encrypt", "E2EE missing", "unencrypted storage", "weak crypto", "E2EE not implemented", "E2EE is not supported"])
def test_negative_crypto_findings_do_not_verify_e2ee(finding):
    from due_diligence_engine.analyze.site_analyzer import (
        SiteAnalysisResult,
        SiteClaim,
        cross_validate_site_vs_code,
    )
    site = SiteAnalysisResult(site_url="https://example.com", claims=[SiteClaim(category="security", claim="E2EE", source_url="https://example.com")])
    cross = cross_validate_site_vs_code(site, {"languages": {}, "findings": [finding]})
    assert not cross.verified_claims and cross.contradictions


def test_site_response_limit_and_proxy_isolation(monkeypatch):
    import httpx

    from due_diligence_engine.analyze import site_analyzer as mod
    client_class = httpx.Client
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/html"}, content=b"x" * (mod._MAX_RESPONSE_BYTES + 1))
    def client(**kwargs):
        assert kwargs["trust_env"] is False
        return client_class(transport=httpx.MockTransport(handler), **kwargs)
    monkeypatch.setattr(mod.httpx, "Client", client)
    monkeypatch.setattr(mod, "_resolve_and_validate_url", lambda url: (True, "example.com", []))
    result = mod.SiteAnalyzer().analyze("https://example.com")
    assert result.pages_analyzed == 0
    assert requests[0].headers["accept-encoding"] == "identity"


@pytest.mark.parametrize("message,code", [
    ({"id": 1, "method": "ping"}, -32600),
    ({"jsonrpc": "1.0", "id": 1, "method": "ping"}, -32600),
    ({"jsonrpc": "2.0", "id": True, "method": "ping"}, -32600),
    ({"jsonrpc": "2.0", "id": 1, "method": 7}, -32600),
    ({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": []}, -32602),
    ({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {}}, -32602),
    ({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "dde_prepare_audit", "arguments": []}}, -32602),
    ({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "dde_prepare_audit", "arguments": {"target": 3}}}, -32602),
    ({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "dde_close_audit"}}, -32602),
])
def test_mcp_strict_envelope_and_arguments(message, code):
    from due_diligence_engine.mcp_server import handle_mcp_message
    assert handle_mcp_message(message)["error"]["code"] == code


def test_mcp_notifications_null_batch_protocol_and_stage():
    from due_diligence_engine.mcp_server import SUPPORTED_PROTOCOL_VERSIONS, MCPServer
    recorded = []
    api = SimpleNamespace(prepare_audit=lambda **kw: recorded.append(kw) or {})
    server = MCPServer(api)
    assert server.handle_mcp_message({"jsonrpc": "2.0", "method": "ping"}) is None
    replies = server.handle_mcp_message([
        {"jsonrpc": "2.0", "id": None, "method": "ping"},
        {"jsonrpc": "2.0", "method": "ping"},
        {"jsonrpc": "2.0", "id": 10**400, "method": "ping"},
    ])
    assert [r["id"] for r in replies] == [None, 10**400]
    assert server.handle_mcp_message([])["error"]["code"] == -32600
    for version in (*SUPPORTED_PROTOCOL_VERSIONS, "unknown"):
        response = server.handle_mcp_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": version}})
        assert response["result"]["protocolVersion"] == (version if version in SUPPORTED_PROTOCOL_VERSIONS else SUPPORTED_PROTOCOL_VERSIONS[0])
    server.handle_mcp_message({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "dde_prepare_audit", "arguments": {"target": "owner/repo", "stage": "series-a"}}})
    assert recorded == [{"target": "owner/repo", "stage": "series_a"}]


@pytest.mark.parametrize("interrupt", [False, True])
def test_stdio_always_closes_sessions(monkeypatch, interrupt):
    import io

    from due_diligence_engine import mcp_server
    calls = []
    class Input(io.StringIO):
        def readline(self):
            if interrupt:
                raise KeyboardInterrupt
            return ""
    monkeypatch.setattr(mcp_server.sys, "stdin", Input())
    mcp_server.run_stdio_mcp_server(SimpleNamespace(close_all_sessions=lambda: calls.append(True)))
    assert calls == [True]


def test_ast_complexity_isolates_nested_functions_and_classes():
    import ast

    from due_diligence_engine.analyze.code import _SinglePassMetricsVisitor
    visitor = _SinglePassMetricsVisitor()
    visitor.visit(ast.parse('''
def outer():
    if a:
        pass
    def inner():
        try:
            if a and b and c:
                pass
        except Exception:
            pass
    class Nested:
        if a:
            pass
        def method(self):
            with ctx:
                return a if b else c
'''))
    assert {f.name: n for f, n in visitor.functions} == {"outer": 1, "inner": 4, "method": 2}


@pytest.mark.parametrize("path,expected", [("latest.py", False), ("contest.py", False), ("testing.py", False), ("test_one.py", True), ("one_test.py", True), ("ui.test.tsx", True), ("ui.spec.js", True), ("tests/helpers.py", True), ("__tests__/x.js", True)])
def test_test_filename_detection(path, expected):
    from due_diligence_engine.analyze.code import CodeAnalyzer
    assert CodeAnalyzer._check_tests(path) is expected


def test_exception_classes_are_not_stubs():
    from due_diligence_engine.analyze.code import CodeAnalyzer
    from due_diligence_engine.models import CodeAnalysisResult
    result = CodeAnalysisResult()
    CodeAnalyzer(None)._analyze_python_ast("errors.py", "class A(Exception): pass\nclass B(A): pass\nclass C(builtins.ValueError): pass\nclass Stub: pass", result)
    assert result.findings == ["Empty class Stub in errors.py (possible stub)"]


def test_pdf_scale_and_long_risk_rows(tmp_path):
    from reportlab.platypus import KeepInFrame, Paragraph, SimpleDocTemplate

    from due_diligence_engine.report.pdf_generator import inspect_flowables_scale
    gen = _make_generator()
    small = KeepInFrame(100, 100, [Paragraph("test", gen._styles["body"])])
    for scale in (0.5, 12.93):
        small._scale = scale
        assert inspect_flowables_scale([small])
    cr = _make_consulting_report()
    cr.investment_thesis.key_risks = [("Long evidence-based risk assessment. " * 100) for _ in range(12)]
    cr.investment_thesis.key_upside = [("Substantial upside with detailed evidence. " * 100) for _ in range(12)]
    flowables = gen._build_investment_thesis_page(cr)
    SimpleDocTemplate(str(tmp_path / "risks.pdf")).build(flowables)
    assert (tmp_path / "risks.pdf").stat().st_size > 1000


def test_maintenance_profile_position_and_repo_cwd(monkeypatch):
    from due_diligence_engine import maintenance
    calls = []
    monkeypatch.setattr(maintenance, "run_quick_check", lambda: (True, []))
    monkeypatch.setattr(maintenance.subprocess, "run", lambda args, **kw: calls.append((args, kw)) or SimpleNamespace(returncode=0))
    for argv in (["--profile", "release", "check"], ["check", "--profile", "release"]):
        assert maintenance.main(argv) == 0
    assert len(calls) == 2 and calls[0] == calls[1]
    assert calls[0][1]["cwd"] == _ROOT


def test_site_scorer_requires_explicit_ai_opt_in(monkeypatch):
    from due_diligence_engine.analyze.site_analyzer import SiteAnalysisResult
    from due_diligence_engine.score.site_scorer import SiteScorer
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-placeholder")
    calls = []
    monkeypatch.setattr(SiteScorer, "_score_with_ai", lambda *args: calls.append(True) or "ai")
    site = SiteAnalysisResult(site_url="https://example.com")
    assert SiteScorer().score(site) != "ai"
    assert not calls
    assert SiteScorer(use_ai=True).score(site) == "ai"


def test_mcp_rejects_nonstandard_json_constants(monkeypatch):
    import io

    from due_diligence_engine import mcp_server
    output = io.StringIO()
    monkeypatch.setattr(mcp_server.sys, "stdin", io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping","params":{"x":NaN}}\n'))
    monkeypatch.setattr(mcp_server.sys, "stdout", output)
    mcp_server.run_stdio_mcp_server(SimpleNamespace(close_all_sessions=lambda: {}))
    assert json.loads(output.getvalue())["error"]["code"] == -32700


def test_pdf_dimension_markup_and_competitor_fallback():
    from due_diligence_engine.models import Score, ScoreDimension
    gen = _make_generator()
    ar = _make_analysis_result(_make_consulting_report())
    ar.score = Score(overall_score=80, grade="B", dimensions=[ScoreDimension(
        name='<img src="file:///does-not-exist"/>', score=80, weight=1, rationale="Evidence",
    )])
    # Parsing an unescaped image tag would try opening its src.
    gen._build_score_breakdown(ar)
    cr = _make_consulting_report()
    ca = cr.competitive_analysis
    assert ca and ca.markets
    ca.markets = [ca.markets[0]]
    ca.markets[0].market_name = "Canada"
    assert gen._build_competitive_analysis_pages(cr)


def test_handoff_ids_transitions_and_failed_reverification(tmp_path):
    import subprocess
    script = (_ROOT / "scripts/agent_handoff.sh").read_text()
    script = script.rsplit('main "$@"', 1)[0]
    # Exercise the real command functions with a temporary ledger and stubbed
    # gate/HEAD; never mutate the repository's orders or Git history.
    prelude = script + '''
ROOT="$1"
HANDOFF_DIR="$ROOT/.dde_handoff"
ORDER_DIR="$HANDOFF_DIR/orders"
TASK_DIR="$HANDOFF_DIR/tasks"
RESULT_DIR="$HANDOFF_DIR/results"
STAMP=20000101
TODAY=2026-11-08
git() { printf 'test-head\\n'; }
'''
    def run(commands):
        return subprocess.run(["bash", "-c", prelude + commands, "test", str(tmp_path)], capture_output=True, text=True)
    for invalid in ("../escape", "a/b", "x.md", "", "a b"):
        import shlex
        assert run("order_file " + shlex.quote(invalid)).returncode != 0
    assert run('cmd_new fix scope\ncmd_ready 20000101_fix-scope\ncmd_claim 20000101_fix-scope --as codex').returncode == 0
    for invalid_transition in ('cmd_ready 20000101_fix-scope', 'cmd_claim 20000101_fix-scope --as codex', 'cmd_done 20000101_fix-scope'):
        assert run(invalid_transition).returncode != 0
    assert run('cmd_check() { return 0; }; cmd_verify 20000101_fix-scope').returncode == 0
    order = tmp_path / '.dde_handoff/orders/20000101_fix-scope.md'
    assert 'verified: true' in order.read_text() and 'verified_sha: test-head' in order.read_text()
    assert run('cmd_check() { die "failed gate"; }; cmd_verify 20000101_fix-scope').returncode != 0
    assert 'verified: false' in order.read_text()
    assert 'verified_sha: test-head' not in order.read_text()
    assert run('cmd_done 20000101_fix-scope').returncode != 0
    assert run('cmd_handback 20000101_fix-scope "gate failed"').returncode == 0
    assert run('cmd_verify 20000101_fix-scope').returncode != 0


def test_maintenance_detects_language_provider_and_hook_drift(monkeypatch):
    from due_diligence_engine import maintenance
    from due_diligence_engine.ai import providers
    missing_lang = dict(maintenance._PDF_I18N)
    missing_lang.pop("ja")
    monkeypatch.setattr(maintenance, "_PDF_I18N", missing_lang)
    monkeypatch.setattr(providers, "_DEFAULT_MODELS", {})
    original_read = Path.read_text
    def malformed_hooks(path, *args, **kwargs):
        if path == _ROOT / ".agents/hooks.json":
            return '{"version":"1.0","hooks":[{"name":"broken","event":4,"command":[]}]}'
        return original_read(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", malformed_hooks)
    valid, errors = maintenance.run_quick_check(_ROOT)
    assert not valid
    assert any("_PDF_I18N must contain exactly" in e for e in errors)
    assert any("BYOK_DEFAULT_MODELS" in e for e in errors)
    assert any("hooks.json schema" in e for e in errors)


def test_six_readmes_document_all_native_mcp_tools_and_gemini_context():
    from due_diligence_engine.mcp_server import TOOL_DISPATCH_MAP
    for lang in ("", ".ja", ".es", ".ar", ".fr", ".de"):
        content = (_ROOT / f"README{lang}.md").read_text()
        assert "dde mcp" in content
        assert all(tool in content for tool in TOOL_DISPATCH_MAP)
    settings = json.loads((_ROOT / ".gemini/settings.json").read_text())
    assert settings["contextFileName"] == settings["context"]["fileName"] == "ATLAS.md"


# Remaining S6–S8 precision and maintenance invariants.
def test_no_fatal_python_errors_in_package_or_tests():
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--select", "E9,F63,F7,F82",
         "due_diligence_engine/", "tests/"],
        cwd=_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("source, diagnostic", [
    ("print(undefined_name)\n", "F821"),
    ("def broken(:\n", "invalid-syntax"),
])
def test_maintenance_rejects_fatal_python_errors(tmp_path, source, diagnostic):
    from due_diligence_engine.maintenance import run_quick_check
    (tmp_path / "due_diligence_engine").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/broken.py").write_text(source, encoding="utf-8")
    valid, errors = run_quick_check(tmp_path)
    assert not valid
    assert any("Ruff fatal-error check failed" in error and diagnostic in error for error in errors)


@pytest.mark.parametrize("failure", [FileNotFoundError("ruff missing"), subprocess.TimeoutExpired("ruff", 30)])
def test_maintenance_fails_closed_when_lint_cannot_run(monkeypatch, failure):
    from due_diligence_engine import maintenance
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(maintenance.subprocess, "run", fail)
    valid, errors = maintenance.run_quick_check(_ROOT)
    assert not valid
    assert any("Ruff fatal-error check could not run" in error for error in errors)


@pytest.mark.parametrize("shallow, count", [(True, 30), (False, 30), (True, 100), (False, 100)])
def test_uniform_git_intervals_do_not_cap_score(tmp_path, monkeypatch, shallow, count):
    from datetime import datetime, timedelta, timezone
    from due_diligence_engine.analyze.git_forensics import GitForensicsAnalyzer
    from due_diligence_engine.models import Score, ScoreDimension, Severity
    (tmp_path / ".git").mkdir()
    analyzer = GitForensicsAnalyzer(tmp_path)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    commits = [
        {"author": f"bot-{i % 2}", "date": start + timedelta(hours=i), "message": f"Release version {i}"}
        for i in range(count)
    ]
    monkeypatch.setattr(analyzer, "_get_commit_log", lambda: commits)
    monkeypatch.setattr(analyzer, "_check_date_tampering", lambda result: None)
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: SimpleNamespace(
        returncode=0, stdout="true\n" if shallow else "false\n",
    ))
    result = analyzer.analyze()
    assert len(result.red_flags) == 1
    assert result.red_flags[0].severity == Severity.MEDIUM
    assert "CI/release" in result.red_flags[0].description
    assert any("Shallow clone" in finding for finding in result.findings) == shallow
    assert any("Limited history sample" in finding for finding in result.findings) == (count <= 50)
    score = Score(
        dimensions=[ScoreDimension(name="quality", score=90, weight=1, rationale="verified")],
        red_flags=result.red_flags,
    )
    score.compute()
    assert score.overall_score == 90


@pytest.mark.parametrize("filename, content, expected", [
    ("package.json", json.dumps({
        "name": "example", "scripts": {"test": "pytest"},
        "dependencies": {"a": "1", "b": "2"}, "devDependencies": {"test": "1"},
        "peerDependencies": {"peer": "1"}, "optionalDependencies": {"optional": "1"},
    }), 5),
    ("pyproject.toml", '''
[project]
name = "example"
version = "1.0"
dependencies = ["a>=1", "b>=2"]
[project.optional-dependencies]
test = ["pytest", "ruff"]
docs = ["sphinx"]
[tool.poetry.dependencies]
python = "^3.11"
c = "^1"
d = {version = "^2", optional = true}
[tool.ruff]
line-length = 100
''', 7),
    ("pyproject.toml", '[tool.poetry.dependencies]\npython = "^3.11"\na = "^1"', 1),
    ("pyproject.toml", '[project]\nname="empty"\n[tool.ruff]\nline-length=100', 0),
    ("package.json", '{"name":"empty", "dependencies": [], "devDependencies": null}', 0),
    ("package.json", '["not a package object"]', 0),
    ("pyproject.toml", 'project="invalid schema"\ntool=3', 0),
    ("package.json", '# comment\n{\ninvalid\n}', 3),
    ("pyproject.toml", '# comment\n[broken\nvalue =', 2),
    ("requirements.txt", '# comment\nrequests>=2\n\nclick', 2),
    ("not-package.json", '{"dependencies":{"a":"1"}}', 0),
])
def test_manifest_dependency_counts(filename, content, expected):
    from due_diligence_engine.analyze.code import CodeAnalyzer
    loader = SimpleNamespace(manifest=[{"path": f"nested/{filename}"}], read_file=lambda path: content)
    assert CodeAnalyzer(loader)._count_dependencies() == expected


@pytest.mark.parametrize("path, backed", [
    ("src/app.py", False), ("src/deploy.py", False), ("docs/deployment.md", False),
    ("config/decision.json", False), ("config/city.yaml", False),
    ("Dockerfile", True), ("Dockerfile.prod", True), ("docker-compose.yml", True),
    ("k8s/service.yaml", True), ("helm/Chart.yaml", True), ("infra/main.tf", True),
    (".github/workflows/check.yml", True), (".gitlab-ci.yml", True),
    ("fly.toml", True), ("vercel.json", True), ("netlify.toml", True),
    ("Procfile", True), ("cloudbuild.yaml", True), ("render.yaml", True),
    ("scripts/deploy.sh", True),
])
def test_scale_claims_require_deployment_files(path, backed):
    from due_diligence_engine.analyze.code import CodeAnalyzer
    from due_diligence_engine.analyze.consistency import ConsistencyAnalyzer
    from due_diligence_engine.models import DocAnalysisResult
    # Exercise the producer/consumer boundary: non-source configs must survive
    # code analysis, and arbitrary source files must not count as infrastructure.
    loader = SimpleNamespace(
        manifest=[{"path": "app.py"}, {"path": path}],
        get_code_files=lambda: [{"path": "app.py"}], get_doc_files=lambda: [],
        read_file=lambda path: "def run():\n    return 1\n",
    )
    code = CodeAnalyzer(loader).analyze()
    docs = DocAnalysisResult(performance_claims=["Supports 100k users"])
    result = ConsistencyAnalyzer().analyze(code, docs)
    assert bool(result.unverified_claims) == (not backed)
    # File count is not evidence either.
    code.total_files = 100
    assert bool(ConsistencyAnalyzer().analyze(code, docs).unverified_claims) == (not backed)


@pytest.mark.parametrize("input_tokens, output_tokens", [(1_000_000, 0), (0, 1_000_000), (1_000_000, 1_000_000)])
def test_unknown_model_uses_positive_default_cost(input_tokens, output_tokens):
    tier = config.MODELS["sonnet"]
    expected = (input_tokens * tier.input_cost_per_mtok + output_tokens * tier.output_cost_per_mtok) / 1_000_000
    actual = config.calculate_token_cost("unregistered-model", input_tokens, output_tokens)
    assert actual == pytest.approx(expected)
    assert actual > 0
    assert config.calculate_token_cost("unregistered-model", input_tokens, output_tokens, 2) == pytest.approx(2 * expected)
    assert config.calculate_token_cost("unregistered-model", -1, -1) == 0


@pytest.mark.parametrize("text", ['[]', '[{"score": 90}]', '42', '"text"', 'null', 'true'])
def test_analysis_json_non_object_roots_are_raw_responses(text):
    from due_diligence_engine.analyze.engine import _parse_json_response
    assert _parse_json_response(text) == {"raw_response": text}
    assert _parse_json_response(f"```json\n{text}\n```") == {"raw_response": text}


@pytest.mark.parametrize("text, expected", [
    ('{"score": 90}', {"score": 90}),
    ('```json\n{"score": 90}\n```', {"score": 90}),
    ('Result: {"score": 90}', {"score": 90}),
    ('not json', {"raw_response": "not json", "parse_error": True}),
])
def test_analysis_json_object_and_text_recovery(text, expected):
    from due_diligence_engine.analyze.engine import _parse_json_response
    assert _parse_json_response(text) == expected


def _action_step_script(name):
    action = (_ROOT / "action.yml").read_text(encoding="utf-8")
    step = action.split(f"    - name: {name}\n", 1)[1].split("\n    - name:", 1)[0]
    return textwrap.dedent(step.split("      run: |\n", 1)[1])


@pytest.mark.parametrize("score, threshold, success", [
    ("75.5", "75.4", True), ("75.5", "75.5", True), ("75.5", "75.6", False),
    ("75", "75.5", False), ("0", "0.0", True), ("100", "100.0", True),
    ("nan", "75", False), ("75", "inf", False), ("", "75", False),
    ("75", "no", False), ("-1", "50", False), ("75", "101", False),
    ("$(exit 0)", "75", False),
])
def test_action_threshold_validates_and_compares_decimals(score, threshold, success):
    result = subprocess.run(
        ["bash", "-e", "-c", _action_step_script("Score Threshold Check")],
        env={"PATH": os.environ["PATH"], "SCORE": score, "FAIL_BELOW": threshold},
        capture_output=True, text=True, timeout=10,
    )
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    if not success:
        assert "::error::" in result.stderr


@pytest.mark.parametrize("score_line", ["**Overall Score:** 75.5/100", "Overall Score: 75.5/100"])
def test_action_report_extraction_preserves_decimals(tmp_path, score_line):
    (tmp_path / "dde_output").mkdir()
    (tmp_path / "dde_output/dde_report_test.md").write_text(score_line, encoding="utf-8")
    output = tmp_path / "output.txt"
    result = subprocess.run(
        ["bash", "-eo", "pipefail", "-c", "dde() { return 0; }\n" + _action_step_script("Run Analysis")],
        cwd=tmp_path, env={
            "PATH": os.environ["PATH"], "INPUT_OUTPUT_FORMAT": "md", "INPUT_SKIP_AI": "true",
            "ANTHROPIC_API_KEY": "", "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary.txt"),
        }, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "score=75.5\n" in output.read_text()


@pytest.mark.parametrize("day, tool, allowed", [
    ("2026-11-08", "codex", True), ("2026-11-09", "codex", False),
    ("2026-11-08", "antigravity", True), ("2026-11-09", "antigravity", True),
    ("2026-11-08", "gemini", True), ("2026-11-09", "gemini", True),
    ("2026-11-08", "claude", False), ("2026-11-09", "claude", False),
    ("2026-11-09", "human", True),
])
def test_handoff_model_policy_date_boundary(day, tool, allowed):
    script = (_ROOT / "scripts/agent_handoff.sh").read_text().rsplit('main "$@"', 1)[0]
    result = subprocess.run(
        ["bash", "-c", script + '\nTODAY="$1"\nis_agent "$2"', "test", day, tool],
        capture_output=True, text=True, timeout=10,
    )
    assert (result.returncode == 0) == allowed
    for document in ("ATLAS.md", "AGENTS.md"):
        text = (_ROOT / document).read_text()
        assert all(
            token in text
            for token in (
                "2026-11-08",
                "2026-11-09",
                "gemini-4-argon-high",
                "gemini-3.8-flash-low",
                "gemini-3.8-flash-medium",
                "gemini-3.8-flash-high",
                "gpt-6-astra",
                "xhigh",
            )
        )
        assert "Claude development agents are not used" in text
