# Rule 00: SSOT & Zero-Drift Invariants

> **Scope**: Repository-wide architectural invariants.  
> **Enforcement**: Mechanically enforced by `tests/test_zero_drift_invariants.py` and `tests/test_model_ids.py`.

---

## 1. Version Invariant (SSOT: `due_diligence_engine/__init__.py`)
- The version string in `due_diligence_engine/__init__.py` (`__version__ = "X.Y.Z"`) is the absolute Single Source of Truth.
- The following files must strictly match `__version__`:
  1. `pyproject.toml` (`version = "X.Y.Z"`)
  2. `due_diligence_engine/cli.py` (`@click.version_option(version=__version__)`)
  3. `due_diligence_engine/report/generator.py` (Report footer string)
  4. All 6 READMEs: Badge `version-vX.Y.Z-5271FF` and footer line `` `vX.Y.Z` ``
  5. `scorecard.html` template (`due_diligence_engine/report/templates/scorecard.html`)
- Any mismatch causes immediate CI build termination.

---

## 2. Models & Pricing Invariant (SSOT: `due_diligence_engine/config.py`)
- Model identifiers, tier structures, BYOK defaults, and per-token pricing MUST only be declared in:
  - `due_diligence_engine/config.py` (`MODELS`, `PROVIDER_MODEL_COSTS`, `BYOK_DEFAULT_MODELS`).
- **Forbidden**:
  - Hardcoded model names or prices in `ai/providers.py` or elsewhere outside `config.py`.
  - Date-suffixed legacy model strings (e.g. `-2024`, `-2025`, `-latest`). Use dateless current-gen identifiers:
    - Claude: `claude-sonnet-5-5`, `claude-fable-5-1`, `claude-haiku-5-5`
    - Gemini: `gemini-4-argon`
    - OpenAI / Astra: `gpt-6.1-sol`, `gpt-6-astra`, `gpt-5`
  - Zero-cost fallbacks for active models; negative token numbers must be clamped to `0.0`.

---

## 3. 6-Language README Parity Invariant
- All 6 language editions of the README MUST be kept in perfect parity:
  - `README.md` (English)
  - `README.ja.md` (Japanese)
  - `README.es.md` (Spanish)
  - `README.ar.md` (Arabic)
  - `README.fr.md` (French)
  - `README.de.md` (German)
- CLI examples must include localized flags (e.g. `dde prompt --pdf --lang ja`).
- Stale strings (e.g. obsolete page counts, deprecated roadmap versions) are rejected by CI.

---

## 4. 14-Language PDF Dictionary Parity Invariant
- All 14 supported languages must have identical translation key sets across:
  - `_PDF_I18N`
  - `_DIM_NAME_MAPS`
  - `_PDF_GRADE_REC`
- Incomplete translations or missing keys will fail `TestMultilingualReports` and `test_fourteen_language_pdf_dictionary_parity_invariant`.
