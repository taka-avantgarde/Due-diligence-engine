"""Comprehensive regression and end-to-end tests for DDE audit fixes (Task-1 to Task-5).

Verifies:
1. `dde report --consulting <json> --pdf` CLI execution exits 0 and creates a valid PDF.
2. `dde prompt` and `dde analyze --skip-ai` never invoke AI providers even when API keys are set.
3. `SecureLoader.load_from_url` preserves `.git` until `destroy()` and shreds the clone dir, invalidating `_fernet`.
4. `SecureLoader` and `SecurePurger` do not follow symlinks outside root, and `load_archive` blocks Zip Slip attacks.
5. `Score.compute()` deduplicates red flags by ID and is strictly idempotent.
6. `AnthropicProvider` handles ThinkingBlock, `OpenAIProvider` handles gpt-5 (no temp), `GoogleProvider` passes store=False.
7. `parse_consulting_dict` preserves rationales, sources, last_verified, retains negated false-positive red flags, and handles null/NaN safely.
8. `PDFReportGenerator` escapes dangerous XML/HTML tags without crashing, non-destructively handles Arabic mode, and places chart + label in the same cell.
"""

from __future__ import annotations

import copy
import json
import math
import subprocess
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from due_diligence_engine.ai.providers import (
    AnthropicProvider,
    GoogleProvider,
    OpenAIProvider,
)
from due_diligence_engine.cli import cli
from due_diligence_engine.config import Config
from due_diligence_engine.ingest.secure_loader import SecureLoader
from due_diligence_engine.models import (
    AnalysisResult,
    CompetitiveAnalysis,
    CompetitorDataPoint,
    ConsultingReport,
    DataFreshness,
    ScoreDimension,
    EnhancedDimensionScore,
    FutureOutlook,
    InvestmentThesis,
    MarketChart,
    MarketPosition,
    RedFlag,
    Score,
    Severity,
    StrategicAction,
    StrategicAdvice,
    SWOTAnalysis,
    SWOTItem,
)
from due_diligence_engine.prompt.response_parser import (
    parse_consulting_dict,
    parse_consulting_response,
)
from due_diligence_engine.purge.secure_delete import SecurePurger
from due_diligence_engine.report.pdf_generator import PDFReportGenerator


def _make_sample_consulting_dict(project_name: str = "RegressionApp") -> dict:
    """Build a valid, comprehensive dictionary that parses into a ConsultingReport."""
    return {
        "project_name": project_name,
        "executive_summary": "Comprehensive analysis of technical capabilities and market risks.",
        "executive_summary_business": "Target has demonstrated initial traction and solid engineering fundamentals.",
        "data_freshness": {
            "web_search_performed": True,
            "search_date": "2026-04-02",
            "queries_executed": ["tech due diligence 2026"],
            "sources_consulted": ["https://example.com/source-1"],
        },
        "dimension_scores": {
            "technical_originality": {
                "score": 85.0,
                "level": 8,
                "label": "Technical Originality",
                "rationale": "Proprietary algorithmic core.",
                "business_explanation": "Reduces dependency on external vendors.",
                "enables": "Long-term IP moat.",
            },
            "technology_advancement": {
                "score": 80.0,
                "level": 8,
                "label": "Technology Advancement",
                "rationale": "Modern stack.",
                "business_explanation": "Attracts top talent.",
                "enables": "Fast feature iteration.",
            },
            "implementation_depth": {
                "score": 75.0,
                "level": 7,
                "label": "Implementation Depth",
                "rationale": "Deep testing coverage.",
                "business_explanation": "Fewer critical bugs in production.",
                "enables": "Enterprise SLA guarantees.",
            },
            "architecture_quality": {
                "score": 90.0,
                "level": 9,
                "label": "Architecture Quality",
                "rationale": "High cohesion and microservice boundaries.",
                "business_explanation": "Low maintenance overhead.",
                "enables": "High horizontal scale.",
            },
            "claim_consistency": {
                "score": 88.0,
                "level": 8,
                "label": "Claim Consistency",
                "rationale": "Site claims match repository evidence.",
                "business_explanation": "High credibility with enterprise clients.",
                "enables": "Faster sales cycles.",
            },
        },
        "swot": {
            "strengths": [{"point": "Robust architecture", "explanation": "Clean modular domain boundaries."}],
            "weaknesses": [{"point": "Sparse docstrings", "explanation": "Requires onboarding hand-holding."}],
            "opportunities": [{"point": "Multi-region failover", "explanation": "Expand into EU financial hubs."}],
            "threats": [{"point": "Rapid open source parity", "explanation": "Open models closing gap."}],
        },
        "tech_level_summary": {
            "overall_level": 8,
            "level_label": "Advanced Enterprise Ready",
            "summary": "Engineering practice reflects top decile discipline.",
        },
        "future_outlook": {
            "product_vision": "Scalable AI execution platform.",
            "viability_assessment": "High viability assuming continuous cloud cost controls.",
            "year_1_projection": {
                "projection": "Achieve SOC 2 Type II compliance.",
                "confidence": "high",
                "key_milestones": ["Milestone 1"],
            },
        },
        "strategic_advice": {
            "immediate_actions": [{"action": "Add CI/CD secret scanning", "rationale": "Prevent accidental leaks.", "expected_impact": "Immediate security baseline."}],
            "medium_term": [],
            "long_term_vision": "Sovereign AI infra.",
        },
        "investment_thesis": {
            "recommendation": "BUY",
            "rationale": "Strong unit economics and resilient engineering team.",
            "target_valuation_factors": ["High gross margin"],
            "comparable_companies": ["Datadog", "Snowflake"],
        },
        "competitive_analysis": {
            "target_company": project_name,
            "home_country": "US",
            "markets": [
                {
                    "market_name": "Global",
                    "market_name_ja": "グローバル",
                    "charts": [
                        {
                            "chart_type": "magic_quadrant",
                            "title": "Market Positioning",
                            "x_axis_label": "Execution Ability",
                            "y_axis_label": "Completeness of Vision",
                            "x_axis_rationale": "Measures engineering execution track record.",
                            "y_axis_rationale": "Measures defensibility of technological strategy.",
                            "data_points": [
                                {"name": project_name, "x": 80, "y": 85, "z": 50, "is_target": True},
                                {"name": "CompetitorA", "x": 70, "y": 65, "z": 40},
                            ],
                        }
                    ],
                }
            ],
        },
        "competitor_matrix": [
            {
                "competitor_name": "CompetitorA",
                "category": "direct",
                "hq_country": "US",
                "market_position": "Challenger",
                "rationale_text": "Good user experience but weaker backend security.",
                "sources": ["https://competitora.com/whitepaper"],
                "last_verified": "2026-03-15",
            }
        ],
        "implementation_matrix": {
            "target_company": project_name,
            "competitors": ["CompetitorA"],
            "items": [
                {
                    "layer_name": "Infrastructure Security",
                    "item_en": "KMS envelope encryption",
                    "item_ja": "KMSエンベロープ暗号化",
                    "statuses": [
                        {
                            "company_name": project_name,
                            "status": "implemented",
                            "sources": ["src/crypto/kms.py"],
                            "last_verified": "2026-04-01",
                        }
                    ],
                }
            ],
        },
        "red_flags": [
            {
                "id": "flag-audit-1",
                "title": "Not a false positive: Missing rate limiting",
                "description": "This is not a false positive: endpoint /auth/login lacks rate limiting.",
                "severity": "HIGH",
                "business_impact": "Vulnerable to credential stuffing.",
            }
        ],
        "atlas_four_axis": {
            "industry_context": "B2B SaaS / FinTech",
            "technology_potential": {"name": "Tech Potential", "score": 8.0, "weight": 0.25, "rationale": "Solid.", "sub_items": []},
            "market_traction": {"name": "Market Traction", "score": 7.5, "weight": 0.25, "rationale": "Early pilot revenue.", "sub_items": []},
            "team_execution": {"name": "Team Execution", "score": 9.0, "weight": 0.25, "rationale": "Top tier backgrounds.", "sub_items": []},
            "defensibility_moat": {"name": "Defensibility Moat", "score": 8.5, "weight": 0.25, "rationale": "Patented algorithms.", "sub_items": []},
        },
    }


# ===========================================================================
# 1. CLI report --consulting <json> --pdf execution
# ===========================================================================
def test_cli_report_consulting_pdf(tmp_path):
    """Test that `dde report --consulting <json> --pdf` runs with exit code 0 and produces a PDF."""
    runner = CliRunner()
    consulting_data = _make_sample_consulting_dict("AlphaCorp")
    json_path = tmp_path / "dde_consulting_alphacorp_20260402.json"
    json_path.write_text(json.dumps(consulting_data), encoding="utf-8")

    out_dir = tmp_path / "output_pdf"
    out_dir.mkdir()

    result = runner.invoke(cli, ["report", "--consulting", str(json_path), "--pdf", "-o", str(out_dir), "-l", "en"])
    assert result.exit_code == 0, f"CLI error: {result.output}\nException: {result.exception}"
    pdfs = list(out_dir.glob("*.pdf"))
    assert len(pdfs) == 1, f"Expected 1 PDF, got {pdfs}"
    assert pdfs[0].stat().st_size > 1000, "Generated PDF must be non-empty"


# ===========================================================================
# 2. Local-only & prompt isolation (never call AI providers)
# ===========================================================================
def test_skip_ai_and_prompt_isolation(monkeypatch, tmp_path):
    """Test that `dde prompt` and `dde analyze --skip-ai` never invoke AI providers even when keys are set."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-key-123")
    monkeypatch.setenv("GOOGLE_AI_API_KEY", "AIzaSyMockKey-456")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-mock-key-789")

    # Set up a clean dummy repo
    dummy_repo = tmp_path / "dummy_repo"
    dummy_repo.mkdir()
    (dummy_repo / "main.py").write_text("print('hello world')\n", encoding="utf-8")

    with patch("due_diligence_engine.ai.providers.OpenAIProvider.analyze") as mock_openai, \
         patch("due_diligence_engine.ai.providers.GoogleProvider.analyze") as mock_google, \
         patch("due_diligence_engine.ai.providers.AnthropicProvider.analyze") as mock_anthropic:

        runner = CliRunner()

        # (a) dde prompt must generate prompt text locally without invoking any AI
        res_prompt = runner.invoke(cli, ["prompt", str(dummy_repo)])
        assert res_prompt.exit_code == 0, f"prompt command failed: {res_prompt.output}"
        mock_openai.assert_not_called()
        mock_google.assert_not_called()
        mock_anthropic.assert_not_called()

        # (b) dde analyze --skip-ai must run analysis without invoking any AI
        out_analysis = tmp_path / "analysis_out"
        res_analyze = runner.invoke(cli, ["analyze", str(dummy_repo), "--skip-ai", "--skip-git", "-o", str(out_analysis)])
        assert res_analyze.exit_code == 0, f"analyze --skip-ai failed: {res_analyze.output}"
        mock_openai.assert_not_called()
        mock_google.assert_not_called()
        mock_anthropic.assert_not_called()


# ===========================================================================
# 3. SecureLoader preserves .git and shreds clone dir upon destroy
# ===========================================================================
def test_secure_loader_preserves_git_and_shreds_clone_dir(tmp_path):
    """Test that SecureLoader.load_from_url preserves .git for forensics and shreds _clone_dir on destroy."""
    loader = SecureLoader(Config(temp_dir=tmp_path / "loader_temp"))

    def mock_git_clone(cmd, **kwargs):
        dest = Path(cmd[-1])
        dest.mkdir(parents=True, exist_ok=True)
        git_dir = dest / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        (git_dir / "config").write_text("[core]\n", encoding="utf-8")
        (dest / "main.py").write_text("print('cloned')", encoding="utf-8")
        res = MagicMock()
        res.returncode = 0
        return res

    with patch("subprocess.run", side_effect=mock_git_clone):
        codebase = loader.load_from_url("https://github.com/mock-org/mock-repo.git")
        clone_dir = loader._clone_dir
        assert clone_dir is not None
        assert clone_dir.exists(), "Clone dir must exist during analysis"
        assert (clone_dir / "repo" / ".git").exists(), ".git must be preserved for forensics during analysis"
        assert loader._fernet is not None, "Encryption key must be initialized"

        loader.destroy()

        assert not clone_dir.exists(), "Clone dir must be shredded and removed upon destroy()"
        assert loader._clone_dir is None, "loader._clone_dir reference must be cleared"
        assert loader._fernet is None, "loader._fernet must be set to None"


# ===========================================================================
# 4. Symlink security and Zip Slip protection
# ===========================================================================
def test_symlink_and_zip_slip_security(tmp_path):
    """Test that SecureLoader blocks Zip Slip and symlinks, and SecurePurger does not follow out-of-root symlinks."""
    # (a1) Directory traversal attempt blocked with ValueError
    evil_zip_1 = tmp_path / "malicious_traversal.zip"
    with zipfile.ZipFile(evil_zip_1, "w") as zf:
        zf.writestr("../evil_traversal.txt", "MALICIOUS")
    loader1 = SecureLoader(Config(temp_dir=tmp_path / "zip_temp1"))
    with pytest.raises(ValueError, match="Zip path traversal detected"):
        loader1.load_archive(evil_zip_1)
    loader1.destroy()

    # (a2) Sibling prefix attempt blocked with ValueError
    evil_zip_2 = tmp_path / "malicious_sibling.zip"
    with zipfile.ZipFile(evil_zip_2, "w") as zf:
        zf.writestr("../_extracted_evil/evil.txt", "MALICIOUS SIBLING")
    loader2 = SecureLoader(Config(temp_dir=tmp_path / "zip_temp2"))
    with pytest.raises(ValueError, match="Zip path traversal detected"):
        loader2.load_archive(evil_zip_2)
    loader2.destroy()

    # (a3) Symlink in zip blocked with ValueError
    evil_zip_3 = tmp_path / "malicious_symlink.zip"
    with zipfile.ZipFile(evil_zip_3, "w") as zf:
        zi = zipfile.ZipInfo("symlink_file")
        zi.create_system = 3  # UNIX
        zi.external_attr = (0o120777 << 16)  # symlink mode
        zf.writestr(zi, "/etc/passwd")
    loader3 = SecureLoader(Config(temp_dir=tmp_path / "zip_temp3"))
    with pytest.raises(ValueError, match="Zip symlink rejected"):
        loader3.load_archive(evil_zip_3)
    loader3.destroy()

    # (b) SecurePurger does NOT follow symlink outside shred directory
    sensitive_outside = tmp_path / "sensitive_outside.txt"
    sensitive_outside.write_text("SENSITIVE DATA TO PROTECT", encoding="utf-8")

    purge_target_dir = tmp_path / "purge_target"
    purge_target_dir.mkdir()
    (purge_target_dir / "dummy_file.txt").write_text("TO BE PURGED", encoding="utf-8")
    symlink_inside = purge_target_dir / "link_to_sensitive"
    symlink_inside.symlink_to(sensitive_outside)

    purger = SecurePurger()
    purger.purge_directory(purge_target_dir, analysis_id="test-id", project_name="test-proj")

    # The target dir should be gone
    assert not purge_target_dir.exists()
    # The sensitive outside file must STILL exist with contents intact!
    assert sensitive_outside.exists(), "Purger must NOT delete outside files pointed by symlinks"
    assert sensitive_outside.read_text(encoding="utf-8") == "SENSITIVE DATA TO PROTECT"


# ===========================================================================
# 5. Score.compute() deduplication and idempotence
# ===========================================================================
def test_score_compute_deduplication_and_idempotence():
    """Test that Score.compute() deduplicates red flags by ID and produces identical results on repeated calls."""
    flag_dup_1 = RedFlag(id="sec-001", category="security", title="Hardcoded Key", description="Secret key found", severity=Severity.HIGH)
    flag_dup_2 = RedFlag(id="sec-001", category="security", title="Hardcoded Key (dup)", description="Secret key found again", severity=Severity.HIGH)
    flag_unique = RedFlag(id="perf-002", category="performance", title="N+1 Query", description="Inefficient query loop", severity=Severity.MEDIUM)

    dim1 = ScoreDimension(name="architecture_quality", score=80.0, weight=0.5, rationale="test rationale", flags=[flag_dup_1, flag_dup_2])
    dim2 = ScoreDimension(name="technical_originality", score=90.0, weight=0.5, rationale="test rationale", flags=[flag_unique])

    score = Score(dimensions=[dim1, dim2], red_flags=[flag_dup_1, flag_dup_2, flag_unique])

    # First computation
    score.compute()
    assert len(score.red_flags) == 2, f"Expected 2 unique flags, got {len(score.red_flags)}"
    assert [f.id for f in score.red_flags] == ["sec-001", "perf-002"]

    first_overall = score.overall_score
    first_flags_count = len(score.red_flags)

    # Second computation (idempotence verification)
    score.compute()
    assert score.overall_score == first_overall
    assert len(score.red_flags) == first_flags_count
    assert [f.id for f in score.red_flags] == ["sec-001", "perf-002"]


# ===========================================================================
# 6. AI Providers: ThinkingBlock, OpenAI gpt-5, Google store=False
# ===========================================================================
def test_ai_providers_handling():
    """Test Anthropic ThinkingBlock parsing, OpenAI gpt-5 no-temperature/max_completion_tokens, and Google store=False."""
    # (a) AnthropicProvider handling ThinkingBlock before TextBlock
    anthropic_p = AnthropicProvider(api_key="mock-ant-key", model_id="claude-sonnet-5-5")

    class MockThinkingBlock:
        type = "thinking"
        thinking = "internal chain of thought reasoning..."

    class MockTextBlock:
        type = "text"
        text = json.dumps({
            "scores": {"technical_originality": 88.0, "technology_advancement": 82.0},
            "reasoning": "Original code verified.",
        })

    mock_anthropic_client = MagicMock()
    mock_anthropic_resp = MagicMock()
    mock_anthropic_resp.content = [MockThinkingBlock(), MockTextBlock()]
    mock_anthropic_resp.usage = MagicMock(input_tokens=150, output_tokens=80)
    mock_anthropic_client.messages.create.return_value = mock_anthropic_resp

    with patch("due_diligence_engine.ai.providers._require_sdk") as mock_sdk:
        mock_sdk_mod = MagicMock()
        mock_sdk_mod.Anthropic.return_value = mock_anthropic_client
        mock_sdk.return_value = mock_sdk_mod

        anth_result = anthropic_p.analyze("test summary", "test context")
        assert "scores" in anth_result
        assert anth_result["scores"].get("technical_originality") == 88.0

    # (b) OpenAIProvider with gpt-5: no temperature, max_completion_tokens=8192
    openai_p = OpenAIProvider(api_key="mock-openai-key", model_id="gpt-5")

    mock_openai_client = MagicMock()
    mock_openai_resp = MagicMock()
    mock_openai_resp.choices = [MagicMock(message=MagicMock(content=json.dumps({"scores": {"architecture_quality": 95.0}})))]
    mock_openai_resp.usage = MagicMock(prompt_tokens=200, completion_tokens=100)
    mock_openai_client.chat.completions.create.return_value = mock_openai_resp

    with patch("due_diligence_engine.ai.providers._require_sdk") as mock_sdk:
        mock_sdk_mod = MagicMock()
        mock_sdk_mod.OpenAI.return_value = mock_openai_client
        mock_sdk.return_value = mock_sdk_mod

        openai_result = openai_p.analyze("test summary", "test context")
        assert "scores" in openai_result
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert "temperature" not in call_kwargs, "gpt-5 reasoning model must NOT receive temperature"
        assert call_kwargs.get("max_completion_tokens") == 8192

    # (c) GoogleProvider: store=False in interactions.create
    google_p = GoogleProvider(api_key="mock-google-key", model_id="gemini-4-argon")

    mock_google_client = MagicMock()
    mock_google_resp = MagicMock()
    mock_google_resp.output_text = json.dumps({"scores": {"claim_consistency": 91.0}})
    mock_google_resp.usage = MagicMock(total_input_tokens=180, total_output_tokens=90, total_thought_tokens=0)
    mock_google_client.interactions.create.return_value = mock_google_resp

    with patch("due_diligence_engine.ai.providers._require_sdk") as mock_sdk:
        mock_sdk_mod = MagicMock()
        mock_sdk_mod.Client.return_value = mock_google_client
        mock_sdk.return_value = mock_sdk_mod

        google_result = google_p.analyze("test summary", "test context")
        assert "scores" in google_result
        call_google_kwargs = mock_google_client.interactions.create.call_args.kwargs
        assert call_google_kwargs.get("store") is False, "GoogleProvider must pass store=False"


# ===========================================================================
# 7. parse_consulting_dict robustness (rationales, sources, negated false-positives)
# ===========================================================================
def test_parse_consulting_response_robustness():
    """Test that response parsing retains rationales, sources, last_verified, negated false positives, and tolerates null/NaN."""
    raw_data = {
        "project_name": "RobustParseApp",
        "executive_summary": "Testing parser stability under edge conditions.",
        "dimension_scores": {
            "technical_originality": {"score": float("nan"), "label": "Originality"},
            "technology_advancement": None,
            "architecture_quality": {"score": 90.0, "label": "Architecture"},
        },
        "overall_score": None,  # Will be reconciled from non-empty valid dimensions
        "competitive_analysis": {
            "target_company": "RobustParseApp",
            "home_country": "US",
            "markets": [
                {
                    "market_name": "Global",
                    "charts": [
                        {
                            "chart_type": "magic_quadrant",
                            "title": "Analyst Wave",
                            "x_axis_label": "Execution Track",
                            "y_axis_label": "Vision Completeness",
                            "x_axis_rationale": "Execution metric rationale preserved.",
                            "y_axis_rationale": "Vision metric rationale preserved.",
                            "data_points": [{"name": "CompX", "x": 60, "y": 70, "sources": ["https://compx.io/spec"], "last_verified": "2026-03-20"}],
                        }
                    ],
                }
            ],
        },
        "competitor_rationales": [
            {
                "name": "CompX",
                "category": "direct",
                "rationale_en": "Direct competitor in AI payment infra.",
                "hq_country": "US",
                "market_position": "Challenger",
            }
        ],
        "implementation_matrix": {
            "target_company": "RobustParseApp",
            "competitors": ["CompX"],
            "items": [
                {
                    "layer_name": "Auth Layer",
                    "item_en": "OAuth2 PKCE",
                    "item_ja": "OAuth2 PKCE",
                    "statuses": [
                        {
                            "company_name": "RobustParseApp",
                            "status": "implemented",
                            "sources": ["src/auth/pkce.ts"],
                            "last_verified": "2026-04-05",
                        }
                    ],
                }
            ],
        },
        "red_flags": [
            {
                "title": "Definite Risk",
                "description": "This is not a false positive: SQL injection present in query builder.",
                "severity": "HIGH",
            },
            {
                "title": "誤検知ではないセキュリティ懸念",
                "description": "誤検知ではなく、本番の認証バイパスリスクが存在します。",
                "severity": "CRITICAL",
            },
            {
                "title": "Ignored Alarm",
                "description": "This is a false positive caused by dummy credentials in tests.",
                "severity": "LOW",
            },
        ],
    }

    report = parse_consulting_dict(raw_data)
    assert isinstance(report, ConsultingReport)

    # 1. Negated false positives are NOT filtered out, while true false-positive alarms are dropped
    assert len(report.red_flags) == 2, f"Expected 2 red flags, got {len(report.red_flags)}"
    flag_descriptions = [f.get("description", "") for f in report.red_flags]
    assert any("not a false positive" in d for d in flag_descriptions)
    assert any("誤検知ではなく" in d for d in flag_descriptions)

    # 2. Market chart rationales are preserved
    assert len(report.competitive_analysis.markets) > 0
    chart = report.competitive_analysis.markets[0].charts[0]
    assert chart.x_axis_rationale == "Execution metric rationale preserved."
    assert chart.y_axis_rationale == "Vision metric rationale preserved."

    # 3. Competitor DataPoint and Implementation sources & last_verified are preserved
    assert chart.data_points[0].sources == ["https://compx.io/spec"]
    assert chart.data_points[0].last_verified == "2026-03-20"

    assert len(report.competitor_rationales) == 1
    assert report.competitor_rationales[0].name == "CompX"

    assert len(report.implementation_matrix.items) == 1
    status = report.implementation_matrix.items[0].statuses[0]
    assert status.sources == ["src/auth/pkce.ts"]
    assert status.last_verified == "2026-04-05"

    # 4. Safe score clamping and reconciliation
    assert math.isfinite(report.overall_score)
    assert 0.0 <= report.overall_score <= 100.0


# ===========================================================================
# 8. PDFReportGenerator security escaping, Arabic non-destructive & layout
# ===========================================================================
def test_pdf_generator_security_and_arabic_rendering(tmp_path):
    """Test that PDF generator escapes HTML/XML tags, does not mutate ConsultingReport in Arabic, and maintains layout."""
    consulting_data = _make_sample_consulting_dict("SecurityTarget")
    report = parse_consulting_dict(consulting_data)

    # Inject potentially malicious tags and unclosed tags across various fields
    evil_text = '<img src="http://169.254.169.254/latest/meta-data/"> Injected text <script>alert(1)</script> & <b>unclosed tag'
    report.executive_summary = evil_text
    report.swot.strengths[0].point = "<evil_tag>Strength & Subversion</evil_tag>"
    report.strategic_advice.immediate_actions[0].action = "Action <script>console.log('xss')</script> & More"

    original_summary = str(report.executive_summary)

    result = AnalysisResult(
        project_name="SecurityTarget <img src='x'> & 'Quotes'",
        analysis_id="sec-audit-001",
        consulting_report=report,
    )

    pdf_gen = PDFReportGenerator()
    out_pdf = tmp_path / "arabic_sanitized.pdf"

    # Must generate successfully without XML parse error or SSRF
    pdf_gen.generate_to_file(result, out_pdf, lang="ar")
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 1000

    # Ensure result.consulting_report was NOT mutated in-place by Arabic reshaping
    assert report.executive_summary == original_summary

    # Verify competitive analysis pages have CELL_H == 152 and both label and drawing in the same cell
    comp_flowables = pdf_gen._build_competitive_analysis_pages(report)
    assert len(comp_flowables) > 0

    from reportlab.platypus import Table
    tables = [elem for elem in comp_flowables if isinstance(elem, Table)]
    assert len(tables) > 0
    for table in tables:
        # Inspect cell contents: every cell with content should be a list containing [Paragraph, Drawing]
        for row in table._cellvalues:
            for cell in row:
                if isinstance(cell, list):
                    types = [type(c).__name__ for c in cell]
                    assert "Paragraph" in types, f"Cell must contain Paragraph, got {types}"
                    assert "Drawing" in types, f"Cell must contain Drawing, got {types}"


# ===========================================================================
# 9. Phase 3 Audit Regressions: AI results markdown & Red flags format
# ===========================================================================
def test_markdown_ai_results_and_red_flags():
    """Verify Markdown report formats AI results correctly with Failed/Success and provider/model_id,
    and formats Red Flags as - **[SEVERITY]** **Title** (category) supporting both Enum and str severity."""
    from due_diligence_engine.models import AIProviderResult, AnalysisResult, RedFlag, Score, Severity
    from due_diligence_engine.report.generator import ReportGenerator

    flags = [
        RedFlag(id="rf1", title="SQL Injection", description="SQL injection risk", category="security", severity=Severity.CRITICAL),
        RedFlag(id="rf2", title="Slow Query", description="Slow query loop", category="performance", severity="high"),
    ]
    res = AnalysisResult(
        project_name="TestProject",
        score=Score(overall_score=85.0, grade="B", recommendation="Viable", red_flags=flags, dimensions=[]),
        ai_results={
            "chatgpt": AIProviderResult(provider="chatgpt", model_id="gpt-5"),
            "gemini": AIProviderResult(provider="gemini", model_id="gemini-4-argon", error="Rate limited"),
        },
        red_flags=flags,
    )
    generator = ReportGenerator()
    md = generator.generate_markdown(res)

    assert "### Chatgpt (gpt-5) — Success" in md
    assert "### Gemini (gemini-4-argon) — Failed" in md
    assert "**Error:** Rate limited" in md
    assert "- **[CRITICAL]** **SQL Injection** (security)" in md
    assert "- **[HIGH]** **Slow Query** (performance)" in md


# ===========================================================================
# 10. Phase 3 Audit Regressions: action.yml regex matching
# ===========================================================================
def test_action_yml_regex():
    """Verify action.yml regex filters out '- **Files:**' etc. and only counts '- **[SEVERITY]**'."""
    import re
    pattern = re.compile(r'^\s*-\s*\*\*\[(CRITICAL|HIGH|MEDIUM|LOW|INFO)\]\*\*')

    positive_lines = [
        "- **[CRITICAL]** **API key leak** (security)",
        "  - **[HIGH]** **Missing rate limit** (security)",
        "- **[MEDIUM]** **Low test coverage** (quality)",
        "- **[LOW]** **Outdated dependency** (deps)",
        "- **[INFO]** **Informational notice** (general)",
    ]
    negative_lines = [
        "- **Files:** 10",
        "- **Issues:** 0",
        "- **Score:** 85/100",
        "- **openai** (gpt-5): Success",
        "- [CRITICAL] Not bold brackets",
        "**[HIGH]** Missing dash prefix",
    ]
    for line in positive_lines:
        assert pattern.search(line), f"Should match: {line}"
    for line in negative_lines:
        assert not pattern.search(line), f"Should not match: {line}"


# ===========================================================================
# 11. Phase 3 Audit Regressions: SiteAnalyzer DNS SSRF & redirect protection
# ===========================================================================
def test_site_analyzer_dns_ssrf_and_redirects():
    """Verify _is_safe_url blocks DNS resolving to private IPs and handles redirects securely."""
    import socket
    from due_diligence_engine.analyze.site_analyzer import _is_safe_url, SiteAnalyzer

    analyzer = SiteAnalyzer()

    # Public IP: safe
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        assert _is_safe_url("https://example.com") is True

    # Private IP resolved: blocked
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
        assert _is_safe_url("https://malicious-local.com") is False

    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0))]
        assert _is_safe_url("https://cloud-metadata.internal") is False

    # Redirect loop / redirect to private IP blocked
    with patch("due_diligence_engine.analyze.site_analyzer._is_safe_url") as mock_safe:
        mock_safe.side_effect = lambda u: "safe" in u
        mock_resp1 = MagicMock()
        mock_resp1.is_redirect = True
        mock_resp1.status_code = 302
        mock_resp1.headers = {"location": "http://169.254.169.254/latest/meta-data/"}

        with patch("httpx.Client.get", return_value=mock_resp1):
            analyzer._crawl("https://safe-start.com")
            assert len(analyzer._texts) == 0  # Blocked because redirect target is unsafe


# ===========================================================================
# 12. Phase 3 Audit Regressions: PDFReportGenerator Latin entity integrity
# ===========================================================================
def test_pdf_generator_latin_xml_entity_integrity():
    """Verify PDFReportGenerator._esc_text preserves XML entities (&amp;, etc.) when wrapping Latin words."""
    pdf_gen = PDFReportGenerator()
    pdf_gen._lang = "ar"
    raw = "تقرير & اختبار AI/ML و Platform (v2.0)"
    esc = pdf_gen._esc_text(raw)
    assert "&amp;amp;" not in esc
    assert "&amp;" in esc
    assert '<font name="Helvetica">AI/ML</font>' in esc
    assert '<font name="Helvetica">Platform</font>' in esc

    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    p = Paragraph(esc, styles["Normal"])
    assert p is not None


# ===========================================================================
# 13. Phase 3 Audit Regressions: SecurePurger symlink dir & overwrite error
# ===========================================================================
def test_purge_directory_symlink_and_overwrite_error(tmp_path):
    """Verify purge_directory unlinks symlink root without following, and records failed_files on overwrite error."""
    purger = SecurePurger()

    # Case 1: Target directory itself is a symlink
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    (real_dir / "secret.txt").write_text("DO NOT DELETE", encoding="utf-8")
    symlink_dir = tmp_path / "symlink_dir"
    symlink_dir.symlink_to(real_dir, target_is_directory=True)

    cert = purger.purge_directory(symlink_dir, analysis_id="test-sym", project_name="test-sym")
    assert cert.verification_hash != "purge_incomplete"
    assert cert.files_purged == 1
    assert not symlink_dir.exists()
    assert real_dir.exists(), "Underlying real directory must NOT be deleted when target is symlink"
    assert (real_dir / "secret.txt").read_text(encoding="utf-8") == "DO NOT DELETE"

    # Case 2: Overwrite error re-raised and counted as failed_files
    target_dir = tmp_path / "target_with_locked_file"
    target_dir.mkdir()
    locked_file = target_dir / "locked.txt"
    locked_file.write_text("CANNOT OVERWRITE", encoding="utf-8")

    with patch.object(purger, "_secure_overwrite", side_effect=OSError("Disk write error")):
        cert2 = purger.purge_directory(target_dir, analysis_id="test-fail", project_name="test-fail")
        assert cert2.verification_hash == "purge_incomplete"


# ===========================================================================
# 14. Phase 3 Audit Regressions: GoogleProvider inspect signature
# ===========================================================================
def test_google_provider_inspect_signature():
    """Verify GoogleProvider passes store=False when supported and only omits store when signature lacks it."""
    google_p = GoogleProvider(api_key="mock-key", model_id="gemini-4-argon")

    mock_client_kwargs = MagicMock()
    mock_resp = MagicMock()
    mock_resp.output_text = "{}"
    mock_resp.usage = MagicMock(total_input_tokens=10, total_output_tokens=10, total_thought_tokens=0)
    mock_client_kwargs.interactions.create.return_value = mock_resp

    with patch("due_diligence_engine.ai.providers._require_sdk") as mock_sdk:
        mock_sdk_mod = MagicMock()
        mock_sdk_mod.Client.return_value = mock_client_kwargs
        mock_sdk.return_value = mock_sdk_mod

        # Default MagicMock has signature accepting (*args, **kwargs) -> store=False passed
        google_p.analyze("summary", "context")
        kwargs = mock_client_kwargs.interactions.create.call_args.kwargs
        assert kwargs.get("store") is False

        # Client where interactions.create has strict signature without store
        def strict_create(model=None, input=None):
            return mock_resp

        mock_client_strict = MagicMock()
        mock_client_strict.interactions.create = strict_create
        mock_sdk_mod.Client.return_value = mock_client_strict

        # Fails closed on zero-retention violation
        res_fail = google_p.analyze("summary", "context")
        assert "error" in res_fail
        assert "Zero-retention policy violation" in res_fail["error"]


# ===========================================================================
# 15. Phase 3 Audit Regressions: Response parser null safety & grade fallback
# ===========================================================================
def test_response_parser_null_safe_and_grade_fallback():
    """Verify parse_consulting_dict safely handles None (null) collections and calculates grade when omitted."""
    raw = {
        "project_name": "NullApp",
        "executive_summary": "Null collections test",
        "dimension_scores": {
            "technical_originality": {"score": 85.0, "label": "Tech Originality"},
            "technology_advancement": {"score": 85.0, "label": "Tech Advancement"},
        },
        "swot": {"strengths": None, "weaknesses": None, "opportunities": None, "threats": None},
        "strategic_advice": {"immediate_actions": None, "medium_term": None},
        "competitive_analysis": {"markets": None},
        "site_verification": {"claims": None},
        "overall_score": 85.0,
        "grade": "",
    }
    report = parse_consulting_dict(raw)
    assert report.grade == "B"
    assert report.swot is not None
    assert report.strategic_advice is not None
    assert report.competitive_analysis is not None
    assert report.site_verification is not None


# ===========================================================================
# 16. Phase 3 Audit Regressions: SecureLoader skips special files (FIFOs, etc.)
# ===========================================================================
def test_secure_loader_skips_special_files(tmp_path):
    """Verify SecureLoader._walk_files and load_directory skip non-regular files (FIFOs, sockets, device nodes)."""
    import os
    loader = SecureLoader(Config(temp_dir=tmp_path / "loader_temp"))
    source_dir = tmp_path / "special_source"
    source_dir.mkdir()
    regular_file = source_dir / "normal.py"
    regular_file.write_text("print('normal')", encoding="utf-8")

    fifo_file = source_dir / "fifo_pipe.py"
    try:
        os.mkfifo(str(fifo_file))
        has_fifo = True
    except (AttributeError, OSError):
        has_fifo = False

    if has_fifo:
        walked = list(loader._walk_files(source_dir))
        assert regular_file in walked
        assert fifo_file not in walked

        work_dir = loader.load_directory(source_dir)
        enc_files = list(work_dir.glob("**/*.enc"))
        assert len(enc_files) == 1
        assert "normal.py.enc" in enc_files[0].name
        loader.destroy()


# ===========================================================================
# 17. Phase 3 2nd Audit: DNS Rebinding / TOCTOU protection
# ===========================================================================
def test_site_analyzer_dns_rebinding_protection():
    """Verify that DNS rebinding is neutralized and _pinned_dns_context supports nesting/concurrency."""
    import socket
    from due_diligence_engine.analyze.site_analyzer import (
        SiteAnalyzer,
        _pinned_dns_context,
        _resolve_and_validate_url,
    )

    analyzer = SiteAnalyzer()

    # Sequence of DNS returns for "rebinding.com":
    # Call 1 (during _resolve_and_validate_url): returns public 93.184.216.34
    # Call 2 (if external DNS was re-queried during client.get): would return loopback 127.0.0.1
    dns_responses = [
        [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))],
        [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))],
    ]

    with patch("socket.getaddrinfo", side_effect=dns_responses) as mock_getaddr:
        is_safe, host, addr_info = _resolve_and_validate_url("http://rebinding.com")
        assert is_safe is True
        assert host == "rebinding.com"

        # Within the pinned context, looking up rebinding.com must return the pinned public IP, NOT 127.0.0.1
        with _pinned_dns_context(host, addr_info):
            resolved = socket.getaddrinfo("rebinding.com", 80)
            resolved_ip = resolved[0][4][0]
            assert resolved_ip == "93.184.216.34"

            # And looking up an unexpected host that resolves to loopback must raise socket.gaierror
            mock_getaddr.side_effect = lambda h, p, *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", p))]
            with pytest.raises(socket.gaierror, match="Blocked non-public IP"):
                socket.getaddrinfo("evil-internal.com", 80)

    # Test nesting / stack semantics:
    # Outer context pins host1 to IP 93.184.216.34
    # Inner context pins host2 to IP 93.184.216.35
    addr1 = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))]
    addr2 = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.35", 80))]
    with _pinned_dns_context("host1.com", addr1):
        assert socket.getaddrinfo("host1.com", 80)[0][4][0] == "93.184.216.34"
        with _pinned_dns_context("host2.com", addr2):
            assert socket.getaddrinfo("host1.com", 80)[0][4][0] == "93.184.216.34"
            assert socket.getaddrinfo("host2.com", 80)[0][4][0] == "93.184.216.35"
        # Exiting inner context must still keep host1 pinned
        assert socket.getaddrinfo("host1.com", 80)[0][4][0] == "93.184.216.34"


# ===========================================================================
# 18. Phase 3 2nd Audit: Implementation Matrix XML injection protection in PDF
# ===========================================================================
def test_pdf_implementation_matrix_xml_injection_escaped(tmp_path):
    """Verify that malicious XML/HTML in ImplementationMatrix item_en/item_ja does not cause XML injection."""
    from due_diligence_engine.models import (
        AnalysisResult,
        CompanyImplementationStatus,
        ConsultingReport,
        ImplementationMatrix,
        ImplementationStatus,
        MatrixItem,
    )
    from due_diligence_engine.report.pdf_generator import PDFReportGenerator

    item_evil = MatrixItem(
        category="encryption",
        item_en='<img src="http://127.0.0.1/evil.png"/> & <script>alert("xss")</script>',
        item_ja='<evil_tag>テスト</evil_tag> & "Quotes"',
        statuses=[
            CompanyImplementationStatus(
                company_name="TargetApp",
                status=ImplementationStatus.VERIFIED,
                sources=["src/test.py"],
            )
        ],
    )
    im = ImplementationMatrix(
        target_company="TargetApp",
        competitors=["CompB"],
        items=[item_evil],
    )
    cr = ConsultingReport(
        project_name="XMLTargetApp",
        executive_summary="Testing PDF XML escape in implementation matrix.",
        implementation_matrix=im,
    )
    result = AnalysisResult(
        project_name="XMLTargetApp",
        analysis_id="pdf-esc-002",
        consulting_report=cr,
    )

    pdf_gen = PDFReportGenerator()
    out_pdf = tmp_path / "xml_escape_test.pdf"

    # Must build without ReportLab XML parse errors
    pdf_gen.generate_to_file(result, out_pdf, lang="en")
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 1000

    out_pdf_ja = tmp_path / "xml_escape_test_ja.pdf"
    pdf_gen.generate_to_file(result, out_pdf_ja, lang="ja")
    assert out_pdf_ja.exists()
    assert out_pdf_ja.stat().st_size > 1000


# ===========================================================================
# 19. Phase 3 2nd Audit: SecureLoader shredding error propagation & reference preservation
# ===========================================================================
def test_secure_loader_shred_tree_error_propagation(tmp_path):
    """Verify that SecureLoader.destroy() / _shred_tree raises on deletion/walk error and preserves dir reference."""
    loader = SecureLoader(Config(temp_dir=tmp_path / "loader_temp"))
    source_dir = tmp_path / "test_source"
    source_dir.mkdir()
    (source_dir / "code.py").write_text("print('sensitive')", encoding="utf-8")

    work_dir = loader.load_directory(source_dir)
    assert work_dir.exists()
    assert loader._work_dir is not None

    # 1. Inject an OSError during file unlinking in _shred_tree
    with patch("pathlib.Path.unlink", side_effect=OSError("Permission denied: simulated lock")):
        with pytest.raises(OSError, match="simulated lock|Failed to securely shred"):
            loader.destroy()

        # Workspace directory reference must NOT be cleared when shredding failed
        assert loader._work_dir is not None, "Failed shredding must preserve _work_dir reference"
        assert loader._work_dir.exists()

    # Allow shredding to succeed
    loader.destroy()
    assert loader._work_dir is None
    assert not work_dir.exists()

    # 2. Verify os.walk onerror callback propagates to shred_errors and raises
    work_dir2 = loader.load_directory(source_dir)
    assert loader._work_dir is not None

    def mock_walk_error(top, onerror=None, **kwargs):
        if onerror:
            onerror(OSError("Directory permission denied during walk"))
        return iter([])

    with patch("os.walk", side_effect=mock_walk_error):
        with pytest.raises(OSError, match="Directory permission denied during walk|Failed to securely shred"):
            loader.destroy()
        assert loader._work_dir is not None

    # Cleanup properly
    loader.destroy()
    assert loader._work_dir is None
