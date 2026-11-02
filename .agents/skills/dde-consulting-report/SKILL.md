---
name: dde-consulting-report
description: Generate enterprise consulting PDF reports in the 14 supported languages using native MCP tools.
---

# Consulting report workflow

Run `dde mcp`, then follow [dde-audit](../dde-audit/SKILL.md) to prepare, list and read evidence.
Supported PDF languages: `en`, `ja`, `es`, `fr`, `de`, `pt`, `nl`, `it`, `id`, `zh`, `ko`, `vi`, `th`, `ar`.

Read `dde://schemas/consulting/v1`. Use five dimensions at 20% each: technical originality,
technology advancement, implementation depth, architecture quality, and claim consistency.
Every score is a finite number from 0 to 100. Use evidence to justify each score and red flag.
The Atlas four-axis assessment is supplementary and does not enter the five-axis average.

`dde_prepare_audit` arguments:
```json
{"target":"/path/to/repository","name":"Example","lang":"en","stage":"series_a"}
```

`dde_verify_sites` arguments (heuristic by default):
```json
{"audit_id":"<audit_id>","urls":["https://example.com"],"use_ai":false}
```

`dde_validate_report` arguments (minimal valid report; populate the optional SWOT, outlook,
strategy, investment thesis, site verification and competitor sections for a full report):
```json
{
  "audit_id": "<audit_id>",
  "snapshot_sha256": "<snapshot_sha256>",
  "report": {
    "project_name": "Example",
    "executive_summary": "Evidence-based assessment of the implementation.",
    "dimension_scores": {
      "technical_originality": {"score": 80, "rationale": "Evidence and reasoning"},
      "technology_advancement": {"score": 80, "rationale": "Evidence and reasoning"},
      "implementation_depth": {"score": 80, "rationale": "Evidence and reasoning"},
      "architecture_quality": {"score": 80, "rationale": "Evidence and reasoning"},
      "claim_consistency": {"score": 80, "rationale": "Evidence and reasoning"}
    },
    "overall_score": 80,
    "grade": "B",
    "red_flags": []
  }
}
```

Use the returned validation ID in `dde_render_report`:
```json
{"audit_id":"<audit_id>","validation_id":"<validation_id>","output_dir":"./dde_output","lang":"ja"}
```

The output is a PDF; page count depends on populated sections and content length.
Finally call `dde_close_audit(audit_id="<audit_id>")` and retain its signed purge certificate.
