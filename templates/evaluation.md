# Due Diligence Evaluation Framework v2.0

## Overview

This framework evaluates **technology only** (no team assessment) across 6 dimensions.
Each dimension uses a **10-level rating scale** with clear criteria, converted to a 100-point weighted score.

---

## Dimension 1: Technical Originality (Weight: 25%)

**What it measures:** Is this genuine intellectual property or a thin wrapper around third-party APIs?

### 10-Level Rating Scale

| Level | Label | Description |
|-------|-------|-------------|
| Lv.1 | Copy | Existing OSS/API をそのまま利用。独自コードなし |
| Lv.2 | Wrapper | API薄いラッパー。設定変更程度のカスタマイズ |
| Lv.3 | Glue | 複数APIの組み合わせ。独自ロジックはルーティングのみ |
| Lv.4 | Customized | 既存技術のカスタマイズ。一部独自処理あり |
| Lv.5 | Extended | 既存フレームワークの大幅拡張。独自アルゴリズム一部あり |
| Lv.6 | Hybrid | 既存+独自技術のハイブリッド。明確なIP領域あり |
| Lv.7 | Original | コア技術が独自実装。特許申請可能レベル |
| Lv.8 | Advanced | 業界先端の独自実装。学会発表レベル |
| Lv.9 | Breakthrough | 新しい技術パラダイムの提案。論文引用されるレベル |
| Lv.10 | Frontier | 世界最先端。既存技術を根本的に置き換える可能性 |

### Red Flag Triggers
- **CRITICAL**: API wrapper ratio > 70% with claims of proprietary technology
- **HIGH**: No custom algorithms despite "AI-powered" marketing claims

---

## Dimension 2: Technology Advancement (Weight: 20%)

**What it measures:** How cutting-edge is the technology stack and approach?

### 10-Level Rating Scale

| Level | Label | Description |
|-------|-------|-------------|
| Lv.1 | Legacy | 10年以上前の技術。メンテナンスモード |
| Lv.2 | Outdated | 5-10年前の技術。後継技術が存在 |
| Lv.3 | Established | 広く普及した安定技術。新規性なし |
| Lv.4 | Current | 現在の業界標準レベル |
| Lv.5 | Modern | 最新のベストプラクティスを採用 |
| Lv.6 | Progressive | 次世代技術の早期採用者 |
| Lv.7 | Innovative | 業界内で先進的。競合が追随中 |
| Lv.8 | Leading | 業界をリードする技術選択 |
| Lv.9 | Pioneering | 新カテゴリを定義する技術 |
| Lv.10 | Visionary | 5年先の技術を今実装。市場が追いつく段階 |

---

## Dimension 3: Implementation Depth (Weight: 20%)

**What it measures:** Is the implementation production-grade or just a prototype?

### 10-Level Rating Scale

| Level | Label | Description |
|-------|-------|-------------|
| Lv.1 | Mockup | UIモックのみ。バックエンド未実装 |
| Lv.2 | PoC | 概念実証レベル。ハードコード多数 |
| Lv.3 | Prototype | 動くプロトタイプ。エラー処理なし |
| Lv.4 | Alpha | 基本機能動作。テストなし |
| Lv.5 | Beta | 主要機能実装済み。基本テストあり |
| Lv.6 | RC | 本番想定の実装。CI/CDあり |
| Lv.7 | Production | 本番運用中。監視・ログあり |
| Lv.8 | Mature | 長期運用実績。パフォーマンス最適化済み |
| Lv.9 | Enterprise | 大規模運用対応。SLA保証レベル |
| Lv.10 | Mission-Critical | ミッションクリティカル対応。冗長性・DR完備 |

### Red Flag Triggers
- **HIGH**: No tests in a production-deployed application
- **MEDIUM**: No CI/CD with claims of "continuous deployment"

---

## Dimension 4: Architecture Quality (Weight: 15%)

**What it measures:** Is the architecture scalable and well-designed?

### 10-Level Rating Scale

| Level | Label | Description |
|-------|-------|-------------|
| Lv.1 | Spaghetti | 構造なし。単一ファイルに全コード |
| Lv.2 | Monolith | 最小限の分離。全結合 |
| Lv.3 | Layered | 基本的なレイヤー分離あり |
| Lv.4 | Modular | モジュール分割。一部密結合 |
| Lv.5 | Clean | 関心の分離が明確。テスト容易 |
| Lv.6 | Scalable | 水平スケーリング対応設計 |
| Lv.7 | Microservice | 適切なサービス分割。API契約明確 |
| Lv.8 | Event-Driven | イベント駆動。非同期処理最適化 |
| Lv.9 | Cloud-Native | クラウドネイティブ設計。自動スケール |
| Lv.10 | Distributed | 分散システム。CAP定理を意識した設計 |

---

## Dimension 5: Claim Consistency (Weight: 10%)

**What it measures:** Do documentation and pitch claims match the actual code?

### 10-Level Rating Scale

| Level | Label | Description |
|-------|-------|-------------|
| Lv.1 | Fabricated | 主張と実装が完全に乖離。意図的虚偽の疑い |
| Lv.2 | Misleading | 重要な点で誤解を招く主張 |
| Lv.3 | Exaggerated | 大幅な誇張。実装は主張の30%以下 |
| Lv.4 | Overstated | 一部誇張あり。コア機能は存在 |
| Lv.5 | Partial | 主張の半分程度が検証可能 |
| Lv.6 | Mostly True | 大部分が事実。軽微な不一致あり |
| Lv.7 | Accurate | 主張が実装と一致。ベンチマーク一部あり |
| Lv.8 | Verified | 主張がコードで完全に検証可能 |
| Lv.9 | Conservative | 実装が主張以上。控えめな表現 |
| Lv.10 | Transparent | 全主張に証拠付き。第三者検証済み |

### Red Flag Triggers
- **CRITICAL**: Claims proprietary technology but code is an API wrapper
- **HIGH**: Performance claims with no benchmarks or evidence

---

## Dimension 6: Security Posture (Weight: 10%)

**What it measures:** Are security practices appropriate for the domain?

### 10-Level Rating Scale

| Level | Label | Description |
|-------|-------|-------------|
| Lv.1 | Negligent | ハードコードされた秘密鍵。SQLi脆弱性 |
| Lv.2 | Minimal | 基本的な問題あり。入力検証なし |
| Lv.3 | Basic | 最低限の対策。OWASP Top10未対応 |
| Lv.4 | Standard | 基本的なセキュリティ対策済み |
| Lv.5 | Compliant | 業界標準準拠。定期的な依存関係更新 |
| Lv.6 | Hardened | セキュリティスキャン自動化。脆弱性管理あり |
| Lv.7 | Defense-in-Depth | 多層防御。ペネトレーションテスト実施 |
| Lv.8 | Zero-Trust | ゼロトラスト設計。暗号化完備 |
| Lv.9 | Certified | SOC2/ISO27001等の認証取得レベル |
| Lv.10 | Military-Grade | 国防レベル。形式検証・監査完備 |

### Red Flag Triggers
- **CRITICAL**: Hardcoded API keys or secrets in repository
- **HIGH**: Known vulnerable dependencies

---

## Overall Grade Mapping

| Score | Grade | Recommendation |
|-------|-------|---------------|
| 90-100 | A | Strong investment candidate. Proceed with standard terms. |
| 75-89  | B | Viable with conditions. Address flagged items before closing. |
| 60-74  | C | Significant concerns. Require remediation plan with milestones. |
| 40-59  | D | High risk. Consider pass or heavily discounted terms. |
| 0-39   | F | Do not invest. Fundamental issues detected. |

## Red Flag Escalation Rules

- Any **CRITICAL** red flag caps the overall score at 40 (Grade D maximum)
- 3+ **HIGH** red flags cap the score at 60 (Grade C maximum)
- Red flags from the **Claim Consistency** dimension carry extra weight as they indicate potential misrepresentation

---

## Pricing Model

| Plan | API Key | Cost | Best For |
|------|---------|------|----------|
| **BYOK** | Your own Anthropic key | FREE | Technical VCs with engineering staff |
| **Starter SaaS** | Managed by DDE | 2x API cost | Individual investors |
| **Professional SaaS** | Managed by DDE | 2x API cost | VC firms (5-25 analyses/month) |
| **Enterprise SaaS** | Managed by DDE | 2x API cost | Large firms (unlimited) |
