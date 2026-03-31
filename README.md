<div align="center">

# Due Diligence Engine

**3 AIs Cross-Validate. One Verdict You Can Trust.**

Why rely on a single AI's opinion? DDE runs Claude, Gemini, and ChatGPT **in parallel** — each evaluates independently, then cross-verifies to produce a unified, bias-resistant investment score.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![AI](https://img.shields.io/badge/AI-Claude_%7C_Gemini_%7C_ChatGPT-orange.svg)](https://github.com/taka-avantgarde/due-diligence-engine)

[English](README.md) | [日本語](README.ja.md)

</div>

---

## Multi-AI Cross-Verification

```
         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
         │   Claude     │  │   Gemini    │  │  ChatGPT    │
         │  (Anthropic) │  │  (Google)   │  │  (OpenAI)   │
         └──────┬───────┘  └──────┬──────┘  └──────┬──────┘
                │                 │                 │
                └────────┬────────┴────────┬────────┘
                   ┌─────▼─────────────────▼─────┐
                   │   Cross-Verification Engine  │
                   │   + Site Credibility Check   │
                   └──────────────┬───────────────┘
                         ┌────────▼────────┐
                         │  Unified Score   │
                         │  + Credibility   │
                         └─────────────────┘
```

---

## Try It Now

**https://due-diligence-engine.web.app/dashboard/**

Paste any public GitHub URL and click Analyze.

> Basic analysis (local code scan) is free. For AI-powered analysis, configure your own API keys — **BYOK (Bring Your Own Key)**.

---

## Pricing

| Plan | Cost | AI Providers | Features |
|------|------|-------------|----------|
| **Free (Local Only)** | Free | None | Code structure, git forensics, dependency scan |
| **BYOK** | Free (API costs billed to you) | Claude / Gemini / ChatGPT (1–3 providers) | Full AI analysis + cross-verification |

> **BYOK (Bring Your Own Key):** One API key is enough to start. Claude, Gemini, and ChatGPT are all supported. Add more providers for cross-verification. Typical cost: ~$10–15/analysis depending on codebase size.

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-AI Cross-Verification** | Claude + Gemini + ChatGPT evaluate independently, then cross-verify |
| **BYOK (Bring Your Own Key)** | Use your own API keys — Claude, Gemini, or ChatGPT. 1 provider or all 3. No vendor lock-in |
| **GitHub Private Repo Access** | PAT-based access — startups grant temporary read-only access |
| **AI-Washing Detection** | Detect thin API wrappers disguised as "proprietary AI" |
| **Git Forensics** | Analyze commit history for suspicious patterns (rush commits before DD) |
| **10-Level Tech Rating** | Each dimension rated Lv.1–10 with clear criteria |
| **PDF Export** | Professional investment committee-ready PDF reports |
| **Disconnect & Purge** | One-click data erasure + purge certificate |
| **Bilingual Dashboard** | English / 日本語 toggle |

---

## Scoring Framework

### Final Score Formula

```
Final Score = Heuristic (30%) + AI Average (70%)
```

### Score Barometer

```
  0          40          60          75          90        100
  |----------|-----------|-----------|-----------|----------|
  F          D           C           B           A
  Do Not    High Risk   Concerns    Viable      Strong
  Invest               Noted      w/Conditions Candidate
```

| Score | Grade | Recommendation |
|-------|-------|----------------|
| 90–100 | 🏆 **A** | Strong investment candidate |
| 75–89  | ✅ **B** | Viable with conditions |
| 60–74  | ⚡ **C** | Significant concerns — review required |
| 40–59  | ⚠️ **D** | High risk |
| 0–39   | 🚫 **F** | Do not invest |

---

### 6 Dimensions

| Dimension | Weight | What It Detects |
|-----------|--------|----------------|
| Technical Originality | 25% | API wrapper vs. genuine IP |
| Technology Advancement | 20% | Stack modernity |
| Implementation Depth | 20% | PoC vs. production |
| Architecture Quality | 15% | Structure quality |
| Claim Consistency | 10% | Pitch vs. reality |
| Security Posture | 10% | Security maturity |

---

### 10-Level Tech Rating

Each dimension is rated on a **Lv.1–10** scale with explicit criteria:

```
Lv.1 ──── Lv.2 ──── Lv.3 ──── Lv.4 ──── Lv.5 ──── Lv.6 ──── Lv.7 ──── Lv.8 ──── Lv.9 ──── Lv.10
 ▓          ▓▓         ▓▓▓        ▓▓▓▓       ▓▓▓▓▓      ▓▓▓▓▓▓     ▓▓▓▓▓▓▓    ▓▓▓▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓
Worst                                       Baseline                                                  Best
```

| Level | Technical Originality | Implementation Depth | Architecture Quality |
|-------|-----------------------|---------------------|---------------------|
| Lv.1  | Pure copy / no original code | UI mockup only | Spaghetti code |
| Lv.3  | Multi-API glue logic | Working prototype | Basic layering |
| Lv.5  | Extended framework + partial IP | Beta — basic tests | Clean separation |
| Lv.7  | Core tech fully original | Production-grade + monitoring | Microservices |
| Lv.10 | Frontier / world-first | Mission-critical, DR complete | Distributed systems |

---

### Example Output — "NeuralPay" (Fintech AI startup)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DUE DILIGENCE ENGINE  ·  NeuralPay / neuralpay/core-api
  Analyzed by: Claude + Gemini + ChatGPT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  OVERALL SCORE                          GRADE
  ┌────────────────────────────┐         ┌───────┐
  │  ████████████████░░░░  78  │         │   B   │
  └────────────────────────────┘         └───────┘
  ▲ Viable with conditions

  Score Barometer:
  0          40          60         [75]        90        100
  |----------|-----------|-----------|----●------|----------|
  F          D           C           B           A
                                     ^here

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  6-DIMENSION BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Technical Originality   (25%)   Lv.7 / 10
  ████████████████████░░░░░░░░░░  72   ← Custom ML model, not a wrapper

  Technology Advancement  (20%)   Lv.8 / 10
  ████████████████████████░░░░░░  84   ← Rust + TypeScript, modern stack

  Implementation Depth    (20%)   Lv.6 / 10
  ██████████████████░░░░░░░░░░░░  61   ← Beta-level; tests present but thin

  Architecture Quality    (15%)   Lv.7 / 10
  ████████████████████░░░░░░░░░░  73   ← Clean micro-services, some gaps

  Claim Consistency       (10%)   Lv.5 / 10
  ██████████████░░░░░░░░░░░░░░░░  54   ⚠ "SOC2" claimed, no evidence in code

  Security Posture        (10%)   Lv.6 / 10
  ██████████████████░░░░░░░░░░░░  62   ← TLS everywhere, but no pen-test docs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AI PROVIDER SCORES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Claude   (Anthropic)  ████████████████████░░░░░░  80
  Gemini   (Google)     ███████████████████░░░░░░░░  77
  ChatGPT  (OpenAI)     ████████████████████░░░░░░░  79
  ─────────────────────────────────────────────────────
  AI Consensus                                    78.7  ✓ High agreement

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RED FLAGS (2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ⚠️  [MEDIUM] Compliance claim mismatch
      Pitch deck: "SOC2 Type II certified"
      Codebase:   No audit logs, no compliance tooling found

  ⚠️  [LOW]    Git forensics: 40% of commits in final 2 weeks before DD
      Pattern suggests rushed cleanup prior to investor review

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✅ B — Viable with conditions
  Technology stack and core ML model are genuinely original.
  Resolve SOC2 claim discrepancy and address test coverage
  before proceeding to term sheet.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Quick Start

```bash
git clone https://github.com/taka-avantgarde/due-diligence-engine.git
cd due-diligence-engine
pip install -e .
```

### Configuration

```bash
# AI Providers (configure 1, 2, or all 3)
export ANTHROPIC_API_KEY="sk-ant-..."     # Claude
export GOOGLE_AI_API_KEY="AIza..."        # Gemini
export OPENAI_API_KEY="sk-..."            # ChatGPT

# Optional: GitHub OAuth for private repo access
export GITHUB_CLIENT_ID="your-github-oauth-app-id"
export GITHUB_CLIENT_SECRET="your-github-oauth-app-secret"
```

### CLI Usage

```bash
# Analyze from GitHub URL
dde analyze https://github.com/some-startup/their-product

# Local-only (free, no AI)
dde analyze some-startup/repo --skip-ai
```

### Web Dashboard

```bash
dde serve
# Open http://localhost:8000/dashboard/
```

---

## Use from Your AI Terminal (Claude Code, Cursor, etc.)

Already using AI in your IDE? You can run DDE analysis on your own project by pasting a single prompt into your AI terminal.

### 1. Setup (one-time)

Paste this into your AI terminal:

```
Clone https://github.com/taka-avantgarde/Due-diligence-engine and install it with `pip install -e .`
```

### 2. Analyze Your Project

Then, from your project directory, paste:

```
Run `dde analyze .` to perform a technical due diligence analysis on this project.
```

Or analyze any public GitHub repo:

```
Run `dde analyze owner/repo` to perform a due diligence analysis.
```

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Your IDE (VS Code / JetBrains / etc.)                  │
│                                                         │
│  ┌─────────────────────────────────┐                    │
│  │  AI Terminal                    │                    │
│  │  (Claude Code / Cursor / etc.)  │                    │
│  │                                 │                    │
│  │  > "Analyze this project        │                    │
│  │     with DDE"                   │                    │
│  │                                 │  ┌──────────────┐  │
│  │  AI reads your codebase ────────┼─▶│ DDE Engine   │  │
│  │  and runs dde analyze .         │  │ (local CLI)  │  │
│  │                                 │  └──────┬───────┘  │
│  │  ◀── Scores, red flags, ────────┼─────────┘          │
│  │      recommendations            │                    │
│  └─────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

> **Your API keys are used directly** — BYOK (Bring Your Own Key). DDE uses whichever AI provider keys you have set (`ANTHROPIC_API_KEY`, `GOOGLE_AI_API_KEY`, `OPENAI_API_KEY`). No additional cost beyond your existing API usage. Use `--skip-ai` for free local-only analysis.

---

## Private Repository Access (PAT)

For private repos, provide a **GitHub Personal Access Token**:

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token → check **`repo`** scope → set 7-day expiration
3. Copy the token (`ghp_...`) and paste it into the dashboard

**Security:** PAT is used once in-memory for `git clone`, then immediately discarded. Never stored.

---


## Data Security

| Guarantee | Implementation |
|-----------|---------------|
| No cloud storage | All data processed in encrypted tmpfs |
| No raw code in reports | PDF contains findings only, never source code |
| Cryptographic erasure | 3-pass random overwrite + purge certificate |
| API 0-day retention | Anthropic / Google / OpenAI API calls — no data retention |

---

## Deployment

| Option | Cost | Description |
|--------|------|-------------|
| Local CLI | Free | `dde analyze owner/repo --skip-ai` |
| BYOK CLI | Free + API costs | Your own API keys, full AI analysis |
| BYOK Dashboard | Free + API costs | Web UI with GitHub PAT support |

---

## Roadmap

- [x] Multi-AI analysis engine (Claude / Gemini / ChatGPT BYOK)
- [x] BYOK API key input on web dashboard
- [x] Provider score comparison (per-provider breakdown)
- [x] Bilingual dashboard (English / 日本語)
- [x] PDF report export
- [x] Disconnect & Purge with certificate
- [ ] Technical Debt + Maintainability axes
- [ ] Batch analysis mode (portfolio-wide DD)
- [ ] Historical tracking (re-analyze over time)

---

## Disclaimer

This tool provides **technical analysis to assist investment decisions**. It is not investment advice. Always consult qualified professionals for investment decisions.

---

## License

[Apache License 2.0](LICENSE)

---

<div align="center">

**Powered by Claude (Anthropic) + Gemini (Google) + ChatGPT (OpenAI)**

</div>
