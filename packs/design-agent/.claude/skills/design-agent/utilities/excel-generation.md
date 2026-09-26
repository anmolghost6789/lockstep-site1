
# EXCEL GENERATION UTILITIES

## LIBRARY SETUP

```python
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import os
import json
from pathlib import Path
```

## WINDOWS-SAFE FILE IO (mandatory)

Every text/JSON read and write in `generate_workbooks.py` and any companion Python script MUST pass `encoding='utf-8'` explicitly. Without it, Python on Windows uses the platform default (cp1252) and silently corrupts UTF-8 payloads — the source symbol `§` becomes `Â§`, em-dash `—` becomes `â€"`, and smart quotes become `â€œ`/`â€\x9d`. This is the exact mojibake bug observed in prior workbook runs.

```python
# CORRECT
design = json.loads(Path(path).read_text(encoding='utf-8'))
with open(path, 'r', encoding='utf-8') as f:
    design = json.load(f)
Path(out).write_text(mermaid_source, encoding='utf-8')

# WRONG — silently produces cp1252 on Windows
design = json.loads(Path(path).read_text())
with open(path, 'r') as f:
    design = json.load(f)
Path(out).write_text(mermaid_source)
```

openpyxl writes cell values as unicode strings internally, so as long as the Python string is correct (i.e., loaded via `encoding='utf-8'`), workbook cells will be correct.

## MERMAID ER MARKDOWN — DETERMINISTIC DERIVATION

Per-layer `ER_DIAGRAM_{layer}.md` and whole-flow `ER_DIAGRAM_LINEAGE.md` files MUST be produced by Python code that reads `outputs/00_state/design/column_mappings.json` and emits Mermaid from the columns actually present in the design. Do NOT let the model write these files freehand — every observed drift bug (invented columns, missing real columns) traced back to freehand writes.

```python
def build_layer_er_mermaid(column_mappings: dict, layer: str) -> str:
    """
    Emit an erDiagram block for a single layer, sourcing columns + PK/FK strictly
    from column_mappings.json. Never invent columns.
    """
    lines = ["```mermaid", "erDiagram"]
    tables = column_mappings.get("layers", {}).get(layer, {}).get("tables", {})
    for table_name, table in tables.items():
        lines.append(f"  {table_name} {{")
        for col in table.get("columns", []):
            dtype = col.get("data_type", "STRING")
            marker = ""
            if col.get("is_primary_key"):
                marker = " PK"
            elif col.get("is_foreign_key"):
                marker = " FK"
            lines.append(f"    {dtype} {col['name']}{marker}")
        lines.append("  }")
    # Semantic FK relationships if declared in the design
    for rel in column_mappings.get("layers", {}).get(layer, {}).get("relationships", []):
        lines.append(f"  {rel['from_table']} }}o--|| {rel['to_table']} : \"{rel.get('via', 'ref')}\"")
    lines.append("```")
    return "\n".join(lines)
```

## COMMENTS/REASON COLUMN DISCIPLINE

Design-side rationale fields (`threshold_value_reason`, `no_dq_reason`, `custom_sql_reason`, etc.) MUST NOT be added as new workbook columns. If a rule is `[NEEDS_HUMAN_REVIEW]` or `NO_DQ_APPLICABLE`, put the reason text in the existing `Comments` column of the DQ sheet; leave every other row's `Comments` cell as `-` unless the design has a genuine business comment. This keeps the workbook column schema stable and matches the templates.

## STYLE CONSTANTS

Apply consistent formatting matching the canonical templates:

```python
# Fonts
HEADER_FONT = Font(name='Calibri', size=11, bold=True)
SUBHEADER_FONT = Font(name='Calibri', size=11, bold=True)
LABEL_FONT = Font(name='Calibri', size=11, bold=True)
DATA_FONT = Font(name='Calibri', size=11)
COLUMN_HEADER_FONT = Font(name='Calibri', size=11, bold=True)

# Alignment
CENTER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT_ALIGN = Alignment(horizontal='left', vertical='top', wrap_text=True)
HEADER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)

# Fills — BMS brand palette (default). Section banners use BMS deep purple with
# white text; column headers use light lavender; label cells use the lightest tint.
# User branding can override these, but BMS is the default look.
HEADER_FILL = PatternFill(start_color='6E2585', end_color='6E2585', fill_type='solid')
SECTION_FILL = PatternFill(start_color='F5F0F5', end_color='F5F0F5', fill_type='solid')
COLUMN_HEADER_FILL = PatternFill(start_color='E8D5E7', end_color='E8D5E7', fill_type='solid')

# Header font for section headers (white text on BMS deep purple)
SECTION_HEADER_FONT = Font(name='Calibri', size=11, bold=True, color='FFFFFF')

# Border
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
```

## WORKBOOK CREATION PATTERNS

### Mandatory: The `_template_reference` sheet contract

Each STTM / DATA_MODEL / DQ template file ships with exactly two sheets:

1. `table_tracker` — index sheet. Keep row 1 headers (`S. No. | Table Name | Comments`) intact; replace all body rows with one row per current-run table.
2. `_template_reference` — a structural blueprint sheet that encodes the correct column layout, summary rows, detail header row, formatting, merged cells, and column widths for one target table. The generator MUST:
   - `copy_worksheet(_template_reference)` for each current-run table, rename the copy to the actual table name, and populate its cells with this run's values.
   - **Delete `_template_reference` from the workbook before `workbook.save()`** — it is a build-time blueprint and must never appear in a delivered artifact.

After save, the final workbook must contain only `table_tracker` plus one sheet per current-run table. Any sheet whose name starts with an underscore (`_`) is a build-time leftover and must be treated as a fatal phase error.

The ER_DIAGRAM template is different — its non-`table_tracker` sheets (`lineage_overview`, `table_relationships`, `layer_diagram_data`) are role-named structural sheets used as-is in the final workbook. Do NOT delete them.

Common dummy-content indicators to scrub from any legacy example rows you encounter: `sample`, `example`, `prototype`, `_template_reference` (as a value, not as a sheet name), plus any table/column values not present in the approved 04-Design / 05-Plan.

```python
def clear_template_sample_content(ws, header_row, detail_start_row, max_col):
    """
    Clear old/sample detail rows while preserving headers and formatting.
    Do not remove summary/header rows. Do not clear formulas or labels that belong to the template.
    """
    for row in range(detail_start_row, ws.max_row + 1):
        for col in range(1, max_col + 1):
            ws.cell(row=row, column=col).value = None

def clear_tracker_sample_rows(tracker_ws):
    """Clear table_tracker rows below the header before writing the current run table list."""
    for row in range(2, tracker_ws.max_row + 1):
        for col in range(1, 4):
            tracker_ws.cell(row=row, column=col).value = None
```

For copied table sheets, clear summary values that are table-specific before writing the current table metadata. Keep section labels and headers. For ER Diagram, clear all old/sample data rows from `lineage_overview`, `table_relationships`, and `layer_diagram_data` before writing current-run rows.



### Preferred: Create a Workbook from the Canonical Template

Use the uploaded workbook templates in `.claude/skills/design-agent/templates/workbooks/` as the preferred starting point for STTM, Data Model, DQ, and ER Diagram files. This preserves merged cells, widths, fills, borders, and template-specific formatting better than rebuilding from scratch. Create from scratch only if the template is missing or unreadable, and log that as a template warning.

```python
import copy
from openpyxl import load_workbook

def create_workbook_from_template(template_path, tables_list):
    """
    Create one layer workbook from a canonical template.
    - Keep table_tracker.
    - Use the existing sample table sheet as the style/layout prototype.
    - Duplicate the prototype once per target table.
    - Clear dummy/example/prototype data from copied sheets before population.
    - Remove the original prototype sheet after copies are created.
    """
    wb = load_workbook(template_path)
    if "table_tracker" not in wb.sheetnames:
        raise ValueError(f"Template missing table_tracker: {template_path}")

    tracker = wb["table_tracker"]
    prototype_names = [name for name in wb.sheetnames if name != "table_tracker"]
    if not prototype_names:
        raise ValueError(f"Template missing table prototype sheet: {template_path}")
    prototype = wb[prototype_names[0]]

    # Clear and rewrite table_tracker while preserving header styling.
    max_row = tracker.max_row
    for row in range(2, max_row + 1):
        for col in range(1, 4):
            tracker.cell(row=row, column=col).value = None

    for idx, table in enumerate(tables_list, 1):
        table_name = table["table_name"]
        tracker.cell(row=idx + 1, column=1, value=idx)
        tracker.cell(row=idx + 1, column=2, value=table_name)
        tracker.cell(row=idx + 1, column=3, value=table.get("comments", ""))

        ws = wb.copy_worksheet(prototype)
        ws.title = safe_sheet_name(table_name)

    wb.remove(prototype)
    return wb

def safe_sheet_name(name):
    # Excel sheet names max 31 chars and cannot contain: []:*?/ or backslash
    cleaned = str(name).replace("[", "_").replace("]", "_")
    for ch in [":", "*", "?", "/", "\\"]:
        cleaned = cleaned.replace(ch, "_")
    return cleaned[:31]
```

After creating sheets from the template, overwrite only the summary values, detail rows, and tracker rows required for the current table. Do not change headers, row positions, or required labels.

### Create a New Workbook with table_tracker

```python
def create_workbook_with_tracker(tables_list):
    """
    Create a new workbook with a table_tracker sheet.
    tables_list: list of dicts with 'table_name' and optional 'comments'
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "table_tracker"
    
    # Headers
    headers = ["S. No.", "Table Name", "Comments"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = COLUMN_HEADER_FONT
        cell.fill = COLUMN_HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = CENTER_ALIGN
    
    # Data rows
    for idx, table in enumerate(tables_list, 1):
        ws.cell(row=idx+1, column=1, value=idx).border = THIN_BORDER
        ws.cell(row=idx+1, column=2, value=table["table_name"]).border = THIN_BORDER
        ws.cell(row=idx+1, column=3, value=table.get("comments", "")).border = THIN_BORDER
    
    # Column widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 40
    
    return wb
```

### Create STTM Summary Section

```python
def write_sttm_summary(ws, metadata, total_cols=17):
    """
    Write the SOURCE TO TARGET - SUMMARY section (rows 1-7).
    metadata: dict with layer, description, loading_strategy, schema, database, frequency
    """
    last_col = get_column_letter(total_cols)
    
    # Row 1: Section header
    ws.merge_cells(f'A1:{last_col}1')
    cell = ws['A1']
    cell.value = "SOURCE TO TARGET - SUMMARY"
    cell.font = SECTION_HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = HEADER_ALIGN
    
    # Rows 2-7: Label-Value pairs
    summary_data = [
        ("Layer:", metadata.get("layer", "")),
        ("Table Description:", metadata.get("description", "")),
        ("Loading Strategy", metadata.get("loading_strategy", "")),
        ("Schema Name", metadata.get("schema_name", "")),
        ("Database Name", metadata.get("database_name", "")),
        ("Frequency", metadata.get("frequency", ""))
    ]
    
    for row_idx, (label, value) in enumerate(summary_data, start=2):
        # Merge label cells A:B
        ws.merge_cells(f'A{row_idx}:B{row_idx}')
        label_cell = ws[f'A{row_idx}']
        label_cell.value = label
        label_cell.font = LABEL_FONT
        label_cell.fill = SECTION_FILL
        label_cell.border = THIN_BORDER
        
        # Value in column C
        ws[f'C{row_idx}'] = value
        ws[f'C{row_idx}'].font = DATA_FONT
        ws[f'C{row_idx}'].border = THIN_BORDER
    
    # Row 8: Detail section header
    ws.merge_cells(f'A8:{last_col}8')
    cell = ws['A8']
    cell.value = "SOURCE TO TARGET - DETAILS"
    cell.font = SECTION_HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = HEADER_ALIGN
```

### Create Data Model Summary Section

```python
def write_dm_summary(ws, metadata, total_cols=14):
    """Same structure as STTM but with 'DATA MODEL - SUMMARY' header and 14 columns."""
    last_col = get_column_letter(total_cols)
    
    ws.merge_cells(f'A1:{last_col}1')
    cell = ws['A1']
    cell.value = "DATA MODEL - SUMMARY"
    cell.font = SECTION_HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = HEADER_ALIGN
    
    summary_data = [
        ("Layer:", metadata.get("layer", "")),
        ("Table Description:", metadata.get("description", "")),
        ("Loading Strategy", metadata.get("loading_strategy", "")),
        ("Schema Name", metadata.get("schema_name", "")),
        ("Database Name", metadata.get("database_name", "")),
        ("Frequency", metadata.get("frequency", ""))
    ]
    
    for row_idx, (label, value) in enumerate(summary_data, start=2):
        ws.merge_cells(f'A{row_idx}:B{row_idx}')
        label_cell = ws[f'A{row_idx}']
        label_cell.value = label
        label_cell.font = LABEL_FONT
        label_cell.fill = SECTION_FILL
        label_cell.border = THIN_BORDER
        
        ws.merge_cells(f'C{row_idx}:{last_col}{row_idx}')
        ws[f'C{row_idx}'] = value
        ws[f'C{row_idx}'].font = DATA_FONT
        ws[f'C{row_idx}'].border = THIN_BORDER
    
    ws.merge_cells(f'A8:{last_col}8')
    cell = ws['A8']
    cell.value = "DATA MODEL - DETAILS"
    cell.font = SECTION_HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = HEADER_ALIGN
```

### Create DQ Summary Section

```python
def write_dq_summary(ws, metadata, total_cols=12):
    """DQ summary has 6 rows (no Frequency), uses 'Table Name' in row 3."""
    last_col = get_column_letter(total_cols)
    
    ws.merge_cells(f'A1:{last_col}1')
    cell = ws['A1']
    cell.value = "DQ - SUMMARY"
    cell.font = SECTION_HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = HEADER_ALIGN
    
    summary_data = [
        ("Layer", metadata.get("layer", "")),
        ("Table Name", metadata.get("table_name_upper", "")),
        ("Table Description", metadata.get("description", "")),
        ("Schema Name", metadata.get("schema_name", "")),
        ("Database Name", metadata.get("database_name", ""))
    ]
    
    for row_idx, (label, value) in enumerate(summary_data, start=2):
        ws.merge_cells(f'A{row_idx}:B{row_idx}')
        label_cell = ws[f'A{row_idx}']
        label_cell.value = label
        label_cell.font = LABEL_FONT
        label_cell.fill = SECTION_FILL
        label_cell.border = THIN_BORDER
        
        ws.merge_cells(f'C{row_idx}:{last_col}{row_idx}')
        ws[f'C{row_idx}'] = value
        ws[f'C{row_idx}'].font = DATA_FONT
        ws[f'C{row_idx}'].border = THIN_BORDER
    
    # Row 7 (not 8): Detail header
    ws.merge_cells(f'A7:{last_col}7')
    cell = ws['A7']
    cell.value = "DQ - DETAILS"
    cell.font = SECTION_HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = HEADER_ALIGN
```

### Write Column Headers Row

```python
def write_column_headers(ws, headers, row_num):
    """Write column headers with formatting."""
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=row_num, column=col_idx, value=header)
        cell.font = COLUMN_HEADER_FONT
        cell.fill = COLUMN_HEADER_FILL
        cell.border = THIN_BORDER
        cell.alignment = CENTER_ALIGN
```

### Write Data Rows

```python
def write_data_rows(ws, data_rows, start_row, col_count):
    """Write data rows with formatting and borders."""
    for row_offset, row_data in enumerate(data_rows):
        row_num = start_row + row_offset
        for col_idx in range(1, col_count + 1):
            cell = ws.cell(row=row_num, column=col_idx)
            if col_idx <= len(row_data):
                cell.value = row_data[col_idx - 1]
            cell.font = DATA_FONT
            cell.border = THIN_BORDER
            cell.alignment = LEFT_ALIGN
```

## ER DIAGRAM TEMPLATE HANDLING

Use `.claude/skills/design-agent/templates/workbooks/ER_DIAGRAM_TEMPLATE.xlsx` for `outputs/ER_DIAGRAM.xlsx`. Required sheets are defined in `.claude/skills/design-agent/templates/specs/er-diagram-spec.md` and `.claude/skills/design-agent/specs/template_contracts.yaml`:

```text
table_tracker
lineage_overview
table_relationships
layer_diagram_data
```

Preserve and update `table_tracker`. Clear dummy/example detail rows in `lineage_overview`, `table_relationships`, and `layer_diagram_data` before writing current-run data. Preserve summary rows 1-8, section title row 9, and detail header row 10. If the ER template is missing, unreadable, or structurally incompatible, stop and report a template defect instead of silently creating an ad hoc ER workbook.

## SAVING WORKBOOKS

```python
def save_workbook(wb, output_dir, filename):
    """Save workbook, creating directories if needed."""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    wb.save(filepath)
    return filepath
```

## COLUMN WIDTH AUTO-ADJUSTMENT

```python
def auto_adjust_column_widths(ws, min_width=10, max_width=50):
    """Adjust column widths based on content."""
    for column_cells in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = min(max(max_length + 2, min_width), max_width)
        ws.column_dimensions[column_letter].width = adjusted_width
```

## REFERENCES COLUMN

Every populated detail row in STTM, Data Model, and DQ must have a non-empty References value. Use the row-level traceability policy in `.claude/skills/design-agent/utilities/traceability-reference-policy.md`. The generator should fail focused validation if a populated detail row has a blank References cell.

## IMPORTANT NOTES

- Always create the `table_tracker` sheet first
- Sheet names must be lowercase and match the table_tracker entries exactly
- Sheet names have a 31-character limit in Excel — truncate if needed
- Merged cells must be written BEFORE any data is put in the merged range
- Test that generated files open correctly in Excel by checking the file size (should be > 5KB)
