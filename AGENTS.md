# Due Diligence Engine — Agent Entrypoint (`AGENTS.md`)

> **SSOT Notice**: The canonical architectural and governance specification for this repository is [`ATLAS.md`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/ATLAS.md).  
> All assigned agents must read `ATLAS.md` before performing any tasks.

Development model policy (ATLAS.md §2):
- **Through 2026-11-08**: Astra Ultra (`gpt-6-astra`, `xhigh`) + Antigravity Gemini 4 Argon (High).
- **From 2026-11-09 onward**: Antigravity Gemini 4 Argon (High) only.
- Claude development agents are not used. This policy does not change the product's AI providers.

---

## 1. Quick Verification Commands
Always verify your changes prior to completing tasks:
```bash
# Fast SSOT & Maintenance Consistency Check
python3 -m due_diligence_engine.maintenance check --profile quick

# Full Test Suite Execution (160+ tests)
.venv/bin/python -m pytest tests/ -q
```

---

## 2. Multi-Agent Handoff Protocol
Use `scripts/agent_handoff.sh` for all task management:
```bash
# Check current orders board
./scripts/agent_handoff.sh board

# Check environment & repository health
./scripts/agent_handoff.sh doctor

# Claim an order
./scripts/agent_handoff.sh claim <id> --as <antigravity|codex|human>
# codex is accepted only through 2026-11-08; human remains available for oversight.

# Verify work
./scripts/agent_handoff.sh verify <id>

# Run verification check gates
./scripts/agent_handoff.sh check
```

---

## 3. Available Skills (`.agents/skills/`)
- [`dde-audit`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/skills/dde-audit/SKILL.md): Repository auditing via native `dde mcp` tools.
- [`dde-consulting-report`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/skills/dde-consulting-report/SKILL.md): Full 24-page enterprise M&A consulting PDF report generation (14 languages).
- [`dde-dev-change`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/skills/dde-dev-change/SKILL.md): Internal developer workflow for version, model, pricing, or README updates.
- [`dde-dev-pdf-qa`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/skills/dde-dev-pdf-qa/SKILL.md): ReportLab PDF rendering, RTL Arabic shaping, and font QA.
- [`dde-dev-release`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/skills/dde-dev-release/SKILL.md): Release preparation, packaging validation, and security audit.

---

## 4. Governance & Engineering Rules (`.agents/rules/`)
- [`00_ssot_invariants.md`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/rules/00_ssot_invariants.md): Version, model/pricing SSOT, 6-language README, and 14-language PDF dictionaries.
- [`10_security_boundaries.md`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/rules/10_security_boundaries.md): Untrusted target isolation, RFC 6598 SSRF blocking, DoD 5220.22-M 3-pass wiping, fail-closed `store=False`.
- [`20_pdf_typography.md`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/.agents/rules/20_pdf_typography.md): ReportLab 5.1 layout safety, KeepInFrame scale factors, Rust python-bidi RTL shaping, Latin/digit font wrapping.
