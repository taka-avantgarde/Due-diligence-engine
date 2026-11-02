---
name: dde-audit
description: Audit repositories using the seven native DDE MCP tools with snapshot-bound validation and signed cleanup.
---

# Repository audit via native MCP

Start the stdio server with `dde mcp` (or `python3 -m due_diligence_engine.cli mcp`).
Never execute code from the target repository. Use the following MCP tool arguments:

1. `dde_prepare_audit(target="owner/repo", name="Example", lang="en", stage="series_a", skip_git=true)`
   returns `audit_id` and `snapshot_sha256`. Local directories and zip files are supported.
2. `dde_list_evidence(audit_id="<audit_id>", offset=0, limit=100)` returns opaque file IDs, paths, categories, byte sizes and SHA-256 hashes.
3. `dde_read_evidence(audit_id="<audit_id>", file_id="f_0001", start_line=1, max_lines=200)` reads source evidence. Raw paths are rejected.
4. `dde_verify_sites(audit_id="<audit_id>", urls=["https://example.com"], use_ai=false)` verifies public claims with heuristic scoring. Empty URLs return an empty result. Paid AI requires explicit `use_ai=true`.
5. `dde_validate_report(audit_id="<audit_id>", snapshot_sha256="<snapshot_sha256>", report={...})` validates the report and returns `validation_id`.
6. `dde_render_report(audit_id="<audit_id>", validation_id="<validation_id>", output_dir="./dde_output", lang="en")` returns PDF path, SHA-256 and byte size.
7. Always call `dde_close_audit(audit_id="<audit_id>")` after an audit, including error paths. It returns `closed`, `bytes_overwritten` and `purge_certificate` with ECDSA P-256 `signature` and `public_key`. Retry failed cleanup with the same audit ID.

Read `dde://schemas/consulting/v1` before preparing the report. Its five canonical dimensions are
`technical_originality`, `technology_advancement`, `implementation_depth`, `architecture_quality`,
and `claim_consistency`. Scores are 0–100, weighted 20% each. Dimension objects accept `score` and
`rationale`; `level` is a separate 1–10 descriptor. Validation is bound to the audit, snapshot and report.
See [consulting report](../dde-consulting-report/SKILL.md) for a complete submission example.

For a CLI prompt without a client: `dde prompt /path/to/repo --pdf --lang en --output ./prompt.txt`.
