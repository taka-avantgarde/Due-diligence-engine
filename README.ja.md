<div align="center">

# Due Diligence Engine

**IDEのAIが、デューデリジェンスアナリストになる。APIキー不要。PDF出力のみ。**

`dde prompt --pdf` を Claude Code / Cursor / Copilot で実行 — AIがコードベースを読み、コンサルティンググレードPDFを自動生成します。

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![CodeQL](https://img.shields.io/badge/Security-CodeQL_%7C_Dependabot_%7C_pip--audit-5271FF.svg)](SECURITY.md)

[English](README.md) | [日本語](README.ja.md)

</div>

---

## クイックスタート

```bash
pip install --no-cache-dir git+https://github.com/taka-avantgarde/Due-diligence-engine.git
dde prompt --pdf --lang ja
```

以上です。AI搭載IDEのターミナルで実行するだけ。AIが自律的にコードを読み、世界トップクラスのテクノロジーコンサルタントとして評価し、PDFを `~/Downloads/` に出力します。

APIキー不要。クラウド保存なし。追加コスト¥0。

---

## 何をするツールか

DDE は既存のIDE AIサブスクを**テクノロジーデューデリジェンスアナリスト**に変えます。投資前DD、買収分析、競合ベンチマーク、AIウォッシュ検出に利用。

**想定ユーザー**: CTO、VCテクノロジーパートナー、M&A技術アドバイザー、事業会社のDD担当。

---

## 機能

- **APIコスト¥0** — IDEの既存AIサブスクを使用（別APIキー不要）
- **競合比較チャート7種** — Forrester Wave · BCG成長シェア · McKinsey技術モート · セキュリティ＆プライバシー成熟度 · データガバナンス＆透明性 · GSリスク・リターン · イノベーションバブル
- **徹底的な競合調査** — 6〜16社×6市場（グローバル / 米国 / EMEA / 日本 / SEA / 中南米）
- **軸選定理由キャプション** — 各チャートになぜその軸か・何を測定するかを説明
- **サイト検証** — プロダクト/サービスURLに対する10項目の信頼性監査
- **SWOT · 投資判断 · レッドフラグ** — 投資委員会が必要とする全要素
- **バイリンガル** — 英日PDF（`--lang ja`）、日付フォーマットもローカライズ
- **セキュリティ監査** — OSS、PR毎に CodeQL / Dependabot / pip-audit / gitleaks

---

## 使い方

```bash
# カレントディレクトリを分析
dde prompt --pdf --lang ja

# GitHub リポジトリをステージ指定で分析
dde prompt owner/repo --pdf --lang ja --stage seed

# 非対話モード（対話入力できないAIターミナル向け）
dde prompt --pdf --lang ja \
  --url https://example.com \
  --url https://docs.example.com

# 直接BYOKマルチAI分析（オプション）
export ANTHROPIC_API_KEY=sk-ant-...
dde analyze owner/repo
```

---

## スコアリング

### 6次元評価

| 評価軸 | 重み | 検出内容 |
|--------|------|---------|
| 技術独自性 | 25% | APIラッパー vs 本物のIP |
| 技術先進性 | 20% | 技術スタックの先進度 |
| 実装深度 | 20% | PoC vs 本番品質 |
| アーキテクチャ品質 | 15% | 設計品質 |
| 主張整合性 | 10% | ピッチ vs 現実 |
| セキュリティ態勢 | 10% | セキュリティ成熟度 |

### グレード分類

```
0     40      60     75      90    100
|-----|-------|------|-------|-----|
  F      D       C      B       A
```

| グレード | 推奨 |
|---------|------|
| 🏆 A (90+) | 有力投資候補 |
| ✅ B (75-89) | 条件付きで投資可能 |
| ⚡ C (60-74) | 重要な懸念あり |
| ⚠️ D (40-59) | 高リスク |
| 🚫 F (<40) | 投資不可 |

各評価軸は **Lv.1〜10** でも明確な基準付きで評価。

---

## PDF構成（13〜15ページ）

| # | セクション | 内容 |
|---|-----------|------|
| 1 | **表紙** | ダークテーマ + Arc sky アクセント、プロジェクト名・スコア・グレード |
| 2 | **スコアダッシュボード** | 6軸棒グラフ + バロメーター |
| 3 | **エグゼクティブサマリー** | ビジネス+技術サマリー |
| 4 | **SWOT分析** | エビデンスベース、ビジネスアナロジー付き |
| 5 | **スコア内訳** | 軸別の根拠・可能性 |
| 6 | **テクレベル評価** | Lv.1〜10ゲージ + 平易な解説 |
| 7 | **将来性評価** | 1/3/5年予測（信頼度付き） |
| 8 | **戦略アドバイス** | 即座/中期/長期 |
| 9 | **投資判断** | 推奨/リスク/アップサイド/類似企業 |
| 10 | **レッドフラグ** | 深刻度別（Critical/High/Medium/Low） |
| 11 | **サイト検証** | 10項目の信頼性監査（URL提供時のみ） |
| 12-14 | **競合分析** | 7チャート×6市場、軸説明キャプション付き |
| 15 | **用語集** | 全技術用語に非エンジニア向け注釈 |

---

## セキュリティ

- ✅ **ローカル完結処理** — `dde prompt` は外部送信ゼロ
- ✅ **レポートにソースコードなし** — PDFは所見のみ
- ✅ **API 0-day保持** — `dde analyze` は無保持エンドポイント使用
- ✅ **自動セキュリティ**: CodeQL · Dependabot · pip-audit · safety · osv-scanner · gitleaks
- ✅ **`main` ブランチ保護** + 必須CI + シークレットプッシュ保護
- ✅ **PrivateリポジトリアクセスはPAT** — メモリ上で1回使用後即破棄

脆弱性報告: [SECURITY.md](SECURITY.md) — 48時間以内の初回応答SLA。

---

## なぜOSSか

オープンソースは**セキュリティ機能**であり、リスクではありません。全てのコードが監査可能。隠しバックドアなし。Signal/libsignal と同じ哲学: **透明性こそ信頼の源泉**。

---

## ライセンス

[Apache License 2.0](LICENSE) — Copyright 2026 Takayuki Miyano / Atlas Associates

---

<div align="center">

**Powered by Due Diligence Engine — Takayuki Miyano / Atlas Associates**

</div>
