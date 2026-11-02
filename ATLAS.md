# Due Diligence Engine — Architecture, Governance & SSOT (`ATLAS.md`)

> **Single Source of Truth (SSOT)** for Due Diligence Engine (`Atlas-Associates-Inc/Due-diligence-engine`).  
> All human contributors, orchestrator agents, and executor agents MUST adhere strictly to this document.

---

## §1 Overview & Architecture

Due Diligence Engine (DDE) is a bank-grade, enterprise-ready software due diligence and M&A code audit platform. It combines static source-tree inspection, live site/infrastructure verification, AI-driven evaluation across 9 institutional dimensions, and cryptographic zero-retention data wiping.

### Key Components

```
due_diligence_engine/
├── __init__.py          # Version SSOT (__version__)
├── api.py               # Shared Application API (Programmatic Audit Engine)
├── cli.py               # CLI entrypoint (dde prompt, dde audit, dde score, dde mcp, dde purge)
├── config.py            # Model & Pricing SSOT (MODELS, PROVIDER_MODEL_COSTS, BYOK_DEFAULT_MODELS)
├── mcp_server.py        # Native Model Context Protocol (MCP) Server ("dde mcp")
├── maintenance.py       # SSOT consistency & release gate checker ("check --profile quick|release")
├── models.py            # Typed domain entities (AnalysisResult, ConsultingReport, DimensionScore)
├── ai/                  # Multi-provider LLM integrations (Claude, Gemini, ChatGPT/Astra) with store=False
├── analyze/             # Repository ingest, AST parsing, and SSRF-safe site verification (site_analyzer.py)
├── ingest/              # Secure data ingest, memory-backed tmpfs, and DOD 5220.22-M shredding
├── prompt/              # 9-dimension structured prompt generation & robust JSON response parsing
├── purge/               # DoD 5220.22-M 3-pass data wipe, Fernet encryption, ECDSA P-256 purge certificates
├── report/              # 24-page enterprise PDF generator (pdf_generator.py), HTML scorecard, 14-lang i18n
└── score/               # Monotonic 9-dimension scoring engine, grade boundaries, zero-false-positive filtering
```

- **Shared Application API (`api.py`)**: Core programmatic interface exposing `prepare_audit()`, `list_evidence()`, `read_evidence()`, `verify_sites()`, `validate_report()`, `render_report()`, and `close_audit()`.
- **Native MCP Server (`mcp_server.py` / `dde mcp`)**: Standard Model Context Protocol server exposing tools (`dde_prepare_audit`, `dde_list_evidence`, `dde_read_evidence`, `dde_verify_sites`, `dde_validate_report`, `dde_render_report`, `dde_close_audit`) and resources (`dde://schemas/consulting/v1`, `dde://evidence/...`, `dde://report/...`).
- **CLI (`cli.py`)**: Direct terminal interface for human operators and script automation.
- **Maintenance (`maintenance.py`)**: Unified maintenance runner (`python -m due_diligence_engine.maintenance check --profile quick` or `--profile release`).

---

## §2 AI Model Split Policy

To ensure supreme software engineering quality, rigorous peer review, and zero-defect execution (Claude development agents are not used):

| Period | Assigned Model(s) | Reasoning Effort | Responsibility |
|---|---|---|---|
| **Through 2026-11-08** | **Astra Ultra** (`gpt-6-astra`, `xhigh`)<br>+ **Antigravity Gemini 4 Argon** (High) | `xhigh` / `high` | Full-spectrum analysis, root-cause investigation, architectural design, holistic cross-layer implementation, and independent verification. |
| **From 2026-11-09 Onward** | **Antigravity Gemini 4 Argon** (High) **Only** | `high` | Exclusive unified model for all orchestration, analysis, design, implementation, and verification (zero external agent dependency). |

### Reasoning Effort Guidelines
- **`low`**: Minor mechanical edits, single-file typo fixes, documentation synchronization.
- **`medium`**: Standard multi-file feature additions, non-critical tests, template adjustments.
- **`high`**: Cryptographic routines, DoD wiping, authentication/SSRF security boundaries, billing/pricing SSOT, ReportLab typography, and multi-model arbitration.

---

## §3 Local Folder Zero-Proliferation Policy

1. **Work Only in Canonical Root**:  
   The canonical workspace is `/Users/takayukimiyano/StudioProjects/due-diligence-engine`.
2. **Zero Sibling Folders**:  
   Never create sibling or snapshot folders (such as `dde-fix`, `due-diligence-engine-backup`, `dde-snapshot-20261101`).
3. **No Unmanaged Subfolders**:  
   Do not introduce ad-hoc subdirectories. Work within existing package folders (`due_diligence_engine/`, `tests/`, `.agents/`, `scripts/`).
4. **Git Worktrees**:  
   Use worktrees only when strictly required for parallel task isolation, and cleanly remove them upon task completion.

---

## §4 SSOT Registry & Zero-Drift Invariants

The repository enforces strict mechanical invariants via `tests/test_zero_drift_invariants.py`:

| Domain | Single Source of Truth (SSOT) | Protected Targets / Invariants |
|---|---|---|
| **Version** | `due_diligence_engine/__init__.py` (`__version__`) | `pyproject.toml`, `cli.py` (`@click.version_option`), `report/generator.py` footer, all 6 READMEs (badge + footer), `scorecard.html`. |
| **Models & Pricing** | `due_diligence_engine/config.py` (`MODELS`, `PROVIDER_MODEL_COSTS`, `BYOK_DEFAULT_MODELS`) | `ai/providers.py` defaults, cost calculation routines, zero date-tagged legacy model IDs, zero unverified models. |
| **HTML Templates** | `due_diligence_engine/report/templates/scorecard.html` | Canonical HTML template. Byte-for-byte parity with legacy root `templates/scorecard.html`. |
| **Documentation** | Multilingual (6 Languages) | Every update must synchronize across `README.md` (EN), `README.ja.md` (JA), `README.es.md` (ES), `README.ar.md` (AR), `README.fr.md` (FR), `README.de.md` (DE). Localized CLI flags and zero stale strings. |
| **PDF Dictionaries** | `due_diligence_engine/report/pdf_generator.py` & `i18n_packs.py` | Complete key parity across all 14 languages (`en`, `ja`, `es`, `fr`, `de`, `pt`, `nl`, `it`, `id`, `zh`, `ko`, `vi`, `th`, `ar`) in `_PDF_I18N`, `_DIM_NAME_MAPS`, `_PDF_GRADE_REC`. |
| **Security Boundaries** | `analyze/site_analyzer.py`, `purge/secure_delete.py`, `ai/providers.py` | SSRF prevention (blocking RFC 6598 carrier-grade NAT & private IP ranges via `ip.is_global`), DoD 5220.22-M 3-pass wipe (`"r+b"`), Fernet encryption (`0o700`), ECDSA P-256 certs, fail-closed `store=False`. |
| **PDF Typography** | `due_diligence_engine/report/pdf_generator.py` | ReportLab 5.1 layout safety, `KeepInFrame` overflow prevention, Rust `python-bidi` for RTL (`ar`), Latin/digit `Helvetica` wrapping in `ar`/`th`, zero Japanese fallback leakage. |

---

## §5 Multi-Agent Handoff & Verification Gates

All task transitions between agents must pass through `scripts/agent_handoff.sh`.

### Verification Gate Commands
Before marking any order or task as done, the following gate commands must succeed with exit code `0`:
```bash
# 1. SSOT Consistency & Maintenance Check
python3 -m due_diligence_engine.maintenance check --profile quick

# 2. Comprehensive Test Suite (160+ tests)
.venv/bin/python -m pytest tests/ -q
```

### Agent Handoff Lifecycle
```
orchestrator:
  scripts/agent_handoff.sh new <type> <slug>     # Create new draft order
  scripts/agent_handoff.sh ready <id>             # Mechanical inspection -> status: ready
  scripts/agent_handoff.sh dispatch <id> --to <tool>

executor:
  scripts/agent_handoff.sh claim <id> --as <tool> # Lock order -> status: in_progress
  # Implement changes strictly according to order
  scripts/agent_handoff.sh verify <id>            # Run automated verification gates
  scripts/agent_handoff.sh done <id>              # Complete order & record results
  # If blocked:
  scripts/agent_handoff.sh handback <id> "reason" # Release lock & return to orchestrator
```
