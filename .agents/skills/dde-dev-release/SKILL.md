---
name: dde-dev-release
description: Pre-release verification workflow covering maintenance profile release checks, wheel packaging, and security vulnerability audits.
---

# Skill: dde-dev-release (Release Verification & Distribution QA)

This skill guides engineers through the pre-release checklist, ensuring code health, clean packaging, and security audits before tagging or publishing a new release.

---

## 1. Pre-Release Verification Gates

Run the comprehensive maintenance release profile:
```bash
# 1. Maintenance release gate
python3 -m due_diligence_engine.maintenance check --profile release

# 2. Complete test suite with coverage
.venv/bin/python -m pytest tests/ -q --cov=due_diligence_engine --cov-report=term-missing
```

The release profile verifies:
- SSOT version alignment across all targets (`__init__.py`, `pyproject.toml`, CLI, 6 READMEs, scorecard HTML).
- Model and pricing consistency across providers and configurations.
- Zero stale documentation strings.
- 14-language PDF dictionary parity.
- Review Git status separately; the maintenance CLI does not enforce a clean worktree.

---

## 2. Wheel Packaging Verification

Build and inspect the distributable source archive and wheel:
```bash
# Build package
.venv/bin/python -m pip install --upgrade build twine
.venv/bin/python -m build

# Validate wheel metadata and package contents
.venv/bin/twine check dist/*
```

Verify that:
- Source tree does not bundle sensitive fixtures, `.env` files, or temporary test outputs.
- `templates/scorecard.html` and package assets are properly packaged inside the wheel.

---

## 3. Dependency & Security Audits

Verify dependencies against known vulnerabilities:
```bash
# Check dependencies using pip-audit
.venv/bin/python -m pip_audit --skip-editable --desc
```

Ensure no critical or high severity vulnerabilities exist prior to distribution.

## Native MCP contract

Run `dde mcp`; use the seven-tool lifecycle in [dde-audit](../dde-audit/SKILL.md).
Use `target`, opaque `file_id`, `snapshot_sha256`, `report`, `validation_id` and `output_dir`
as defined there. The report uses `technical_originality`, `technology_advancement`,
`implementation_depth`, `architecture_quality`, `claim_consistency`: 0–100, 20% each.
PDF language keys: `en`, `ja`, `es`, `fr`, `de`, `pt`, `nl`, `it`, `id`, `zh`, `ko`, `vi`, `th`, `ar`.
