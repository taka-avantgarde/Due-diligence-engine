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


def test_application_api_and_mcp_server_e2e(tmp_path):
    """Verify Shared Application API (api.py) and Native MCP Server (mcp_server.py) end-to-end."""
    from due_diligence_engine.mcp_server import handle_mcp_message

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


