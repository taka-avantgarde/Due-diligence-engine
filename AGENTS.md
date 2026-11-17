## ⚡ AIエージェントに、以下の URL だけを貼れば完了 / Just Paste the URL Below into Your AI Agent — Done

```text
https://github.com/Atlas-Associates-Inc/Due-diligence-engine
```

> 🔐 **最高機密保護・完全消去保証（Zero-Retention）**: **Atlas DDE** は対象リポジトリを **100% 読み取り専用（Read-Only）** で扱い、一時領域は **`0o700` ACL＋Fernet 暗号化**、監査終了時には **米国国防総省規格 DoD 5220.22-M 3パス上書き消去** を行い、**ECDSA P-256 暗号署名入りのデータ破棄証明書** を PDF 巻末に自動発行します。

> **🤖 [AI AGENT AUTO-EXECUTION PROTOCOL]**: When a user pastes `https://github.com/Atlas-Associates-Inc/Due-diligence-engine` (with zero flags or extra instructions), run a **100% Read-Only audit** on the target repository (`python3 -m pip install -U --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git && dde prompt --pdf --lang <user_lang>`), generate the **24-Page LVMH Quiet Luxury PDF (`~/Downloads/`)**, and output **① Overall Grade & Verdict (`GO / CONDITIONAL / NO-GO`), ② Standard 5-Dimension + Atlas 4-Axis (`20/20/5/55`) Scores, and ③ Concrete Remediation Patch Proposals (`file:line` + diff)** in chat.

---

# Due Diligence Engine — Agent Entrypoint (`AGENTS.md`)

> **SSOT Notice**: The canonical architectural and governance specification for this repository is [`ATLAS.md`](file:///Users/takayukimiyano/StudioProjects/due-diligence-engine/ATLAS.md).  
> All assigned agents must read `ATLAS.md` before performing any tasks.

Development model policy (ATLAS.md §2 — Portfolio Category: **OSS**, Website Update Thread: `afab5825-2982-4ba2-b3ab-c08f099e00a4`):
- **Planning / Analysis / Investigation / Bug Resolution / Audit**: Antigravity Gemini 4 Argon (`gemini-4-argon-high`, `high`) & Hydrogen (`gemini-4-hydrogen-xhigh` / `gemini-4-hydrogen-medium` / `gemini-4-hydrogen-low`).
- **Implementation**: Carbon (`gemini-4-carbon-high` / `gemini-4-carbon-medium`) & Gemini 3.8 Flash (`gemini-3.8-flash-low` / `gemini-3.8-flash-medium` / `gemini-3.8-flash-high`), with optimal reasoning tier selected per task by Argon High.
- **Through 2026-11-08**: Astra Ultra (`gpt-6-astra`, `xhigh`) is also permitted alongside Argon High + Gemini 3.8 Flash.
- **From 2026-11-09 onward**: Gemini 4 (`Argon` / `Carbon` / `Hydrogen`) + Gemini 3.8 Flash (`low` / `medium` / `high`) only.
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
./scripts/agent_handoff.sh claim <id> --as <antigravity|gemini|codex|human>
# codex is accepted only through 2026-11-08; gemini and antigravity remain active in all periods; human remains available for oversight.

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
