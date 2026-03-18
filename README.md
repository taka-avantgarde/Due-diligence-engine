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

## Multi-AI Cross-Verification — The Core Advantage

> **One AI can be wrong. Three AIs cross-checking each other dramatically reduce blind spots.**

Traditional AI-powered analysis tools use a single model. That means you inherit that model's biases, training gaps, and blind spots — silently. DDE takes a fundamentally different approach:

```
         ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
         │   Claude     │  │   Gemini    │  │  ChatGPT    │
         │  (Anthropic) │  │  (Google)   │  │  (OpenAI)   │
         └──────┬───────┘  └──────┬──────┘  └──────┬──────┘
                │                 │                 │
                │  Independent    │  Independent    │  Independent
                │  Evaluation     │  Evaluation     │  Evaluation
                │                 │                 │
                └────────┬────────┴────────┬────────┘
                         │                 │
                   ┌─────▼─────────────────▼─────┐
                   │   Cross-Verification Engine  │
                   │   Divergence Detection       │
                   │   Consensus Scoring          │
                   └──────────────┬───────────────┘
                                  │
                         ┌────────▼────────┐
                         │  Unified Score   │
                         │  Heuristic 30%   │
                         │  AI Average 70%  │
                         └─────────────────┘
```

- **Each provider scores independently** — no model sees another's results
- **Divergence detection** — flags dimensions where AIs disagree significantly
- **Consensus scoring** — final score weights agreement across providers
- **Per-provider breakdown** — see exactly where each AI agrees and disagrees

**BYOK (Bring Your Own Key):** Configure 1, 2, or all 3 providers. More providers = higher confidence. Even a single provider gives you AI-powered analysis — adding more activates cross-verification automatically.

---

## Try It Now (No Setup Required)

Want to see how it works before setting up your own API keys? Try our hosted demo:

**https://due-diligence-engine.web.app/dashboard/**

Just paste any public GitHub URL and click Analyze. No API key needed for basic analysis.

> **Note:** The hosted demo performs a **quick preliminary check** (local code analysis only, no AI). For accurate, in-depth AI-powered analysis, please set up your own AI API keys — **Claude** (Anthropic), **Gemini** (Google), and/or **ChatGPT** (OpenAI). You can configure up to 3 AI providers simultaneously for cross-validated results. API costs are billed directly to your account. See [Configuration](#configuration) for BYOK setup.

---

## Pricing

| Plan | Description | Cost |
|------|-------------|------|
| **Free (Local Only)** | Local code analysis (AST, dependency, git forensics). No AI. | Free |
| **BYOK (Bring Your Own Key)** | Your own API keys for up to 3 AI providers. Full cross-verification. | Free (API costs billed to you) |
| **Pro Analysis (Japan)** | Managed Claude + Gemini analysis. No key setup required. | ¥5,000 / analysis (Stripe) |

---

## Just Paste the URL

```bash
dde analyze https://github.com/some-startup/their-product
```

That's it. One command. Full technical due diligence.

### For VCs

```
Step 1: Get the startup's GitHub repo URL
Step 2: dde analyze <URL>
Step 3: Review the scorecard
```

### For Startups (Prove Your Tech)

Add this to your repo — VCs can trigger it anytime:

```yaml
# .github/workflows/dde.yml
name: Technical Due Diligence
on: workflow_dispatch
jobs:
  dd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: taka-avantgarde/due-diligence-engine@main
        with:
          skip_ai: 'true'
```

VCs click **"Run workflow"** on the startup's repo, and get an instant DD report.

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-AI Cross-Verification** | Claude + Gemini + ChatGPT evaluate independently, then cross-verify for bias-resistant scoring |
| **BYOK (Bring Your Own Key)** | Use your own API keys — 1 provider or all 3. No vendor lock-in |
| **GitHub Private Repo Access** | OAuth integration — startups grant temporary access to their private repos |
| **Code Reality Check** | AST analysis to verify AI logic actually exists in the codebase |
| **AI-Washing Detection** | Detect thin API wrappers disguised as "proprietary AI" |
| **Git Forensics** | Analyze commit history for suspicious patterns (rush commits before DD) |
| **Doc-Code Consistency** | Cross-reference technical documents against actual implementation |
| **Architecture Visualization** | Auto-generate Mermaid diagrams of real system architecture |
| **10-Level Tech Rating** | Each dimension rated Lv.1-10 with clear criteria (technology-focused, no team eval) |
| **100-Point Scoring** | Weighted scoring: Heuristic 30% + AI Average 70%, with RED FLAG detection |
| **PDF Export** | Professional investment committee-ready PDF reports |
| **Disconnect & Purge** | One-click GitHub disconnect + cryptographic data erasure + purge certificate |
| **Web Dashboard** | Browser-based UI for non-technical VCs |

---

## Scoring Framework

Technology-focused evaluation only. No team/process assessment.

### 6 Dimensions with 10-Level Rating

| Dimension | Weight | What It Detects |
|-----------|--------|----------------|
| Technical Originality | 25% | API wrapper vs. genuine IP (Lv.1 Copy ... Lv.10 Frontier) |
| Technology Advancement | 20% | Stack modernity (Lv.1 Legacy ... Lv.10 Visionary) |
| Implementation Depth | 20% | PoC vs. production (Lv.1 Mockup ... Lv.10 Mission-Critical) |
| Architecture Quality | 15% | Structure quality (Lv.1 Spaghetti ... Lv.10 Distributed) |
| Claim Consistency | 10% | Pitch vs. reality (Lv.1 Fabricated ... Lv.10 Transparent) |
| Security Posture | 10% | Security maturity (Lv.1 Negligent ... Lv.10 Military-Grade) |

### Final Score Composition

```
Final Score = Heuristic Analysis (30%) + AI Average Score (70%)

AI Average = mean of all configured provider scores
             (Claude, Gemini, ChatGPT — whichever keys are provided)
```

### Grading

| Score | Grade | Recommendation |
|-------|-------|---------------|
| 90-100 | A | Strong investment candidate |
| 75-89 | B | Viable with conditions |
| 60-74 | C | Significant concerns |
| 40-59 | D | High risk |
| 0-39 | F | Do not invest |

---

## Quick Start

### Prerequisites

- Python 3.11+
- At least one AI API key (Claude, Gemini, or ChatGPT) — or none for local-only analysis
- GitHub OAuth App (for private repo access)

### Installation

```bash
git clone https://github.com/taka-avantgarde/due-diligence-engine.git
cd due-diligence-engine
pip install -e .
```

### Configuration

Set up your AI provider API keys. **One key is enough to get started. Add more for cross-verification.**

```bash
# AI Providers (configure 1, 2, or all 3)
export ANTHROPIC_API_KEY="sk-ant-..."     # Claude (Anthropic)
export GOOGLE_AI_API_KEY="AIza..."        # Gemini (Google)
export OPENAI_API_KEY="sk-..."            # ChatGPT (OpenAI)

# Optional: for private repo access via GitHub OAuth
export GITHUB_CLIENT_ID="your-github-oauth-app-id"
export GITHUB_CLIENT_SECRET="your-github-oauth-app-secret"
```

> **How it works:** DDE auto-detects which API keys are present. With 1 key, you get single-provider AI analysis. With 2+ keys, cross-verification activates automatically — no extra configuration needed.

### Private Repository Access — PAT (Personal Access Token)

For private repositories, the startup provides a **GitHub PAT (Personal Access Token)** to DDE.
A PAT is a token string that acts as a password substitute for GitHub API / git operations. DDE supports two types:

---

#### Option A: Classic PAT (Recommended for simplicity)

Classic PATs grant access to **all repositories** the token owner can access. Simple to create but broader scope.

1. Open GitHub → click your **profile icon** (top-right) → **Settings**
2. Left sidebar → scroll down → **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. Click **Generate new token** → **Generate new token (classic)**
5. Configure:

   | Setting | Value |
   |---------|-------|
   | **Note** | `DDE DD Analysis` (any descriptive name) |
   | **Expiration** | `7 days` (recommended — set to match your DD timeline) |
   | **Select scopes** | Check **`repo`** (Full control of private repositories) |

   > Note: The `repo` scope includes both read and write access. DDE only performs `git clone --depth 1` (read-only). The token is used once in-memory and immediately discarded.

6. Click **Generate token**
7. **Copy the token** (`ghp_...`) — it will only be shown once
8. Paste the token into the DDE dashboard "Private repo?" section alongside your repo URL

**Direct link:** [github.com/settings/tokens](https://github.com/settings/tokens)

---

#### Option B: Fine-grained PAT (More secure, per-repo scope)

Fine-grained PATs can be scoped to **specific repositories** with **read-only** permissions. More secure but requires Organization approval for Org repos.

1. Open GitHub → **profile icon** → **Settings**
2. Left sidebar → **Developer settings**
3. **Personal access tokens** → **Fine-grained tokens**
4. Click **Generate new token**
5. Configure:

   | Setting | Value |
   |---------|-------|
   | **Token name** | `DDE DD Analysis` |
   | **Expiration** | `7 days` (recommended) |
   | **Resource owner** | Select the Organization that owns the repo (e.g., `Your-Org`) |
   | **Repository access** | **Only select repositories** → choose the target repo |

6. Expand **Permissions** → **Repository permissions**:

   | Permission | Access level |
   |------------|-------------|
   | **Contents** | **Read-only** |
   | **Metadata** | **Read-only** (auto-selected) |

   > All other permissions should remain **No access**.

7. Click **Generate token**
8. **Copy the token** (`github_pat_...`) — it will only be shown once
9. Paste into the DDE dashboard

**Direct link:** [github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)

**Important for Organization repos:**
- The Org admin must enable Fine-grained PATs: Org Settings → Personal access tokens → **Allow access via fine-grained personal access tokens**
- If "Require administrator approval" is enabled, the admin must approve the token in **Pending requests** before it works

---

#### Which PAT type should I use?

| | Classic PAT (`ghp_...`) | Fine-grained PAT (`github_pat_...`) |
|---|---|---|
| **Ease of setup** | Simple (2 clicks) | More steps required |
| **Repo scope** | All repos you can access | Specific repos only |
| **Permissions** | `repo` = read+write | Contents: Read-only |
| **Org approval** | Not required | May require admin approval |
| **Best for** | Quick DD, personal repos | Org repos, security-conscious startups |

#### Security Guarantee

- Your PAT is **never stored** on DDE servers
- It is used **once in-memory** for `git clone --depth 1`, then immediately discarded
- No credentials are persisted to disk, database, or logs
- All cloned source code is cryptographically erased after analysis (purge certificate provided)

### Usage — CLI

```bash
# Analyze from GitHub URL (just paste the URL!)
dde analyze https://github.com/some-startup/their-repo

# Short form (owner/repo)
dde analyze some-startup/their-repo

# Specific branch
dde analyze https://github.com/some-startup/their-repo/tree/develop

# Local directory
dde analyze /path/to/startup-code

# Zip archive
dde analyze /path/to/startup-code.zip

# With options
dde analyze some-startup/repo --name "Startup X" --format html --format md

# Skip AI (local analysis only, free)
dde analyze some-startup/repo --skip-ai

# View leaderboard (80+ scores only)
dde leaderboard
```

### Usage — Web Dashboard (for Private Repos)

```bash
# Start the web server
dde serve

# Open http://localhost:8000/dashboard/
```

The Web Dashboard provides:
1. **Connect with GitHub** — OAuth flow to access startup's private repos
2. **Configure AI Keys** — Enter your BYOK API keys (Claude / Gemini / ChatGPT)
3. **Select & Analyze** — Choose a repo and run multi-AI analysis
4. **View Results** — Scorecard, per-provider breakdown, RED FLAGS, architecture diagrams
5. **Export PDF** — Download investment committee-ready report
6. **Disconnect & Purge** — Revoke access + cryptographic data erasure

---

## How It Works

```
                    ┌──────────────────┐
                    │  GitHub Private  │
                    │  Repo (via OAuth)│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  1. INGEST       │
                    │  Shallow clone   │
                    │  Encrypted store │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌───▼────────┐ ┌───▼──────────┐
     │ Code Analysis  │ │ Doc Review │ │ Git Forensics│
     │ AST / Deps /   │ │ Claims vs  │ │ Commit       │
     │ API Detection  │ │ Reality    │ │ Patterns     │
     └────────┬───────┘ └───┬────────┘ └───┬──────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼──────────────────────────┐
                    │ 2. ANALYZE                        │
                    │ Multi-AI Parallel Evaluation       │
                    │ (Claude ∥ Gemini ∥ ChatGPT)       │
                    │ Independent → Cross-Verification  │
                    └────────┬──────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │ 3. SCORE         │
                    │ Heuristic 30%    │
                    │ + AI Avg 70%     │
                    │ RED FLAG detect  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌───▼────────┐ ┌───▼──────────┐
     │ 4. REPORT      │ │ 5. PDF     │ │ 6. PURGE     │
     │ MD / HTML      │ │ Export     │ │ Disconnect   │
     │ Slides         │ │ (no code)  │ │ + Crypto-del │
     └────────────────┘ └────────────┘ │ + Certificate│
                                       └──────────────┘
```

---

## Private Repo Workflow (VC <> Startup)

```
Step 1: VC sends startup an access request link
Step 2: Startup approves GitHub OAuth (grants repo access)
Step 3: DDE clones repo into encrypted temp directory
Step 4: Multi-AI parallel analysis (Claude ∥ Gemini ∥ ChatGPT)
Step 5: Cross-verification → unified score + per-provider breakdown
Step 6: VC reviews scorecard + downloads PDF
Step 7: VC clicks "Disconnect & Purge"
         ├─ GitHub OAuth token revoked
         ├─ All source code crypto-erased
         ├─ Purge certificate generated
         └─ Only scores & findings retained (no code)
```

---

## Output Examples

### Scorecard

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Company:   [REDACTED]
 Date:      2026-03-18
 Providers: Claude + Gemini + ChatGPT
 Overall:   62 / 100  CAUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Technical Reality    ████████░░  16/25
 Originality          ███░░░░░░░   6/20
 Scalability          ████████░░  12/15
 Team Engineering     ██████░░░░  12/15
 Security Posture     ████████░░   8/10
 Business Alignment   ████░░░░░░   8/15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PROVIDER BREAKDOWN:
   Claude:  65/100  |  Gemini: 60/100  |  ChatGPT: 61/100
   Consensus: HIGH (max divergence: 5 pts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 RED FLAGS:
 - "Proprietary LLM" claim — codebase shows
   OpenAI API wrapper with minimal prompt eng.
 - 80% of git commits in last 2 weeks
   (suspected rush development before DD)
 - No test coverage for core ML pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### PDF Report

Professional PDF with cover page, score breakdown, per-provider comparison, RED FLAGS, architecture findings, and NDA compliance footer. **Contains zero source code** — only analysis findings and recommendations.

### Disconnect & Purge Confirmation

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PURGE CERTIFICATE
 Certificate ID: dde_purge_a1b2c3d4
 Date:           2026-03-18T15:30:00Z
 Files purged:   847
 Bytes erased:   12,345,678
 Method:         3-pass random overwrite
 GitHub token:   REVOKED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Data Security & NDA Compliance

| Guarantee | Implementation |
|-----------|---------------|
| **No cloud storage** | All data processed locally in encrypted tmpfs |
| **OAuth tokens encrypted** | Fernet encryption, in-memory only (never written to disk) |
| **API data handling** | Anthropic / Google / OpenAI — 0-day retention policy for API calls |
| **Cryptographic erasure** | 3-pass random overwrite + encrypted volume destruction |
| **Purge certificate** | SHA-256 signed certificate proving data existed and was destroyed |
| **GitHub disconnect** | OAuth token revoked via GitHub API on disconnect |
| **No raw code in reports** | PDF/MD reports contain findings only, never source code |
| **Audit trail** | Timestamped log of all operations for compliance |

---

## Project Structure

```
due-diligence-engine/
├── src/
│   ├── ai/                    # Multi-AI provider abstraction
│   │   └── providers.py       # Claude / Gemini / ChatGPT unified interface
│   ├── ingest/                # Secure data intake (local, zip, GitHub URL)
│   ├── analyze/               # AI-powered analysis
│   │   ├── code.py            # AST & dependency analysis
│   │   ├── docs.py            # Document claim extraction
│   │   ├── git_forensics.py   # Git history forensics
│   │   ├── consistency.py     # Cross-reference checker
│   │   └── engine.py          # Multi-AI orchestrator & cross-verification
│   ├── score/                 # 100-point scoring engine (Heuristic 30% + AI 70%)
│   ├── report/
│   │   ├── generator.py       # MD/HTML report generation
│   │   ├── slides.py          # Architecture visualization
│   │   └── pdf_generator.py   # Professional PDF export
│   ├── purge/                 # Cryptographic data destruction
│   ├── saas/
│   │   ├── app.py             # FastAPI endpoints
│   │   ├── dashboard.py       # Web dashboard UI
│   │   ├── github_oauth.py    # GitHub OAuth integration
│   │   ├── billing.py         # Stripe billing (Pro Analysis)
│   │   └── auth.py            # API key authentication
│   └── cli.py                 # CLI interface
├── templates/
│   ├── evaluation.md          # Evaluation framework
│   ├── scorecard.html         # Scorecard template
│   └── dashboard.html         # Web dashboard template
├── pyproject.toml
└── README.md
```

---

## Deployment Options

### Option 1: Local Only (Free, No AI)

Run local code analysis without any API keys. Get AST analysis, dependency graphs, and git forensics.

```bash
pip install due-diligence-engine
dde analyze owner/repo --skip-ai
```

### Option 2: BYOK — Self-Hosted CLI (Free)

Use your own API keys. Full control, no data leaves your machine (except API calls to your configured providers).

```bash
pip install due-diligence-engine

# Configure 1, 2, or all 3 providers
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_AI_API_KEY="AIza..."
export OPENAI_API_KEY="sk-..."

dde analyze owner/repo
```

### Option 3: BYOK — Self-Hosted Web Dashboard (Free)

Run the full web dashboard locally with GitHub OAuth for private repos. Enter API keys via the dashboard UI.

```bash
export GITHUB_CLIENT_ID="..."
export GITHUB_CLIENT_SECRET="..."
dde serve
# Open http://localhost:8000/dashboard/
# Enter your AI API keys in the dashboard settings
```

### Option 4: Pro Analysis (Japan, Managed)

For investors who prefer not to manage API keys. We run Claude + Gemini analysis on our infrastructure.

**Pricing: ¥5,000 per analysis** (Stripe checkout).

---

## Roadmap

- [x] Core evaluation framework design
- [x] CLI tool with secure ingest pipeline
- [x] Code analysis engine (AST + dependency graph)
- [x] Git forensics module
- [x] Scoring engine with RED FLAG detection
- [x] GitHub URL direct analysis (`dde analyze owner/repo`)
- [x] GitHub OAuth for private repo access
- [x] Web dashboard with Connect/Analyze/Disconnect flow
- [x] PDF report export (no source code included)
- [x] Disconnect & Purge with certificate generation
- [x] Multi-AI analysis engine (Claude / Gemini / ChatGPT simultaneous BYOK)
- [x] BYOK API key input on web dashboard
- [x] Provider score comparison (per-provider breakdown)
- [ ] Pro Analysis with Stripe payment (¥5,000/analysis)
- [ ] Leaderboard management
- [ ] Batch analysis mode (portfolio-wide DD)
- [ ] Startup-side access approval portal

---

## Disclaimer

This tool provides **technical analysis to assist investment decisions**. It is not investment advice. Scores are based on automated analysis of provided materials and should be used as one input among many in the due diligence process. Always consult qualified professionals for investment decisions.

---

## License

[Apache License 2.0](LICENSE) — See [LICENSE](LICENSE) for details.

---

<div align="center">

**Powered by Claude (Anthropic) + Gemini (Google) + ChatGPT (OpenAI)**

</div>
