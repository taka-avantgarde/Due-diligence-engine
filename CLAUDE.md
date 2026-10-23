# Due Diligence Engine — プロジェクト規約 / Project Conventions

## ⚠️ ドキュメント同期（必須） / Doc Sync (MANDATORY)

- README は **6 言語すべてを同期更新**すること:
  - `README.md` (English) / `README.ja.md` (日本語) / `README.es.md` (Español) /
    `README.ar.md` (العربية) / `README.fr.md` (Français) / `README.de.md` (Deutsch)
- 一部の言語だけの更新は禁止。バージョン番号・機能説明・比較表・FAQ・ロードマップ・フッターなど、**あらゆる変更を全 6 言語に反映**する。
- 各ファイル最上部の言語スイッチャーは全ファイルで同一（自言語のみ青ハイライト `5271FF`、他はダークグレー `30363D`）。
- README is multilingual (6 languages): **always update ALL of `README.md`, `README.ja.md`, `README.es.md`, `README.ar.md`, `README.fr.md`, `README.de.md` together.** Never update only some.
- 翻訳元は英語版 `README.md`。新機能はまず英語版を確定 → 各言語へ反映。

## バージョン同期 / Version Sync

- `due_diligence_engine/__init__.py` の `__version__` を Single Source of Truth (SSOT) とし、`tests/test_zero_drift_invariants.py` が以下すべてとの完全一致を機械的に検証・保護する:
1. `pyproject.toml` の `version`
2. `due_diligence_engine/__init__.py` の `__version__`
3. `due_diligence_engine/cli.py` の `@click.version_option(version=__version__)`
4. `due_diligence_engine/report/generator.py` のフッター文字列
5. 全 6 言語 README のバッジ `version-vX.Y.Z` とフッターの `` `vX.Y.Z` `` 行
6. `scorecard.html` テンプレート

## モデル ID と価格の SSOT / Model IDs & Pricing SSOT

- モデル定義・BYOKデフォルト・価格情報は `due_diligence_engine/config.py` の `MODELS`, `BYOK_DEFAULT_MODELS`, `PROVIDER_MODEL_COSTS` を Single Source of Truth (SSOT) とする。
- `ai.providers._DEFAULT_MODELS` や各プロバイダのコスト計算は SSOT から導出し、`tests/test_zero_drift_invariants.py` および `tests/test_model_ids.py` がドリフトを機械的に検出・遮断する。
- 更新時は必ず公式モデル一覧で実在とエイリアスを確認してから変更する（存在しない ID は API を壊す）。

## PDF レポートの検証 / PDF Verification

- `due_diligence_engine/report/pdf_generator.py` を変更したら、**実際に PDF を生成して目視確認**する:
  ```bash
  python3 -c "from pathlib import Path; from tests.test_consulting_pdf import _make_consulting_report, _make_analysis_result; from due_diligence_engine.report.pdf_generator import PDFReportGenerator; cr=_make_consulting_report(); ar=_make_analysis_result(cr); g=PDFReportGenerator(); g.generate_to_file(ar, Path('/tmp/dde_check_ja.pdf'), lang='ja'); g.generate_to_file(ar, Path('/tmp/dde_check_en.pdf'), lang='en'); print('OK')"
  ```
- Drawing 内の `String` 絶対座標描画は自動改行されない。日本語の長いラベルが領域（`label_w`）を超えて他要素に被らないか必ず確認する。

## テスト / Tests

- 変更後は必ず `python3 -m pip install -e .` 済みの環境で `python3 -m pytest tests/ -q` を実行（144 件 pass が基準）。
- CI（`.github/workflows/tests.yml`）が push/PR ごとに pytest を実行する（ubuntu / Python 3.11・3.12・3.13、Windows / macOS も含む）。
- モデル ID の整合は `tests/test_model_ids.py` が保護（日付サフィックス禁止・`config.MODELS` 以外でのハードコード禁止）。
- レッドフラグの誤検知ゼロ原則（ヒューリスティック誤検知のサイレント破棄・実コード欠陥のみ出力・パーサー安全弁 `_filter_red_flags`）は `tests/test_consulting_pdf.py::TestRedFlagZeroFalsePositiveNoise` が保護。
- レポート対応 14 言語は `tests/test_consulting_pdf.py::TestMultilingualReports` がスモークテストで保護（キー整合 + 全言語 PDF 生成）。言語を追加したら `ALL_REPORT_LANGS` にも追加すること。
- 全モジュール横断のセキュリティ・信頼性回帰（SSRF・Zip Slip・FIFO遮断・削除エラー伝播・store=False強制・ThinkingBlock走査等）は `tests/test_audit_regressions.py`（19件）が保護。

## リポジトリ / Repository

- 正式リポジトリ: `Atlas-Associates-Inc/Due-diligence-engine`
- 作者表記: Takayuki Miyano (@taka-avantgarde) / Atlas Associates Inc
