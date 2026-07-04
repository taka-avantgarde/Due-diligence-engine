<div align="center">

| 🇬🇧 [![English](https://img.shields.io/badge/English-30363D?style=for-the-badge)](README.md) | 🇯🇵 [![日本語](https://img.shields.io/badge/%E6%97%A5%E6%9C%AC%E8%AA%9E-5271FF?style=for-the-badge)](README.ja.md) | 🇪🇸 [![Español](https://img.shields.io/badge/Espa%C3%B1ol-30363D?style=for-the-badge)](README.es.md) | 🇸🇦 [![العربية](https://img.shields.io/badge/%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-30363D?style=for-the-badge)](README.ar.md) | 🇫🇷 [![Français](https://img.shields.io/badge/Fran%C3%A7ais-30363D?style=for-the-badge)](README.fr.md) | 🇩🇪 [![Deutsch](https://img.shields.io/badge/Deutsch-30363D?style=for-the-badge)](README.de.md) |
|:--:|:--:|:--:|:--:|:--:|:--:|

<sub>👆 Click your language to switch ・ クリックで言語を切り替え</sub>

<sub>🪟 **Windows の場合:** ネイティブ完全対応・CI テスト済み（Git が PATH に必要）。v0.5.0 から一時領域を現ユーザーのみに ACL ロック — WSL2 は任意です。</sub>

---

# 🔍 Due Diligence Engine

### **IDE の AI が、世界トップクラスの技術DDアナリストになる**

<sub>**APIキー不要 · PDF出力 · OSS · CodeQL監査済み**</sub>

<br/>

```
┌─────────────────────────────────────────────────────────────┐
│  $ dde prompt --pdf --lang ja                               │
│                                                             │
│  🌐 ライブ Web 調査（2026 年最新の競合・資金・CVE）...        │
│  コードベースを読み取り...                                    │
│  5次元で評価（各 20% 均等）...                                │
│  競合ランドスケープ構築（7チャート×6市場）...                │
│  実装能力マトリックス調査（30項目×10社、出典 URL 必須）...   │
│  競合選定理由を執筆中...                                      │
│                                                             │
│  スコア: [■■■■■■■■■■■■■■■■■■■■■■■■■■□□□□] 82/100 Lv.8     │
│  グレード: B  →  条件付きで投資可能                           │
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
[![Version](https://img.shields.io/badge/version-v0.5.0-000000?style=flat-square)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/releases)

[![Repo Views](https://komarev.com/ghpvc/?username=taka-avantgarde&repo=Due-diligence-engine&color=5271FF&style=flat-square&label=Repo+Views)](https://github.com/Atlas-Associates-Inc/Due-diligence-engine)

</div>

---

## ⚡ クイックスタート

**最初に 1 回だけインストール:**

```bash
python3 -m pip install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

**プロジェクトのディレクトリで実行:**

```bash
dde prompt --pdf --lang ja
```

AI 搭載 IDE のターミナル（Claude Code / Cursor / Copilot 等）で実行してください。AI がコードベースを読み、世界トップクラスのテクノロジーコンサルタントとして評価し、24ページの PDF を `~/Downloads/` に書き出します。**APIキー不要・クラウド経由なし・追加コスト¥0。**

<details>
<summary><sub>その他のインストール方法 · macOS Homebrew 注意点</sub></summary>

Linux / venv / 古い macOS の短い形式:
```bash
pip3 install --no-cache-dir git+https://github.com/Atlas-Associates-Inc/Due-diligence-engine.git
```

macOS Homebrew ユーザーは必ず `python3 -m pip` を使用してください。Homebrew Python 3.12+ では `pip` 単体コマンドが同梱されません。

</details>

---

## 💭 ベストな使い方

> **要点**: IDE のターミナルでできるだけ高性能な AI を起動して、コマンドをコピペするだけ。
> 10〜20 分ほど放置すれば完了です。

**推奨セットアップ:**

- **IDE 内で利用可能な最高性能モデルを起動**（Claude Fable 5 / GPT-5 / Gemini 2.5 Pro 等）
- **`dde prompt --pdf --lang ja` をターミナルにペースト**
- **コーヒー一杯の時間 ☕ を** — AI が数百のファイルを読み、9軸以上で評価し、
  世界の競合 5〜10 社を調査し、22 ページのコンサル PDF を構築します
- **所要時間**: **10〜20 分ほど**（大規模コードベースや深いモデルでは長め）

**よくある疑問:**

| 心配 | 回答 |
|------|------|
| 🔐 **データ漏洩は?** | ありません。全て IDE の AI サンドボックス内で完結 — 第三者サーバーなし・テレメトリなし。DDE 本体は 100% ローカル Python |
| 💰 **コストは?** | 追加 ¥0。既存の IDE AI サブスクを流用 |
| 🔑 **API キーは?** | 不要。IDE が AI 認証を処理 |
| ⚙️ **セットアップは?** | `python3 -m pip install` のみ。設定・アカウント不要 |
| 🎁 **裏はある?** | ありません。DDE は**個人の趣味プロジェクト**として楽しく作って OSS 公開しているだけ。ご自由にどうぞ |

> **趣味で一人で作っています。** 誰かの役に立てばそれで満足。よければ ⭐ で応援してください

---

## 💻 どの AI ターミナルで動くか — あなたが今使っている AI でそのまま使えます

DDE は構造化プロンプトを生成するだけのツールです。**ファイルを読めて、シェルコマンドを実行できる任意の AI エージェント**が、そのプロンプトを実行できます。DDE 専用の統合・プラグインは一切必要ありません。

**動作確認済み**（公式ドキュメント確認 + 実機検証、2026-05）:
- ✅ [**Claude Code**](https://code.claude.com/docs/en/overview)（CLI / VS Code / JetBrains / Desktop / Web、Anthropic 公式）
- ✅ [**GitHub Copilot Agent Mode**](https://docs.github.com/en/copilot/using-github-copilot/copilot-chat/asking-github-copilot-questions-in-your-ide)（VS Code / Visual Studio / JetBrains / Xcode / Eclipse、GA リリース済み）

**原理的に動作（要件: ファイル読み取り + シェル実行 + できれば Web 検索）**:
- Cursor Agent、Gemini Code Assist、Continue.dev、Cody (Sourcegraph)、Aider、Windsurf、Amazon Q Developer、JetBrains AI Assistant など

> ✅ 既に上記のどれかを使っているなら、`pip install` 一発で今日から使えます。
> 動作確認した環境は [Issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues) で教えてください。

### 💰 追加料金は一切ありません

**あなたが既に契約している AI のサブスクリプションだけで完結します**。Claude Code Pro / GitHub Copilot / Cursor Pro / Gemini Advanced 等の月額に含まれる利用枠で動作。DDE のプラン購入も、追加 API キーも、隠れた課金も一切ありません。

---

## 👥 誰のためのツールか

| ユーザー | ユースケース | 短縮時間 |
|---------|-------------|---------|
| **VC のテクノロジーパートナー** | 投資前の技術 DD | 2-5日 → 30分 |
| **CTO・エンジニアリングリード** | 取締役会前の社内技術監査 | 1週間 → 1時間 |
| **M&A 技術アドバイザー** | 買収対象の DD | 1-2週間 → 1日 |
| **DD コンサル独立業者** | ブティック級の技術評価 | スケール: 1→10社/週 |
| **創業者** | 資金調達前の自己評価 | 自社コードを客観視できる |
| **事業会社のイノベーション部門** | ベンダー・スタートアップ提携評価 | アドホック → 体系的 |

> 日常ワークフローで AI を既に使っているエンジニア・技術系意思決定者向けのツール。

---

## 🆚 他ツールとの比較

|   | DDE | 手動 DD | 一般的な AI コードレビュー | SaaS DD プラットフォーム |
|---|:---:|:---:|:---:|:---:|
| **コスト** | ¥0 (IDE AI 流用) | ¥¥¥¥ (コンサル費) | API 課金 | ¥¥¥¥ (サブスク) |
| **プライバシー** | ローカル完結 | ローカル | ベンダー送信 | ベンダー送信 |
| **出力** | 24ページ コンサル PDF | 個別レポート | インラインコメント | Web ダッシュボード |
| **データ鮮度** | ✅ ライブ Web 検索 (2026) + 出典 URL | アナリスト次第 | 学習データのみ (古い) | 更新頻度はベンダー次第 |
| **暗号評価深度** | PQXDH / Signal Protocol | コンサル次第 | 一般的 | 一般的 |
| **競合チャート** | 7種 + 実装マトリックス | 手動調査 | なし | 限定的 |
| **セットアップ時間** | 1コマンド | 数週間 | 数分 | 数日 (アカウント・オンボーディング) |
| **カスタマイズ性** | 完全ソース公開 | 可能 | 限定的 | ベンダーロックイン |

---

## DDE の差別化ポイント

ありがちな「AIコードレビュアー」のチェック:
> *「認証あるか？✓ HTTPS あるか？✓ テストあるか？✓」*

これはチェックリスト遵守。**DDE はもっと深く掘ります:**

> *「暗号化は Signal Protocol か？ PQXDH + ML-KEM-1024 か？
> libsignal/BoringSSL FFI か、それとも自前 crypto 実装か？
> チームは暗号研究を発表しているか？」*

土台は **Atlas エンジニアリング哲学**: サイバーセキュリティ全般（暗号化・プライバシー・
通信・多層防御）への真剣なエンジニアリング — ソースコードから直接読み取る。
SOC2 / MFA / WebAuthn 等の認証は参考情報のみ、スコア対象外。

**🌐 さらに v0.3.2 から**: AI は**コードを読む前にライブ Web 検索を実行**します — 競合の最新動向（買収・倒産・新規参入）、2026 年のファンディングラウンド、最新 CVE、規制動向を取得し、その鮮度ある文脈で評価。各競合・各マトリックスセルには**出典 URL と検証日**が付き、JSON 先頭の `data_freshness` ブロックで全検索クエリが追跡可能。**学習データカットオフ依存の古い分析は構造的に排除されます**。**（v0.5.0）** この出所情報は PDF に直接表示されるようになりました — スコアダッシュボードの「データ出所ボックス」が検索日とクエリ/ソース数を示し、Web 調査が実施されなかった場合は学習データのみ警告を明示します。

---

## 🔒 Atlas エンジニアリング哲学（サイバーセキュリティ重視・並列評価）

標準 5 次元スコアに **置き換わるのではなく並列に追加** される評価系。

```
4軸 — 重み合計 100%

  高速化            20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  安定化            20%  ██████████░░░░░░░░░░░░░░░░░░░░░░
  軽量化             5%  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  セキュリティ強度 55%  ███████████████████████████░░░░░  ← 核心

  サイバーセキュリティのサブ内訳（55% 内訳・全層防御）:
    暗号化技術の高度さ          35%  ← 最大: Signal Protocol、PQXDH、libsignal
    プライバシー保護              8%
    通信の安全                    7%
    レイヤー構成                  3%
    基本衛生（MFA・WebAuthn）     2%  ← コード実装のみ評価、認証は参考情報
```

---

## 📊 5次元標準スコア（v0.3 — 均等 20% バランス）

| 評価軸 | 重み | 検出内容 |
|--------|----:|---------|
| 技術独自性 | 20% | API ラッパー vs 本物の IP |
| 技術先進性 | 20% | 技術スタックの先進度 |
| 実装深度 | 20% | PoC vs 本番品質 |
| アーキテクチャ品質（セキュリティ態勢を含む） | 20% | 設計品質 + セキュリティ成熟度 |
| 主張整合性 | 20% | ピッチ vs 現実 |

> **最終スコア** = ヒューリスティック分析（30%）+ AI 平均スコア（70%）

> **v0.3 変更**: セキュリティ態勢をアーキテクチャ品質にマージ。セキュリティは
> 本番運用アーキテクチャの不可分な要素として評価（独立サイロではない）。

```
グレード分類:

  0      40       60      75       90     100
  |------|--------|-------|--------|------|
   F      D        C       B        A
   ✗      ⚠        ⚡       ✓        ★
```

| グレード | 推奨アクション |
|---------|----------------|
| ★ A (90+)  | 有力な投資候補 |
| ✓ B (75-89)| 条件付きで投資可能 |
| ⚡ C (60-74)| 重要な懸念あり |
| ⚠ D (40-59) | 高リスク |
| ✗ F (<40)  | 投資不可 |

各軸は **Lv.1〜10** でも明確な基準付きで評価。

---

## 🎯 競合分析チャート 7種 × 6市場

6つのグローバル市場（グローバル / 米国 / EMEA / 日本 / SEA / 中南米）それぞれで:

| # | チャート | 評価軸 |
|---|---------|--------|
| 1 | **Forrester Wave / マジック・クアドラント** | ビジョン × 実行力 |
| 2 | **BCG 成長・シェアマトリックス** | 市場成長率 × 相対シェア |
| 3 | **McKinsey 技術モート** | 競争ポジション × 技術モート深度 |
| 4 | **セキュリティ＆プライバシー成熟度** | セキュリティ実装 × プライバシー準備 |
| 5 | **データガバナンス＆透明性** | データ保護 × 監査透明性 |
| 6 | **GS リスク調整リターン** | 下振れリスク × 上振れポテンシャル |
| 7 | **イノベーション vs 商業化** | R&D 速度 × ARR トラクション (3D バブル) |

各チャートに **6〜16社** の競合を配置。**軸選定理由キャプション** で
*なぜ* この軸か、*何を* 測定しているかを明示（クロスファンクショナル対応）。

---

## 🆕 実装能力マトリックス

第8の競合チャート — **約30項目 × グローバルトップ競合 5〜10社**:

```
                        Target   社 A    社 B    社 C    社 D    ...
暗号化（核心差別化）
  項目 1                ○        ○       ×       △       ○
  項目 2                ○        ○       ×       ×       ○
  項目 3                ○        ○       ○       ×       ○
  項目 4                ○        ×       ×       △       △
  ...
プライバシー・コンプライアンス
  項目 1                ○        △       ○       ×       △
  項目 2                ○        ○       △       ×       ×
  ...
```

項目と競合は **対象企業の業界に合わせて動的に選定**
（メッセージング / フィンテック / 医療 / ゲーミング / SaaS / IoT 等）。

4状態マーキング（日本式テックレーティング標準）:
- **○ verified**（公開資料で実装確認済み）
- **△ claimed**（主張あり、検証未完）
- **× not_implemented**（明示的に未対応）
- **? unknown**（判定不能 — 推測より優先）

さらに **競合選定理由** — 各競合企業について「なぜこの比較対象に選んだか」を
3〜5 行で解説（本社所在国、市場ポジション、カテゴリ付き）。

---

## 📄 24ページ PDF の中身

| # | セクション | 内容 |
|---|-----------|------|
| 1 | 表紙 | 黒 + Arc sky (#5271FF) アクセント、プロジェクト名・スコア・グレード |
| 2 | スコアダッシュボード | **5 次元** 横棒グラフ（各 20%）+ バロメーター + **5 次元レーダーチャート** + **データ出所ボックス**（検索日・クエリ/ソース数、未実施時は学習データのみ警告）|
| 3 | エグゼクティブサマリー | ビジネス + 技術サマリー |
| 4 | SWOT 分析 | 2×2 ビジュアルグリッド + エビデンス + ビジネスアナロジー |
| 5 | スコア内訳 | 軸別の根拠・可能性 |
| 6 | テクレベル評価 | **5 次元** Lv.1〜10 バー + 総合ゲージ |
| 7 | 将来性評価 | 1/3/5 年予測（信頼度付き） |
| 8 | 戦略アドバイス | 即座 / 中期 / 長期 |
| 9 | 投資判断 | 推奨 / リスク / アップサイド / 類似企業 |
| 10 | レッドフラグ | 深刻度別（Critical/High/Medium/Low） |
| 11 | サイト検証 | 10項目の技術力監査（主張検証 4 + コード実測 6） |
| 12-14 | 競合分析 | 7チャート × 6市場、軸説明キャプション付き |
| 15 | **🆕 競合選定理由** | 各競合について 3-5 行で「なぜ選んだか」（本社・ポジション・カテゴリ付き） |
| 16 | **実装能力マトリックス** | 約30項目 × トップ競合、○△×? マーキング |
| 17 | **Atlas 4 軸ダッシュボード** | 高速化 / 安定化 / 軽量化 / セキュリティ強度 |
| 18 | **セキュリティ内訳 + 用語集** | 5 サブ項目 + 非エンジニア向け用語解説（MFA/SOC2/libsignal/PQXDH 等） |
| 19-24 | 用語集 · 整合性 · コスト · 破棄証明 | 標準付録セクション |

---

## 🛠️ 使い方

> 🌍 **レポート対応言語（14）:** `en` `ja` `es` `fr` `de` `pt` `nl` `it` `id` `zh` `ko` `vi` `th` `ar` — 例: `dde prompt --pdf --lang es`。アラビア語は RTL 字形整形で描画（紙面レイアウトは LTR のまま）。

```bash
# カレントディレクトリ、日本語 PDF
dde prompt --pdf --lang ja

# GitHub リポをステージ指定で
dde prompt owner/repo --pdf --lang ja --stage seed

# 非対話モード（プロンプト入力できない AI ターミナル向け）
dde prompt --pdf --lang ja \
  --url https://example.com \
  --url https://docs.example.com

# 直接 BYOK マルチAIクロス検証（オプション）
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_AI_API_KEY=AIza...
export OPENAI_API_KEY=sk-...
dde analyze owner/repo
```

---

## 🔐 セキュリティ & OSS 哲学

| 保証 | 実装 |
|------|------|
| **ローカル完結処理** | `dde prompt` は外部送信ゼロ |
| **レポートにソースコードなし** | PDF は所見のみ |
| **API 0-day 保持** | `dde analyze` は無保持エンドポイント使用 |
| **自動セキュリティ CI** | CodeQL · Dependabot · pip-audit · safety · osv-scanner · GitHub Secret Scanning |
| **ブランチ保護** | `main` は PR + CI + シークレットプッシュ保護必須 |
| **Private リポ PAT** | メモリ上で 1 回使用後即破棄 |

脆弱性報告: [SECURITY.md](SECURITY.md) — 48 時間以内の初回応答 SLA。

### なぜ OSS はリスクではなくセキュリティ機能なのか

オープンソースは全コード監査可能。隠しバックドアなし。ブラックボックススコアリングなし。
これは Signal および libsignal と同じ哲学: **透明性こそ信頼の源泉**。

---

## ❓ FAQ

**Q: DDE は私のコードをどこかに送りますか?**
A: 送りません。`dde prompt` は完全にローカルで動作 — 構造化プロンプトを生成するだけで、実際のコードは IDE の AI が手元で読みます。オプションの `dde analyze`（BYOK）は AI プロバイダーの「無保持エンドポイント」のみ使用。

**Q: なぜ無料? 何か裏がある?**
A: 裏はありません。DDE は OSS（Apache 2.0）で、既存の IDE AI サブスク（Claude Code / Cursor / Copilot）を流用するだけ。テレメトリも追加課金もなし。

**Q: CI で使えますか?**
A: はい — [`action.yml`](action.yml) を参照。GitHub Actions として PR に組み込み、自動 DD スコアリングが可能。

**Q: 競合チャートの精度は?**
A: チャートは公開情報（whitepaper, GitHub, ブログ, SOC2 報告書）を AI が調査します。信頼度は競合の透明性に依存。`?`（不明）を積極的に使用 — 推測による誤検知の方がレポートの信頼性を損なうため。

**Q: 競合データは古くないですか? AI の学習カットオフは半年〜1年前では?**
A: v0.3.2 から **STEP 0「ライブ Web 調査」が必須化** されました。AI はコード読取の前に WebSearch / WebFetch で 2025〜2026 年の競合動向（買収・倒産・新規参入）、最新ファンディング、CVE、規制を取得します。各競合・各マトリックスセルには `sources` (URL) と `last_verified` (日付) が付き、JSON 先頭の `data_freshness` ブロックで実行クエリ全件を追跡可能。Web 検索ツールが無いランタイムでは `data_cutoff_warning` を明示し、**鮮度のないデータを黙って出力しない設計**。

**Q: なぜ「Atlas エンジニアリング哲学」?**
A: DDE は **Atlas Associates Inc** が開発（Arc Messenger — libsignal + PQXDH の E2EE メッセンジャー）。4軸評価は実際に Atlas が技術評価で見ている観点を反映。

**Q: スコア重みをカスタマイズできますか?**
A: 5 次元の重みは各 20% 均等（バランス・簡潔・解釈容易）。Atlas 4 軸の重み（20/20/5/55）は Atlas 哲学を反映したもので固定。Security Strength 内のサブ重みは業界コンテキストにより動的調整。

**Q: セキュリティが重要でないプロジェクトには?**
A: 5 次元スコア（アーキテクチャ品質にセキュリティ態勢が含まれ、均等 20%）が主スコアです。Atlas 4 軸は並列参考視点 — 両方表示されます。

**Q: `command not found: pip` でインストールできません**
A: `python3 -m pip install ...` の形式を使ってください。macOS Homebrew Python 3.12+ では `pip` コマンド単体が同梱されなくなりました。`python3 -m pip` 形式は全プラットフォーム（macOS / Linux / Windows / venv / pyenv / conda）で確実に動作します。

**Q: 第三者認証（SOC2 / ISO / HIPAA）がスコアに反映されないのはなぜ?**
A: DDE はバッジではなくソースコードを評価します。SOC2 取得済みでも平文保存サービスは依然として平文保存。SOC2 未取得でも libsignal + PQXDH を使えば暗号学的に強い。認証は文脈情報として表示しますがスコアには加味しません — セキュリティ内訳ページに明記しています。

---

## 🗺️ ロードマップ

**最近リリース (v0.3.x)**
- ✅ **レーダーチャート + データ出所 + Windows 強化**（2026-07、v0.5.0）: スコアダッシュボードに5次元レーダー（スパイダー）チャート追加。STEP 0 の Web 調査証跡を PDF に表示（検索日・クエリ/ソース数、未実施時は学習データのみ警告）。セキュア一時領域の Windows NTFS ACL ロック（icacls・所有者のみ）。CI テストマトリクスに Windows 追加
- ✅ **PDF レポート 14 言語対応**（2026-06、v0.4.0）: `--lang` でコンサル PDF を14言語生成 — English / 日本語 / Español / Français / Deutsch / Português / Nederlands / Italiano / Bahasa Indonesia / 简体中文 / 한국어 / Tiếng Việt / ไทย / العربية（アラビア語は RTL 字形整形）。Noto フォント同梱・設定不要。
- ✅ **Windows 互換性修正**（2026-06、v0.3.8）: `--pdf` コンサルフローの一時ファイルパスをクロスプラットフォーム化（旧 `/tmp` ハードコード）+ `--copy` の Windows クリップボード対応（`clip`）
- ✅ **6 言語 README**（2026-06、v0.3.7）: 最上部に言語スイッチャーを設置し、現在の言語をハイライト表示 — English / 日本語 / Español / العربية / Français / Deutsch、各言語を `README.<lang>.md` に分離
- ✅ **Claude Fable 5 へ更新**（2026-06、v0.3.6）: judge ティアを Opus 4.8 → **Fable 5**（`claude-fable-5`、Anthropic の最高性能モデル、2026-06-09 GA）に更新。ティア名も `opus` → `fable` にリネーム。価格は $10/$50 per MTok（Opus 4.8 比 2 倍だが最終判定の品質を最優先）
- ✅ **PDF チャート視覚強化 + 文字重なり修正**（2026-05、v0.3.5）: スコアダッシュボード/技術レベル/競合/マトリックスの全バーをモダンな丸角ピル型に刷新。日本語の長いラベル（「アーキテクチャ品質（セキュリティ含む）」等）がバーに被る問題をラベル領域拡大で解消（実際に PDF を生成・目視確認しながら反復）
- ✅ **Claude Opus 4.8 へ更新**（2026-05、v0.3.3〜4）: judge ティアを Opus 4.7→4.8 に（Sonnet 4.6 / Haiku 4.5 も最新化）。旧 Opus 4 / Sonnet 4 (20250514) の 2026-06-15 retire を回避し、Opus 値下げ（$15→$5 input）も反映
- ✅ **Atlas-Associates-Inc 組織へ移管**（2026-05、v0.3.4〜5）: リポジトリを taka-avantgarde → Atlas-Associates-Inc に移管。全 URL 更新、作者表記を Takayuki Miyano（@taka-avantgarde）+ Atlas Associates Inc に統一、gitleaks → GitHub native Secret Scanning に切替
- ✅ **ライブ Web 調査の必須化**（2026-05、STEP 0）: プロンプト冒頭に `_WEB_RESEARCH_MANDATE` を新設し、AI が「コードを読む前に」WebSearch/WebFetch で 2025〜2026 年の競合・資金調達・技術トレンド・CVE・規制動向を取りに行くことを必須化。JSON 出力に `data_freshness` ブロック（検索日・実行クエリ・参照 URL）と各競合・各マトリックスセルへの `sources` / `last_verified` を追加。学習データカットオフのみに依拠した古い分析を排除
- ✅ **プロンプト誤記修正**: 「6次元（実際は5次元）」「5つのチャート（実際は7つ）」を正しい数値に修正
- ✅ **CI Self-Test 修正**（2026-05）: `action.yml` の `grep -c` が「マッチ 0 件で exit 1」を返し、`set -e` + `pipefail` でジョブを落としていた問題を修正。`|| FALLBACK="0"` パターンで安全にハンドリング。**DDE Self-Test が初めて green に**
- ✅ **README にスコア算出式を明示**（最終スコア = ヒューリスティック 30% + AI 平均 70%）
- ✅ **Dependabot 完全自動化**: `dependencies` / `security` / `ci` ラベルを整備し、PR #23 (checkout v6) / #24 (upload-artifact v7) / #25 (osv-scanner-action v2.3.8) を全てマージ
- ✅ **自己参照バイアス対策**: プロンプト冒頭に「分析対象は DDE 本体ではない」明示警告（DDE を別プロジェクトで実行時の AI 混乱を防止）
- ✅ **レッドフラグの位置づけ明確化**: スコア対象外、開発チームのコード改善用参考情報として明記
- ✅ **クイックスタート簡素化**（インストール 1 行 + 代替形式は折り畳み）
- ✅ **Atlas 哲学をサイバーセキュリティ重視に再フレーミング**（暗号化単独ではなく全層防御、暗号化は最大サブウェイト 35%）
- ✅ **サイト検証を純粋な技術力評価に再設計**（10 項目: 主張検証 4 + コード実測 6 — 暗号実装深さ・並行制御モデル・I/O パターン・キャッシュ・スケーラビリティ・ML 深度）
- ✅ Atlas 重み再調整 **20 / 20 / 5 / 55**（暗号化コアを 35% にブースト）
- ✅ **ソースコードのみで判断**: 第三者認証（SOC2 / ISO / HIPAA）は参考情報のみ・スコア対象外
- ✅ **競合 1:1 整合**: マトリックスと選定理由を同一競合で揃え、推定スコア + 公開情報注釈
- ✅ 5 次元スコアリング（各 20% 均等、セキュリティはアーキテクチャに統合）
- ✅ 競合選定理由（各競合について 3-5 行で「なぜ選んだか」を説明）
- ✅ セキュリティ内訳ページに非エンジニア向け用語解説（MFA/SOC2/libsignal/PQXDH）
- ✅ AIDD 時代対応: AI 使用・高速コミットをスコアに反映しない
- ✅ `python3 -m pip` ガイド + 訪問者カウンターバッジ
- ✅ PDF レイアウト修正: KeepTogether、KeepInFrame (SWOT)、2 行ラップ説明文

**以前のリリース (v0.2.0)**
- ✅ Atlas 4 軸最適化評価（当初 25/20/5/50、現在 20/20/5/55）
- ✅ 実装能力マトリックス（第8競合チャート）
- ✅ Web ダッシュボード完全削除（CLI + PDF 一本化）
- ✅ 黒 + Arc sky (#5271FF) ブランドアイデンティティ
- ✅ タイポグラフィシステム刷新（leading・階層）
- ✅ セキュリティ CI 強化（CodeQL, Dependabot, gitleaks）

**今後の予定 (v0.4.0+)**
- 🚧 バッチモード — ポートフォリオ複数リポを 1 コマンドで分析
- 🚧 履歴トラッキング — 再分析でスコア推移可視化
- 🚧 Slack/Discord 通知アダプター
- 🚧 業界別評価パック（医療・フィンテック・ゲーミングプリセット）
- 🚧 PyPI / Homebrew 配布

機能要望・バグ報告は [Issue](https://github.com/Atlas-Associates-Inc/Due-diligence-engine/issues) でお知らせください。

---

## 🤝 コントリビューション

コントリビューション歓迎。コードベースは小さく、テストもしっかり:

```bash
git clone https://github.com/Atlas-Associates-Inc/Due-diligence-engine
cd Due-diligence-engine
python3 -m pip install -e ".[dev]"
pytest
```

- **バグ報告**: `dde --version` の出力 + 最小再現手順を含めてください
- **機能要望**: GitHub Discussions で関心度を測ってからお願いします
- **PR**: 全テスト pass + 新機能には新テスト追加

---

## 📜 ライセンス

[Apache License 2.0](LICENSE) — Copyright © 2026 [Takayuki Miyano](https://github.com/taka-avantgarde) / [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

---

<div align="center">

**Powered by Due Diligence Engine**

Created by [Takayuki Miyano](https://github.com/taka-avantgarde) — [Atlas Associates Inc](https://github.com/Atlas-Associates-Inc)

`v0.5.0` — 🌍 6 言語 README · 🆕 Claude Fable 5 / Sonnet 4.6 / Haiku 4.5 対応 · 🌐 ライブ Web 調査 · 5 次元スコアリング

</div>
