<div align="center">

| 🇬🇧 [![English](https://img.shields.io/badge/English-5271FF?style=for-the-badge)](README.md) | 🇯🇵 [![日本語](https://img.shields.io/badge/%E6%97%A5%E6%9C%AC%E8%AA%9E-30363D?style=for-the-badge)](README.ja.md) | 🇪🇸 [![Español](https://img.shields.io/badge/Espa%C3%B1ol-30363D?style=for-the-badge)](README.es.md) | 🇸🇦 [![العربية](https://img.shields.io/badge/%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-30363D?style=for-the-badge)](README.ar.md) | 🇫🇷 [![Français](https://img.shields.io/badge/Fran%C3%A7ais-30363D?style=for-the-badge)](README.fr.md) | 🇩🇪 [![Deutsch](https://img.shields.io/badge/Deutsch-30363D?style=for-the-badge)](README.de.md) |
|:--:|:--:|:--:|:--:|:--:|:--:|

<sub>👆 Click your language to switch ・ クリックで言語を切り替え</sub>

<sub>🪟 **On Windows:** fully supported & CI-tested (Git required on PATH). Since v0.5.0 the secure temp dir is ACL-locked to the current user natively — WSL2 is optional.</sub>

---

# 🔍 Due Diligence Engine

### **Your IDE's AI → World-Class Tech DD Analyst**

<sub>**Zero API keys · PDF-first · OSS · CodeQL-audited**</sub>

<br/>

```
┌─────────────────────────────────────────────────────────────┐
│  $ dde prompt --pdf                                         │
│                                                             │
│  🌐 Live web research (2026 competitors, funding, CVEs)...  │
│  Reading codebase...                                        │
│  Evaluating across 5 dimensions (equal 20% weights)...      │
│  Building competitive landscape (7 charts × 6 markets)...   │
│  Researching implementation matrix (30 items × 10 cos.)...  │
│  Writing competitor selection rationales (with sources)...  │
│                                                             │
│  Score:  [■■■■■■■■■■■■■■■■■■■■■■■■■■□□□□] 82/100  Lv.8     │
│  Grade:  B  →  Viable with conditions                       │
│                                                             │
│  → ~/Downloads/dde_consulting_<project>_<date>.pdf  (24 p.) │
└─────────────────────────────────────────────────────────────┘
```

<br/>

[![License](https://img.shields.io/badge/License-Apache_2.0-000000.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-5271FF.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![CodeQL](https://img.shields.io/badge/Security-CodeQL_·_Dependabot_·_pip--audit-5271FF.svg?style=for-the-badge&logo=github&logoColor=white)](SECURITY.md)
[![PDF](https://img.shields.io/badge/Output-PDF_First-000000.svg?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](#)

[![GitHub stars](https://img.shields.io/github/stars/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=5271FF)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=000000)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Atlas-Associates-Inc/Due-diligence-engine?style=flat-square&color=5271FF)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/commits/main)
[![Version](https://img.shields.io/badge/version-v0.6.1-000000?style=flat-square)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/releases)

[![Repo Views](https://komarev.com/ghpvc/?username=taka-avantgarde&repo=Due-diligence-engine&color=5271FF&style=flat-square&label=Repo+Views)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine)

</div>

---

## ⚡ Quick Start

**Install once:**

```bash
python3 -m pip install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

**Run from your project directory:**

```bash
dde prompt --pdf
```

Use any AI-powered IDE terminal (Claude Code / Cursor / Copilot). Your AI reads the codebase, evaluates it as a world-class technology consultant, and writes a 24-page PDF to `~/Downloads/`. **No API keys. No cloud. No extra cost.**

<details>
<summary><sub>Other install options · macOS Homebrew note</sub></summary>

Linux / venv / older macOS short form:
```bash
pip3 install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

macOS Homebrew users: use `python3 -m pip` — the bare `pip` command is no longer installed by Homebrew Python 3.12+.

</details>

---

## 💭 How to Get the Best Results

> **TL;DR**: Launch the highest-tier AI you have access to in your IDE terminal,
> paste the command, and wait 10-20 minutes. That's it.

**Recommended setup:**

- **Spin up the most capable model available** in your IDE (Claude Fable 5, GPT-5, Gemini 2.5 Pro, etc.)
- **Paste `dde prompt --pdf`** into the terminal
- **Go grab a coffee** ☕ — the AI will read hundreds of files, evaluate across
  9+ dimensions, research 5-10 competitors globally, and build a 24-page consulting PDF
- **Expected time**: **10-20 minutes** (longer for large codebases or deeper models)

**Why this approach?**

| Concern | Answer |
|---------|--------|
| 🔐 **Data leakage?** | None. Everything runs inside your IDE's AI sandbox — no 3rd-party servers, no telemetry. DDE itself is 100% local Python |
| 💰 **Cost?** | $0 extra. Uses your existing IDE AI subscription |
| 🔑 **API keys?** | Not needed. Your IDE already handles AI auth |
| ⚙️ **Setup?** | Just `python3 -m pip install`. No config, no accounts |
| 🎁 **Catch?** | There isn't one. DDE is a **hobby project** — built and open-sourced for fun. Use it freely |

> **Made by a solo dev as a hobby.** If it helps you, that's enough reward. Star the repo if you like it ⭐

---

## 💻 Where Does DDE Run — Use the AI You Already Have

DDE generates a structured prompt. **Any AI agent that can read files and execute shell commands** can run it. No DDE-specific integration, plugin, or login required.

**Verified working** (official docs + tested, 2026-05):
- ✅ [**Claude Code**](https://code.claude.com/docs/en/overview) (CLI / VS Code / JetBrains / Desktop / Web — Anthropic official)
- ✅ [**GitHub Copilot Agent Mode**](https://docs.github.com/en/copilot/using-github-copilot/copilot-chat/asking-github-copilot-questions-in-your-ide) (VS Code / Visual Studio / JetBrains / Xcode / Eclipse — generally available)

**Should work** (requirements: file read + shell exec + ideally web search):
- Cursor Agent, Gemini Code Assist, Continue.dev, Cody (Sourcegraph), Aider, Windsurf, Amazon Q Developer, JetBrains AI Assistant, and similar agentic terminals.

> ✅ If you already use any of the above, you're one `pip install` away from running DDE today.
> Confirmed a specific terminal works? Let us know in an [issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues).

### 💰 Zero added cost

**You only pay for the AI subscription you already have.** Claude Code Pro / GitHub Copilot / Cursor Pro / Gemini Advanced — DDE runs inside your existing AI's allowance. No DDE pricing tiers, no extra API keys, no hidden fees, ever.

---

## 👥 Who Is This For?

| User | Use Case | Time Saved |
|------|----------|-----------|
| **VC Tech Partners** | Pre-investment technical DD on portfolio candidates | 2-5 days → 30 min |
| **CTOs / Engineering Leads** | Internal tech audit before board meetings | 1 week → 1 hour |
| **M&A Technical Advisors** | Due diligence on acquisition targets | 1-2 weeks → 1 day |
| **Independent DD Consultants** | Boutique firm tech evaluations | scale: 1→10 clients/week |
| **Founders** | Self-assessment before fundraising | objective view of own codebase |
| **Corporate Innovation** | Vendor / startup partnership evaluation | ad-hoc → systematic |

> Built for engineers and technical decision-makers who already use AI in their daily workflow.

---

## 🆚 vs. Other Tools

|   | DDE | Manual DD | Generic AI Code Review | SaaS DD Platforms |
|---|:---:|:---:|:---:|:---:|
| **Cost** | $0 (uses your IDE AI) | $$$$ (consultant fees) | API fees | $$$$ (subscription) |
| **Privacy** | Local-only | Local | Sends code to vendor | Sends code to vendor |
| **Output** | 24-page consulting PDF | Custom report | Inline comments | Web dashboard |
| **Data Freshness** | ✅ Live web search (2026) + source URLs | Depends on analyst | Training-data only (stale) | Vendor-controlled refresh |
| **Crypto Depth** | PQXDH / Signal Protocol level | Depends on consultant | Generic | Generic |
| **Competitive Charts** | 7 + Implementation Matrix | Manual research | None | Limited |
| **Setup Time** | 1 command | Weeks | Minutes | Days (account/onboarding) |
| **Customization** | Full source access | Yes | Limited | Vendor-locked |

---

## What Makes DDE Different

Most "AI code reviewers" check:
> *"Does it have authentication? ✓ Does it have HTTPS? ✓ Does it have tests? ✓"*

That's checkbox compliance. **DDE goes deeper:**

> *"Is the encryption Signal Protocol? Is it PQXDH with ML-KEM-1024?
> Is it built on libsignal/BoringSSL FFI, or self-rolled crypto?
> Does the team publish cryptographic research?"*

Built on the **Atlas Engineering Philosophy**: serious cybersecurity engineering
across encryption, privacy, communications, and layered defense — read directly
from the source code. Checkbox compliance (SOC2, MFA, WebAuthn certifications)
is reference-only, never scored.

**🌐 New in v0.3.2**: Before reading any code, the AI runs **live web searches** for the latest competitor landscape (acquisitions, shutdowns, new entrants), 2026 funding rounds, recent CVEs, and regulatory shifts. Every competitor and every implementation-matrix cell carries a **source URL + verification date**, and the JSON output starts with a `data_freshness` block that tracks every search query. **Training-cutoff-only stale analysis is structurally eliminated.** **(v0.5.0)** This provenance is now surfaced directly in the PDF — a data-provenance box on the score dashboard shows the search date and query/source counts, or a clearly marked training-data-only warning when web research did not run.

---

## 🔒 Atlas Engineering Philosophy (cybersecurity-focused parallel view)

A parallel evaluation system added alongside the standard 5-dimension scoring.

```
4 axes — weights sum to 100%

  Performance        20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  Stability          20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  Lightweight         5%  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  Security Strength 55%  ███████████████████████████░░░░░  ← THE CORE

  Cybersecurity sub-breakdown (within 55% — defense across all layers):
    Cryptographic Sophistication  35%  ← largest: Signal Protocol, PQXDH, libsignal
    Privacy Protection             8%
    Communication Safety           7%
    Layer Composition              3%
    Basic Hygiene (MFA/WebAuthn)   2%  ← code-only; certs are reference-only
```

---

## 📊 5-Dimension Standard Scoring (v0.3 — balanced, equal weights)

| Dimension | Weight | What It Detects |
|-----------|-------:|-----------------|
| Technical Originality | 20% | API wrapper vs. genuine IP |
| Technology Advancement | 20% | Stack modernity |
| Implementation Depth | 20% | PoC vs. production |
| Architecture Quality (incl. Security Posture) | 20% | Structure quality + security maturity |
| Claim Consistency | 20% | Pitch vs. reality |

> **Final Score** = Heuristic Analysis (30%) + AI Average Score (70%)

> **v0.3 change**: Security Posture was merged into Architecture Quality. Security is now evaluated as an integral part of production-grade architecture, not a separate silo.

```
Grade Bands:

  0      40       60      75       90     100
  |------|--------|-------|--------|------|
   F      D        C       B        A
   ✗      ⚠        ⚡       ✓        ★
```

| Grade | Recommendation |
|-------|----------------|
| ★ A (90+)  | Strong investment candidate |
| ✓ B (75-89)| Viable with conditions |
| ⚡ C (60-74)| Significant concerns |
| ⚠ D (40-59) | High risk |
| ✗ F (<40)  | Do not invest |

Each dimension also rated **Lv.1-10** with explicit criteria.

---

## 🎯 7 Competitive Charts × 6 Markets

For each of 6 global markets (Global / US / EMEA / Japan / SEA / LATAM):

| # | Chart | What It Shows |
|---|-------|---------------|
| 1 | **Forrester Wave / Magic Quadrant** | Vision × Execution |
| 2 | **BCG Growth-Share Matrix** | Market growth × Relative share |
| 3 | **McKinsey Tech Moat** | Competitive position × Technical moat |
| 4 | **Security & Privacy Maturity** | Security implementation × Privacy readiness |
| 5 | **Data Governance & Transparency** | Data protection × Audit transparency |
| 6 | **GS Risk-Adjusted Return** | Downside risk × Upside potential |
| 7 | **Innovation vs. Commercialization** | R&D velocity × ARR traction (3D bubble) |

**6-16 competitors per chart** with axis rationale captions explaining
*why* each axis matters and *what* the composite score captures.

---

## 🆕 Implementation Capability Matrix

The 8th competitive chart — **~30 items × 5-10 top global competitors**:

```
                        Target   Comp. A   Comp. B   Comp. C   Comp. D   ...
Encryption (core differentiator)
  Feature 1              ○        ○         ×         △         ○
  Feature 2              ○        ○         ×         ×         ○
  Feature 3              ○        ○         ○         ×         ○
  Feature 4              ○        ×         ×         △         △
  ...
Privacy & Compliance
  Feature 1              ○        △         ○         ×         △
  Feature 2              ○        ○         △         ×         ×
  ...
```

Items and competitors are **chosen dynamically per target's industry**
(messaging, fintech, medical, gaming, SaaS, IoT, etc.).

4-state marking (Japanese tech rating standard):
- **○ verified** (publicly documented implementation)
- **△ claimed** (asserted, not verifiable)
- **× not implemented** (explicitly absent)
- **? unknown** (cannot determine — preferred over guessing)

Plus **competitor selection rationales** — 3-5 lines each explaining why each
specific competitor was chosen as a comparison target (HQ, market position, category).

---

## 📄 What's in the 24-Page PDF

| # | Section | Content |
|---|---------|---------|
| 1 | Cover | Black + Arc sky (#5271FF) accent, project name, score, grade |
| 2 | Score Dashboard | **5-dim** horizontal bars (20% each) + score barometer + **5-dim radar chart** + **data-provenance box** (search date / query & source counts, or a training-data-only warning) |
| 3 | Executive Summary | Business + technical summary |
| 4 | SWOT Analysis | 2×2 visual grid with evidence + business analogies |
| 5 | Score Breakdown | Per-dimension rationale & enablers |
| 6 | Tech Level Assessment | **5-dim** Lv.1-10 bar chart + overall gauge |
| 7 | Future Outlook | 1/3/5-year projections with confidence |
| 8 | Strategic Advice | Immediate, medium, long-term |
| 9 | Investment Thesis | Recommendation, risks, upside, comparables |
| 10 | Red Flags | Severity-rated (Critical/High/Medium/Low) |
| 11 | Site Verification | 10-item technical capability audit (4 claim-vs-code + 6 code-measured) |
| 12-14 | Competitive Analysis | 7 charts × 6 markets with axis rationale |
| 15 | **🆕 Competitor Selection Rationales** | 3-5 line explanation per competitor (why chosen, HQ, position) |
| 16 | **Implementation Capability Matrix** | ~30 items × top competitors, ○△×? marking |
| 17 | **Atlas 4-Axis Dashboard** | Performance / Stability / Lightweight / Security Strength |
| 18 | **Security Sub-Breakdown + Glossary** | 5 sub-items with non-engineer glossary (MFA/SOC2/libsignal/PQXDH…) |
| 19-24 | Glossary · Consistency · Cost · Purge Cert | Standard appendix sections |

---

## 🛠️ Usage

> 🌍 **Report languages (14):** `en` `ja` `es` `fr` `de` `pt` `nl` `it` `id` `zh` `ko` `vi` `th` `ar` — e.g. `dde prompt --pdf --lang es`. Arabic renders with RTL contextual shaping (page layout stays LTR).

```bash
# Current directory, English PDF
dde prompt --pdf

# Japanese PDF
dde prompt --pdf --lang ja

# GitHub repo with stage context
dde prompt owner/repo --pdf --lang ja --stage seed

# Check your environment is ready (git, fonts, reportlab, ~/Downloads, AI SDKs)
dde doctor

# Non-interactive (for AI terminals without prompt support)
dde prompt --pdf --lang ja \
  --url https://example.com \
  --url https://docs.example.com

# Direct BYOK multi-AI cross-verification (optional — needs the [byok] extra)
pip install "due-diligence-engine[byok]"
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_AI_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
dde analyze owner/repo
```

---

## 🔐 Security & OSS Philosophy

| Guarantee | Implementation |
|-----------|----------------|
| **Local-only processing** | `dde prompt` never sends data anywhere |
| **No source code in reports** | PDFs contain findings only |
| **API 0-day retention** | `dde analyze` uses no-retention endpoints |
| **Automated security CI** | CodeQL · Dependabot · pip-audit · safety · osv-scanner · GitHub Secret Scanning |
| **Branch protection** | `main` requires PR + CI + secret push protection |
| **Private repo access via PAT** | Used in memory once, never stored |

Vulnerability reports: see [SECURITY.md](SECURITY.md) — 48h response SLA.

### Why OSS is a security feature, not a risk

Open-source means every line is auditable. No hidden backdoors. No black-box scoring.
This is the same philosophy as Signal and libsignal: **transparency *is* trust**.

---

## ❓ FAQ

**Q: Does DDE send my code anywhere?**
A: No. `dde prompt` runs entirely locally — it generates a structured prompt that your IDE's AI reads. The AI evaluates the code in-place. The optional `dde analyze` (BYOK) sends to AI providers using their no-retention endpoints only.

**Q: Why is it free? What's the catch?**
A: There is no catch. DDE is OSS (Apache 2.0) and uses your existing IDE AI subscription (Claude Code / Cursor / Copilot). No telemetry, no upsell.

**Q: Can I use it in CI?**
A: Yes — see [`action.yml`](action.yml). Add the GitHub Action to PRs for automated DD scoring.

**Q: How accurate are the competitive charts?**
A: Charts are AI-researched from public sources (whitepapers, GitHub, blogs, SOC2 reports). Confidence depends on competitor transparency. Use `?` (unknown) liberally — false positives damage credibility more than gaps.

**Q: Isn't competitor data stale? AI training cutoffs are 6-12 months old.**
A: As of v0.3.2, **STEP 0 "Live Web Research" is mandatory**. Before reading any code, the AI runs WebSearch / WebFetch for 2025-2026 competitor moves (acquisitions, shutdowns, new entrants), latest funding rounds, CVEs, and regulatory shifts. Every competitor and matrix cell carries a `sources` (URL) and `last_verified` (date) field, and the JSON output starts with a `data_freshness` block that tracks every search query executed. When the runtime lacks web search tools, the AI MUST write a `data_cutoff_warning` — **no silent stale output by design**.

**Q: Why "Atlas Engineering Philosophy"?**
A: DDE is built by **Atlas Associates Inc**, the company behind Arc Messenger (E2EE messaging with libsignal + PQXDH). The 4-axis evaluation reflects what we actually look for when evaluating tech.

**Q: Can I customize the scoring weights?**
A: The 5-dimension weights are equal 20% each (balanced, simple, interpretable). Atlas 4-axis weights (20/20/5/55) reflect Atlas philosophy and are also fixed. Sub-item weights within Security Strength adjust by industry context.

**Q: What if my project isn't security-critical?**
A: The 5-dimension score (Architecture Quality includes Security Posture at a balanced 20%) is your primary score. The Atlas 4-axis is a parallel reference view — both are shown.

**Q: I get `command not found: pip` — how do I install?**
A: Use `python3 -m pip install ...` instead. macOS Homebrew Python 3.12+ no longer ships a bare `pip` command. The `python3 -m pip` form works on all platforms (macOS / Linux / Windows / venv / pyenv / conda).

**Q: Why don't third-party certifications (SOC2, ISO, HIPAA) affect the score?**
A: DDE evaluates the source code, not the badge. A SOC2-certified plaintext-storage service still has plaintext storage. An uncertified libsignal+PQXDH service is still cryptographically strong. Certifications are shown for context but never scored — see the Security Sub-Breakdown page.

---

## 🗺️ Roadmap

**Recently shipped (v0.3.x)**
- ✅ **Package renamed `src` → `due_diligence_engine`** (2026-07, v0.6.1): the importable package no longer uses the generic top-level name `src`, avoiding `sys.path` collisions once pip-installed. The `dde` command is unchanged; only `import` paths change (`from due_diligence_engine...`).
- ✅ **PyPI-ready packaging, `dde doctor`, visual-summary page & source appendix** (2026-07, v0.6.0): AI-provider SDKs moved to an optional `[byok]` extra so the base install is truly zero-API-key (fixes a bug where `dde prompt` crashed when `anthropic` was absent); new `dde doctor` environment self-check; the radar chart now gets its own **Visual Summary** page and a new **Source Appendix** lists every live-web URL consulted (14 languages); a real security fix so archive loading no longer leaves a plaintext staging copy on disk; first tests for the secure-loader/secure-purge modules; CI matrix extended to macOS + Windows 3.12 with coverage. Distribution stays via the documented `git+https` install; a PyPI release was evaluated and deferred.
- ✅ **Radar chart + data provenance + Windows hardening** (2026-07, v0.5.0): 5-dimension radar (spider) chart on the score dashboard; STEP 0 web-research provenance box in the PDF (search date, query/source counts, or a clearly marked training-data-only warning); Windows NTFS ACL lock for the secure temp dir (`icacls`, owner-only); Windows added to the CI test matrix
- ✅ **14-language PDF reports** (2026-06, v0.4.0): the consulting PDF generates in any of 14 languages via `--lang` — English / 日本語 / Español / Français / Deutsch / Português / Nederlands / Italiano / Bahasa Indonesia / 简体中文 / 한국어 / Tiếng Việt / ไทย / العربية (Arabic with RTL contextual shaping). Bundled Noto fonts, no setup.
- ✅ **Windows compatibility fixes** (2026-06, v0.3.8): cross-platform temp path for the `--pdf` consulting flow (was a hardcoded `/tmp`) and Windows clipboard support (`clip`) for `--copy`
- ✅ **6-language READMEs** (2026-06, v0.3.7): top-of-page language switcher with the active language highlighted — English / 日本語 / Español / العربية / Français / Deutsch, each a separate `README.<lang>.md`
- ✅ **Claude Fable 5 upgrade** (2026-06, v0.3.6): judge tier moved Opus 4.8 → **Fable 5** (`claude-fable-5`, Anthropic's most capable widely released model, GA 2026-06-09). Tier key renamed `opus` → `fable`. Pricing $10/$50 per MTok (2× Opus 4.8, prioritizing final-verdict quality)
- ✅ **PDF chart polish + label overlap fix** (2026-05, v0.3.5): all bars across Score Dashboard / Tech Level / Competitive / Matrix charts redesigned as modern rounded pill shapes. Long Japanese labels (e.g. 「アーキテクチャ品質（セキュリティ含む）」) that overlapped the bars are fixed by widening the label area (verified by rendering + visually inspecting each PDF page)
- ✅ **Claude Opus 4.8 upgrade** (2026-05, v0.3.3–4): judge tier moved Opus 4.7→4.8 (Sonnet 4.6 / Haiku 4.5 also refreshed). Avoids the 2026-06-15 retirement of legacy Opus 4 / Sonnet 4 (20250514) and reflects the Opus price drop ($15→$5 input)
- ✅ **Transfer to Atlas-Associates-Inc org** (2026-05, v0.3.4–5): repo moved taka-avantgarde → Atlas-Associates-Inc. All URLs updated, author credit unified to Takayuki Miyano (@taka-avantgarde) + Atlas Associates Inc, gitleaks → GitHub native Secret Scanning
- ✅ **Live Web Research mandate** (2026-05, STEP 0): added `_WEB_RESEARCH_MANDATE` to the top of every consulting prompt — AI MUST run WebSearch/WebFetch on competitor landscape, funding, tech trends, CVEs, and regulation **before** reading code. JSON output now includes a `data_freshness` block (search date, queries executed, sources consulted) plus per-competitor and per-matrix-cell `sources` / `last_verified` fields. Eliminates training-cutoff-only stale analysis
- ✅ **Prompt typo fixes**: "6 dimensions" → "5 dimensions" and "5つのチャート" → "7つのチャート" in JA consulting prompt
- ✅ **CI Self-Test fix** (2026-05): `action.yml`'s `grep -c` returned exit code 1 on zero matches, which `set -e` + `pipefail` propagated as a job failure. Fixed with `|| FALLBACK="0"` pattern. **DDE Self-Test now green for the first time**
- ✅ **Scoring formula made explicit in README** (Final Score = Heuristic 30% + AI Average 70%)
- ✅ **Dependabot fully wired**: created `dependencies` / `security` / `ci` labels and merged PR #23 (checkout v6) / #24 (upload-artifact v7) / #25 (osv-scanner-action v2.3.8)
- ✅ **Anti-self-bias guardrails**: explicit "the target is NOT DDE itself" warnings in prompt header (prevents AI confusion when DDE is run on another project)
- ✅ **Red flags clarified**: shown as actionable items for code improvement (NOT factored into score)
- ✅ **Quick Start simplified** in README (single install command + collapsible alternatives)
- ✅ **Atlas philosophy reframed** as "cybersecurity defense overall" (not just encryption — encryption is the largest sub-weight at 35%)
- ✅ **Site Verification refocused to pure technical capability** (10 items: 4 claim-vs-code + 6 code-measured — crypto depth, concurrency model, I/O pattern, caching, scalability, ML depth)
- ✅ Atlas weights rebalanced to **20 / 20 / 5 / 55** (encryption core bumped to 35%)
- ✅ **Source-code-only evaluation**: third-party certs (SOC2 / ISO / HIPAA) are reference-only, not scored
- ✅ **Competitor 1:1 alignment** between matrix and rationales (estimated score per competitor + public-info disclaimer)
- ✅ 5-dimension scoring (equal 20% weights, Security merged into Architecture)
- ✅ Competitor Selection Rationales (3-5 line explanation per competitor)
- ✅ Non-engineer glossary on Security Sub-Breakdown page (MFA/SOC2/libsignal/PQXDH)
- ✅ AIDD-era stance: no penalty for AI usage or high-velocity commits
- ✅ `python3 -m pip` guide + visitor counter badges
- ✅ PDF layout fixes: KeepTogether, KeepInFrame (SWOT), 2-line wrapped descriptions

**Previously shipped (v0.2.0)**
- ✅ Atlas 4-axis Optimization Assessment (originally 25/20/5/50, now 20/20/5/55)
- ✅ Implementation Capability Matrix (8th competitive chart)
- ✅ Web dashboard fully removed (CLI + PDF only)
- ✅ Black + Arc sky (#5271FF) brand identity
- ✅ Typography system overhaul (leading, hierarchy)
- ✅ Security CI hardening (CodeQL, Dependabot, gitleaks)

**Planned (v0.4.0+)**
- 🚧 Batch mode — analyze a portfolio of repos in one command
- 🚧 Historical tracking — re-analyze and show score deltas over time
- 🚧 Slack/Discord notification adapter
- 🚧 Industry-specific evaluation packs (medical, fintech, gaming presets)
- 🚧 PyPI / Homebrew distribution

Open an [issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues) to suggest features or report bugs.

---

## 🤝 Contributing

Contributions welcome! The codebase is small and well-tested:

```bash
git clone https://github.com/Atlas-Associates-Inc/Due-diligence-engine
cd Due-diligence-engine
python3 -m pip install -e ".[dev]"
pytest
```

- **Bug reports**: please include `dde --version` output and a minimal reproduction
- **Feature requests**: open a GitHub Discussion first to gauge interest
- **Pull requests**: ensure all tests pass + add new tests for new features

---

## 📜 License

[Apache License 2.0](LICENSE) — Copyright © 2026 [Takayuki Miyano](https://github.com/taka-avantgarde) / [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

---

<div align="center">

**Powered by Due Diligence Engine**

Created by [Takayuki Miyano](https://github.com/taka-avantgarde) — [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

`v0.6.1` — 🌍 6-language READMEs · 🆕 Claude Fable 5 / Sonnet 4.6 / Haiku 4.5 · 🌐 Live web research · 5-dimension scoring

</div>
