# Due Diligence Engine — プロジェクト規約 / Project Conventions

## ⚠️ ドキュメント同期（必須） / Doc Sync (MANDATORY)

- README は **6 言語すべてを同期更新**すること:
  - `README.md` (English) / `README.ja.md` (日本語) / `README.es.md` (Español) /
    `README.ar.md` (العربية) / `README.fr.md` (Français) / `README.de.md` (Deutsch)
- 一部の言語だけの更新は禁止。バージョン番号・機能説明・比較表・FAQ・ロードマップ・フッターなど、**あらゆる変更を全 6 言語に反映**する。
- 各ファイル最上部の言語スイッチャーは全ファイルで同一（自言語のみ青ハイライト `5271FF`、他は淡灰 `EEF2F7`）。
- README is multilingual (6 languages): **always update ALL of `README.md`, `README.ja.md`, `README.es.md`, `README.ar.md`, `README.fr.md`, `README.de.md` together.** Never update only some.
- 翻訳元は英語版 `README.md`。新機能はまず英語版を確定 → 各言語へ反映。

## バージョン同期 / Version Sync

リリース時、バージョン番号は以下 **4 箇所すべて**で揃える:
1. `pyproject.toml` の `version`
2. `src/cli.py` の `@click.version_option(version=...)`
3. 両 README のバッジ `version-vX.Y.Z`
4. 両 README フッターの `` `vX.Y.Z` `` 行

## モデル ID / Model IDs

- Claude モデル ID は `src/config.py` の `MODELS` 辞書で一元管理。
- 更新時は必ず[公式モデル一覧](https://platform.claude.com/docs/en/about-claude/models/overview)で実在とエイリアスを確認してから変更する（存在しない ID は API を壊す）。

## PDF レポートの検証 / PDF Verification

- `src/report/pdf_generator.py` を変更したら、**実際に PDF を生成して目視確認**する:
  ```bash
  python3 -c "from pathlib import Path; from tests.test_consulting_pdf import _make_consulting_report, _make_analysis_result; from src.report.pdf_generator import PDFReportGenerator; cr=_make_consulting_report(); ar=_make_analysis_result(cr); g=PDFReportGenerator(); g.generate_to_file(ar, Path('/tmp/dde_check_ja.pdf'), lang='ja'); g.generate_to_file(ar, Path('/tmp/dde_check_en.pdf'), lang='en'); print('OK')"
  ```
- Drawing 内の `String` 絶対座標描画は自動改行されない。日本語の長いラベルが領域（`label_w`）を超えて他要素に被らないか必ず確認する。

## テスト / Tests

- 変更後は必ず `python3 -m pip install -e .` 済みの環境で `python3 -m pytest tests/ -q` を実行（56 件 pass が基準）。
- CI（`.github/workflows/tests.yml`）が push/PR ごとに pytest を実行する（ubuntu / Python 3.11・3.12）。
- レポート対応 14 言語は `tests/test_consulting_pdf.py::TestMultilingualReports` がスモークテストで保護（キー整合 + 全言語 PDF 生成）。言語を追加したら `ALL_REPORT_LANGS` にも追加すること。

## リポジトリ / Repository

- 正式リポジトリ: `Atlas-Associates-Inc/Due-diligence-engine`
- 作者表記: Takayuki Miyano (@taka-avantgarde) / Atlas Associates Inc
