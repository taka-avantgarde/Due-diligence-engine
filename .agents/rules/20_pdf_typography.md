# Rule 20: PDF Typography & Multilingual Layout Safety

> **Scope**: ReportLab PDF generation, styling, font binding, and multi-script bidirectional text handling.  
> **Enforcement**: Mechanically verified by `tests/test_consulting_pdf.py` and visual PDF QA checks.

---

## 1. ReportLab 5.1 Layout Safety & Overflow Prevention
- All fixed-height layout cells (scorecards, callout banners, executive summaries) must be wrapped in `KeepInFrame` to prevent unexpected page breaks or clipping.
- Tables must explicitly define `colWidths`. Cells containing dynamic strings must use `Paragraph` objects rather than raw strings to ensure automated text wrapping.
- Drawing components (`Drawing`, `String`) use absolute coordinate systems without automated wrapping. Ensure label bounds (`label_w`, `x`, `y`) are dynamically calculated based on font size and string length to prevent visual collisions.

---

## 2. Right-to-Left (RTL) Arabic Shaping (`lang="ar"`)
- Arabic text requires both glyph shaping and bidirectional visual reordering.
- Use the Rust-accelerated `python-bidi` fast-path (`from bidi import get_display`) and `arabic_reshaper`.
- **Latin & Digit Isolation**:
  - Embedded Latin terms (e.g. "GitHub", "Python", "API", "SHA-256") and numerals within Arabic paragraphs must be wrapped or partitioned to prevent reversed numeric sequences (e.g., preventing "123" from rendering as "321").
  - Set font family explicitly to `Helvetica` or neutral font for Latin/numeric fragments embedded in RTL text blocks.

---

## 3. Complex Script Font Binding (Thai, Vietnamese, CJK)
- **Thai (`th`)**: Requires Thai-compatible TrueType font (e.g. `Sarabun`) with proper tonemark vertical stacking.
- **Vietnamese (`vi`)**: Ensure all diacritics (acute, grave, hook above, tilde, dot below) are fully rendered without font replacement tofu (`□`).
- **Zero Japanese Fallback Leakage**:
  - Never allow Japanese default fonts (`HeiseiMin-W3`, `NotoSansJP`) or untranslated Japanese labels (`技術`, `負債`, `スコア`) to leak into non-Japanese PDF editions (`en`, `es`, `fr`, `de`, `ar`, `th`, etc.).
  - Dimension names, grade descriptions, and recommendation badges must resolve strictly from their localized dictionary (`_DIM_NAME_MAPS[lang]`, `_PDF_GRADE_REC[lang]`).
