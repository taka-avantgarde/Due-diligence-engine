---
name: dde-dev-pdf-qa
description: Quality assurance workflow for validating 14-language PDF report rendering, bidirectional RTL text, and ReportLab typography.
---

# Skill: dde-dev-pdf-qa (PDF Typography & Multilingual QA)

This skill describes the QA process for ReportLab 5.1 PDF generation across all 14 supported languages, verifying font registration, bidirectional layout, and overflow protections.

---

## 1. Automated Multilingual PDF Smoke Test

Run the full 14-language report generation suite:
```bash
.venv/bin/python -m pytest tests/test_consulting_pdf.py -k "TestMultilingualReports" -v
```

This verifies:
- `_PDF_I18N` translation key completeness across all 14 languages.
- Successful PDF compilation without ReportLab exceptions.
- Font binding for Japanese, Chinese, Korean, Arabic, Thai, and Vietnamese.

---

## 2. Visual Inspection Script

To generate sample PDFs for manual visual inspection:
```bash
python3 -c "
from pathlib import Path
from tests.test_consulting_pdf import _make_consulting_report, _make_analysis_result
from due_diligence_engine.report.pdf_generator import PDFReportGenerator

cr = _make_consulting_report()
ar = _make_analysis_result(cr)
gen = PDFReportGenerator()

# Generate representative language samples
for lang in ['en', 'ja', 'ar', 'th', 'vi']:
    out = Path(f'dde_output/dde_qa_{lang}.pdf')
    gen.generate_to_file(ar, out, lang=lang)
    print(f'Rendered: {out} ({out.stat().st_size} bytes)')
"
```

---

## 3. Visual QA Checklist

When inspecting generated PDF files:
1. **Arabic (`ar`)**:
   - Verify Arabic letters are properly shaped (initial, medial, final, isolated forms).
   - Verify words read from Right-to-Left (RTL).
   - Verify Latin product names ("Python", "GitHub") and numbers ("10.0", "2026") are NOT visually reversed.
2. **Thai (`th`)**:
   - Check that upper tone marks and lower vowels stack correctly above/below consonants without overlapping adjacent characters.
3. **Japanese (`ja`) & CJK (`zh`, `ko`)**:
   - Confirm no tofu replacement glyphs (`□`) appear in table cells or headers.
4. **Layout Safety**:
   - In Drawing components, confirm text strings do not overflow past the canvas boundary.
   - Confirm `KeepInFrame` cells properly scale down content rather than spilling into unintended page breaks.

## Native MCP contract

Run `dde mcp`; use the seven-tool lifecycle in [dde-audit](../dde-audit/SKILL.md).
Use `target`, opaque `file_id`, `snapshot_sha256`, `report`, `validation_id` and `output_dir`
as defined there. The report uses `technical_originality`, `technology_advancement`,
`implementation_depth`, `architecture_quality`, `claim_consistency`: 0–100, 20% each.
PDF language keys: `en`, `ja`, `es`, `fr`, `de`, `pt`, `nl`, `it`, `id`, `zh`, `ko`, `vi`, `th`, `ar`.
