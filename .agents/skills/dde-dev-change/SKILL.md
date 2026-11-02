---
name: dde-dev-change
description: Internal engineering workflow for updating versions, AI models, token pricing, 6-language READMEs, and scoring rubrics.
---

# Skill: dde-dev-change (Engineering Change & SSOT Synchronization)

This skill instructs engineers and executor agents on performing repository modifications safely while maintaining zero-drift invariants.

---

## 1. Updating Version String

When bumping the repository version (e.g. from `0.6.3` to `0.6.4`):
1. **SSOT Update**: Change `__version__ = "0.6.4"` in `due_diligence_engine/__init__.py`.
2. **Synchronize pyproject.toml**: Update `version = "0.6.4"`.
3. **Synchronize CLI**: Ensure `due_diligence_engine/cli.py` uses `__version__`.
4. **Synchronize 6 READMEs**:
   - `README.md`
   - `README.ja.md`
   - `README.es.md`
   - `README.ar.md`
   - `README.fr.md`
   - `README.de.md`
   - Update badge (`img.shields.io/badge/version-v0.6.4-5271FF`) and footer line (`` `v0.6.4` ``).
5. **Synchronize Scorecard Template**: Update `due_diligence_engine/report/templates/scorecard.html`.

---

## 2. Updating AI Models & Pricing

When adding a new model or updating pricing:
1. **SSOT Update (`due_diligence_engine/config.py`)**:
   - Add/update model in `MODELS` dict with dateless ID.
   - Update `PROVIDER_MODEL_COSTS` input/output rates per million tokens.
   - If default changes, update `BYOK_DEFAULT_MODELS`.
2. **Synchronize 6 READMEs**: Update model comparison tables across all 6 README files in lockstep.
3. **Verify Date Suffixes**: Ensure model IDs do not contain dates (`-2024`, `-2025`, etc.).

---

## 3. Verification & Guardrail Checks

Always execute both maintenance and invariant checks after modifying files:
```bash
# 1. Quick SSOT consistency check
python3 -m due_diligence_engine.maintenance check --profile quick

# 2. Invariants & unit test suite
.venv/bin/python -m pytest tests/test_zero_drift_invariants.py -v
.venv/bin/python -m pytest tests/ -q
```

## Native MCP contract

Run `dde mcp`; use the seven-tool lifecycle in [dde-audit](../dde-audit/SKILL.md).
Use `target`, opaque `file_id`, `snapshot_sha256`, `report`, `validation_id` and `output_dir`
as defined there. The report uses `technical_originality`, `technology_advancement`,
`implementation_depth`, `architecture_quality`, `claim_consistency`: 0–100, 20% each.
PDF language keys: `en`, `ja`, `es`, `fr`, `de`, `pt`, `nl`, `it`, `id`, `zh`, `ko`, `vi`, `th`, `ar`.
