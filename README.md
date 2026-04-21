<div align="center">

# Due Diligence Engine

**Your IDE's AI becomes a due diligence analyst. Zero API keys. PDF-first.**

Run `dde prompt --pdf` in Claude Code / Cursor / Copilot — the AI reads your codebase and generates a consulting-grade PDF evaluation.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![CodeQL](https://img.shields.io/badge/Security-CodeQL_%7C_Dependabot_%7C_pip--audit-5271FF.svg)](SECURITY.md)

[English](README.md) | [日本語](README.ja.md)

</div>

---

## Quick Start

```bash
pip install --no-cache-dir git+https://github.com/taka-avantgarde/Due-diligence-engine.git
dde prompt --pdf
```

That's it. Run this in any AI-powered IDE terminal. The AI autonomously reads the codebase, evaluates it as a world-class technology consultant, and writes a PDF to `~/Downloads/`.

No API keys. No cloud storage. No extra cost.

---

## What It Does

DDE turns your existing IDE AI subscription into a **technology due diligence analyst** for pre-investment analysis, acquisition review, competitor benchmarking, and AI-washing detection.

**Target users**: CTOs, VC technology partners, M&A technical advisors, corporate DD teams.

---

## Features

### Core (v1.x — available now)
- **Zero API Cost** — Uses your IDE's existing AI subscription (no separate key)
- **6-Dimension Scoring** — Technical Originality · Advancement · Implementation · Architecture · Claim Consistency · Security Posture
- **7 Competitive Charts** — Forrester Wave · BCG Growth-Share · McKinsey Tech Moat · Security & Privacy Maturity · Data Governance & Transparency · GS Risk-Return · Innovation Bubble
- **Deep Competitor Research** — 6-16 global competitors × 6 markets (Global / US / EMEA / Japan / SEA / LATAM)
- **Axis Rationale Captions** — Every chart explains *why* each axis was chosen and what it measures
- **Site Verification** — 10-item credibility audit against product/service URLs
- **SWOT · Investment Thesis · Red Flags** — Everything an investment committee needs
- **Bilingual** — EN / 日本語 PDFs with localized date stamps (`--lang ja`)
- **Security-Audited** — OSS with CodeQL, Dependabot, pip-audit, gitleaks on every PR
- **Tech Aesthetic** — Horizontal progress bars, high-contrast barometer, monospace numerics

### Great Version Up (v2.0 — in development)
> v2.0 **preserves 100% of v1.x content** and adds the following on top:
- 🚧 **Atlas Optimization Assessment** — Additional 4-axis view aligned with Atlas's engineering philosophy
  - Performance 25% · Stability 20% · Lightweight 5% · **Ultra-High Security 50%**
  - Security dominated by **cryptographic sophistication 30%** (Signal Protocol, PQXDH, self-rolled-crypto absence), not checkbox compliance
  - Non-public sub-item weights with industry-aware adjustment
- 🚧 **Implementation Capability Matrix** — 8th competitive chart
  - ~30 evaluation items × 6-10 top competitors
  - 4-state marking: ✓ verified / △ claimed / ✗ not implemented / ? unknown
  - Cryptographic items weighted heavily (libsignal, ML-KEM, E2E depth)
- 🚧 **Arc Brand Typography** — Black + `#5271FF` sky blue, tech-first aesthetic preserved

---

## Usage

```bash
# Current directory
dde prompt --pdf

# Japanese PDF
dde prompt --pdf --lang ja

# GitHub repo with stage context
dde prompt owner/repo --pdf --lang ja --stage seed

# Non-interactive mode (AI terminals without prompts)
dde prompt --pdf --lang ja \
  --url https://example.com \
  --url https://docs.example.com

# Direct BYOK multi-AI analysis (optional)
export ANTHROPIC_API_KEY=sk-ant-...
dde analyze owner/repo
```

---

## Scoring Framework

### 6 Dimensions

| Dimension | Weight | What It Detects |
|-----------|--------|-----------------|
| Technical Originality | 25% | API wrapper vs. genuine IP |
| Technology Advancement | 20% | Stack modernity |
| Implementation Depth | 20% | PoC vs. production |
| Architecture Quality | 15% | Structure quality |
| Claim Consistency | 10% | Pitch vs. reality |
| Security Posture | 10% | Security maturity |

### Grade Bands

```
0     40      60     75      90    100
|-----|-------|------|-------|-----|
  F      D       C      B       A
```

| Grade | Recommendation |
|-------|---------------|
| 🏆 A (90+) | Strong investment candidate |
| ✅ B (75-89) | Viable with conditions |
| ⚡ C (60-74) | Significant concerns |
| ⚠️ D (40-59) | High risk |
| 🚫 F (<40) | Do not invest |

Each dimension is also rated **Lv.1-10** with explicit criteria.

---

## PDF Structure

### v1.x — 13-15 pages (current)

| # | Section | Content |
|---|---------|---------|
| 1 | **Cover** | Black + Arc sky (#5271FF) accent, project name, score, grade |
| 2 | **Score Dashboard** | 6-dimension horizontal bar chart + score barometer |
| 3 | **Executive Summary** | Business + technical summary |
| 4 | **SWOT Analysis** | Evidence-based with business analogies |
| 5 | **Score Breakdown** | Per-dimension rationale & enablers |
| 6 | **Tech Level Assessment** | Lv.1-10 gauge with plain-language explanation |
| 7 | **Future Outlook** | 1/3/5-year projections with confidence |
| 8 | **Strategic Advice** | Immediate, medium, long-term |
| 9 | **Investment Thesis** | Recommendation, risks, upside, comparables |
| 10 | **Red Flags** | Severity-rated (Critical/High/Medium/Low) |
| 11 | **Site Verification** | 10-item credibility check (if URLs given) |
| 12-14 | **Competitive Analysis** | 7 chart types × 6 markets with axis rationale |
| 15 | **Glossary** | All jargon annotated for non-engineers |

### v2.0 — 19 pages (planned, all v1.x preserved)

| # | Section | Content |
|---|---------|---------|
| 1-15 | **All v1.x sections** | Preserved in full — no deletion, no consolidation |
| 16-17 | 🚧 **Atlas Optimization Assessment** | Performance/Stability/Lightweight/Ultra-Security (25/20/5/50) with encryption-dominant sub-breakdown |
| 18-19 | 🚧 **Implementation Capability Matrix** | ~30 items × 6-10 competitors, 4-state (✓△✗?), organized by dimension |

---

## Security

- ✅ **Local-only processing** — `dde prompt` never sends data anywhere
- ✅ **No source code in reports** — PDFs contain findings only
- ✅ **API 0-day retention** — `dde analyze` uses no-retention endpoints
- ✅ **Automated security**: CodeQL · Dependabot · pip-audit · safety · osv-scanner · gitleaks
- ✅ **Branch protection** on `main` + required CI + secret push protection
- ✅ **Private repo access** via PAT — used in memory once, never stored

Vulnerability reports: see [SECURITY.md](SECURITY.md) — 48h response SLA.

---

## Why OSS?

Being open-source is a **security feature**, not a risk. Every line of code is auditable. No hidden backdoors. Same philosophy as Signal and libsignal: transparency *is* trust.

---

## License

[Apache License 2.0](LICENSE) — Copyright 2026 Takayuki Miyano / Atlas Associates

---

<div align="center">

**Powered by Due Diligence Engine — Takayuki Miyano / Atlas Associates**

</div>
