# FILE PARSING UTILITIES

## GENERAL PRINCIPLES

1. **Parse from the run snapshot.** Read files from `outputs/00_state/input_snapshot/` and `outputs/00_state/midrun_uploads/`, not directly from mutable `inputs/` folders.
2. **Do not ask questions while parsing.** Record parser warnings and questions for `input_set_evaluation_report.md`.
3. **Use runtime code only when needed.** Any temporary helper code must live under `outputs/00_state/runtime_scratch/` (preserved after the run; no terminal cleanup). Read `.claude/skills/design-agent/utilities/runtime-code-policy.md`.
4. **Do not execute user-provided code.** `.py` files supplied by the user are text/reference inputs only.
5. **Preserve original text.** Preserve non-English characters, special symbols, casing, punctuation, line breaks, table/sheet/slide/page references, and original column names.
6. **Read completely.** Do not skip pages, sheets, slides, sections, or rows in specification documents. For very large source data files, profile enough rows for schema/type/sample inference while preserving row counts where available.
7. **Classify before parsing.** Determine if the file is data, describes data, defines business context/rules, or provides additional context, comparison material, or examples.
8. **Record evidence.** Every extracted item should know its file path and location inside the file.
9. **Use available libraries/tools.** Do not assume dependencies are installed. If a required parser is unavailable, use an alternate safe extraction method, record a warning, and ask for remediation in the input set evaluation report rather than silently skipping content.

## SUPPORTED INPUT FORMATS

```text
DOCX, TXT, XLSX, XLS, ZIP, PPTX, PPT, PDF, CSV, TSV, MD, PY, JSON, XML, YAML, YML
```

Case-insensitive extension matching is required.

## DEPENDENCY POLICY

The skill package is instruction-driven and does not ship pre-written parsing scripts. The agent may write temporary runtime code during a run, but only under `outputs/00_state/runtime_scratch/`.

If a package is missing:
1. Try a simpler built-in or command-line extraction path.
2. Record the limitation in the parser warning.
3. Add a question/action item to `input_set_evaluation_report.md` if the limitation affects input quality.
4. Install dependencies only if the environment and project permissions allow it or the human approves.

---

## DOCX PARSING

```python
from docx import Document

def parse_docx(filepath):
    doc = Document(filepath)
    result = {
        "paragraphs": [],
        "tables": [],
        "sections": []
    }
    
    current_section = {"heading": "Document Start", "level": 0, "content": [], "tables": []}
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        
        style_name = para.style.name if para.style else "Normal"
        
        # Detect heading
        if "Heading" in style_name:
            # Save previous section
            if current_section["content"] or current_section["tables"]:
                result["sections"].append(current_section)
            
            level = int(style_name[-1]) if style_name[-1].isdigit() else 1
            current_section = {"heading": text, "level": level, "content": [], "tables": []}
        else:
            current_section["content"].append({
                "text": text,
                "style": style_name,
                "is_list": "List" in style_name
            })
        
        result["paragraphs"].append({"text": text, "style": style_name})
    
    # Save last section
    result["sections"].append(current_section)
    
    # Extract all tables
    for t_idx, table in enumerate(doc.tables):
        parsed_table = {
            "index": t_idx,
            "rows": len(table.rows),
            "cols": len(table.columns),
            "headers": [cell.text.strip() for cell in table.rows[0].cells] if table.rows else [],
            "data": []
        }
        for row in table.rows[1:]:
            parsed_table["data"].append([cell.text.strip() for cell in row.cells])
        result["tables"].append(parsed_table)
    
    return result
```

**Key patterns to detect in DOCX:**
- Section 4 / "Data Sources": Extract source objects per entity
- Section 5 / "Business Rules": Extract per-entity transformation rules
- Section 6 / "Data Quality": Extract DQ rules if present
- Appendix tables: Often contain entity attribute definitions
- Tables with headers "Source Object" + "Description": Source listings
- Tables with headers "Attributes" + "Sample" + "Business Requirement": Entity specifications


## XLSX PARSING — SOURCE DATA FILES

```python
import openpyxl

def parse_xlsx_source_data(filepath):
    wb = openpyxl.load_workbook(filepath, read_only=True)
    result = {"sheets": []}
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        sheet_info = {
            "sheet_name": sheet_name,
            "max_row": ws.max_row,
            "max_col": ws.max_column,
            "columns": [],
            "header_row": None
        }
        
        # Find header row (first row with multiple non-null values)
        for row_idx in range(1, min(ws.max_row + 1, 10)):
            values = [ws.cell(row_idx, c).value for c in range(1, ws.max_column + 1)]
            non_null = [v for v in values if v is not None]
            if len(non_null) >= 2 and all(isinstance(v, str) for v in non_null):
                sheet_info["header_row"] = row_idx
                break
        
        if sheet_info["header_row"]:
            hr = sheet_info["header_row"]
            headers = [ws.cell(hr, c).value for c in range(1, ws.max_column + 1)]
            
            for col_idx, header in enumerate(headers):
                if header is None:
                    continue
                col_letter = openpyxl.utils.get_column_letter(col_idx + 1)
                
                # Sample values (first 100 non-null values after header)
                samples = []
                types_seen = set()
                for row_idx in range(hr + 1, min(ws.max_row + 1, hr + 101)):
                    val = ws.cell(row_idx, col_idx + 1).value
                    if val is not None:
                        samples.append(val)
                        types_seen.add(type(val).__name__)
                
                # Infer data type
                inferred_type = infer_data_type(samples, types_seen)
                
                sheet_info["columns"].append({
                    "column_name": str(header).strip(),
                    "column_index": col_idx + 1,
                    "inferred_type": inferred_type,
                    "sample_values": [str(s) for s in samples[:5]],
                    "non_null_count": len(samples),
                    "total_rows": ws.max_row - hr
                })
        
        result["sheets"].append(sheet_info)
    
    wb.close()
    return result

def infer_data_type(samples, types_seen):
    if not samples:
        return "VARCHAR"
    if types_seen == {"int"} or types_seen == {"int", "float"}:
        return "NUMBER"
    if types_seen == {"float"}:
        return "FLOAT"
    if "datetime" in str(types_seen):
        return "TIMESTAMP"
    return "VARCHAR"
```


## XLSX PARSING — SPECIFICATION FILES

Same as source data parsing, but also look for:
- Sheets that look like STTMs (headers: "Source Table", "Target Column", etc.)
- Sheets with entity metadata (headers: "Attributes", "Sample", "Business Requirement")
- Sheets with naming conventions or mapping guides


## CSV PARSING

```python
import pandas as pd

def parse_csv(filepath):
    # Try multiple encodings
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'shift-jis', 'cp1252']:
        try:
            df = pd.read_csv(filepath, encoding=encoding, nrows=5)
            break
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    
    # Full read
    df = pd.read_csv(filepath, encoding=encoding)
    
    result = {
        "encoding": encoding,
        "row_count": len(df),
        "columns": []
    }
    
    for col in df.columns:
        col_clean = col.strip().lstrip('\ufeff')  # Remove BOM if present
        result["columns"].append({
            "column_name": col_clean,
            "pandas_dtype": str(df[col].dtype),
            "inferred_type": pandas_to_sql_type(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "unique_count": int(df[col].nunique()),
            "sample_values": [str(v) for v in df[col].dropna().head(5).tolist()]
        })
    
    return result

def pandas_to_sql_type(dtype):
    dtype_str = str(dtype)
    if "int" in dtype_str: return "INTEGER"
    if "float" in dtype_str: return "FLOAT"
    if "datetime" in dtype_str: return "TIMESTAMP"
    if "bool" in dtype_str: return "BOOLEAN"
    return "VARCHAR"
```


## PDF PARSING

```python
import pdfplumber

def parse_pdf(filepath):
    result = {"pages": [], "tables": [], "full_text": ""}
    
    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            
            result["pages"].append({
                "page_number": page_num + 1,
                "text": text,
                "table_count": len(tables)
            })
            result["full_text"] += text + "\n"
            
            for table in tables:
                if table and len(table) > 1:
                    result["tables"].append({
                        "page": page_num + 1,
                        "headers": [str(c) for c in table[0]] if table[0] else [],
                        "rows": [[str(c) for c in row] for row in table[1:]]
                    })
    
    return result
```


## JSON PARSING

```python
import json

def parse_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {
        "type": type(data).__name__,  # dict, list, etc.
        "structure": describe_json_structure(data),
        "data": data
    }
    
    return result

def describe_json_structure(data, depth=0, max_depth=3):
    if depth > max_depth:
        return "..."
    if isinstance(data, dict):
        return {k: describe_json_structure(v, depth+1) for k, v in list(data.items())[:20]}
    if isinstance(data, list):
        if len(data) > 0:
            return [describe_json_structure(data[0], depth+1), f"... ({len(data)} items)"]
        return []
    return type(data).__name__
```


## TXT / MD PARSING

```python
def parse_text(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    result = {
        "line_count": len(lines),
        "sections": [],
        "key_value_pairs": [],
        "lists": []
    }
    
    current_section = {"heading": None, "content": []}
    for line in lines:
        stripped = line.strip()
        # Detect headers (Markdown # or ALL CAPS or underlined)
        if stripped.startswith('#') or (stripped.isupper() and len(stripped) > 3):
            if current_section["content"]:
                result["sections"].append(current_section)
            current_section = {"heading": stripped.lstrip('#').strip(), "content": []}
        elif ':' in stripped and len(stripped.split(':')[0]) < 40:
            key, value = stripped.split(':', 1)
            result["key_value_pairs"].append({"key": key.strip(), "value": value.strip()})
            current_section["content"].append(stripped)
        elif stripped.startswith(('-', '*', '•')) or (stripped and stripped[0].isdigit() and '.' in stripped[:4]):
            result["lists"].append(stripped)
            current_section["content"].append(stripped)
        else:
            current_section["content"].append(stripped)
    
    result["sections"].append(current_section)
    return result
```



## ZIP PARSING

```python
import zipfile, os, pathlib, shutil

def unpack_zip(filepath, target_root):
    # Extract into outputs/00_state/unpacked_inputs/{category}/{zip_stem}/
    # Never extract back into inputs/.
    out_dir = pathlib.Path(target_root) / pathlib.Path(filepath).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(filepath, 'r') as zf:
        for member in zf.infolist():
            # Prevent path traversal
            member_path = out_dir / member.filename
            if not str(member_path.resolve()).startswith(str(out_dir.resolve())):
                continue
            zf.extract(member, out_dir)
    return str(out_dir)
```

After unpacking, inventory and parse supported inner files. Preserve both the original zip path and the inner file path in evidence.

## PPTX / PPT PARSING

For PPTX:
- Extract slide text boxes.
- Extract tables.
- Extract speaker notes if accessible.
- Record slide number and shape/table location.
- If python-pptx is unavailable, PPTX is a zip of XML files; extract readable text from `ppt/slides/*.xml` and notes from `ppt/notesSlides/*.xml`.

For PPT:
- Use available conversion/extraction tools if present.
- If not available, record a parser warning and ask the human to provide PPTX/PDF export if the file is important.

```python
def parse_pptx(filepath):
    result = {"slides": [], "parser_warnings": []}
    try:
        from pptx import Presentation
        prs = Presentation(filepath)
        for idx, slide in enumerate(prs.slides, start=1):
            slide_obj = {"slide_number": idx, "texts": [], "tables": []}
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    slide_obj["texts"].append(shape.text)
                if getattr(shape, "has_table", False):
                    rows = []
                    for row in shape.table.rows:
                        rows.append([cell.text for cell in row.cells])
                    slide_obj["tables"].append(rows)
            result["slides"].append(slide_obj)
    except Exception as e:
        result["parser_warnings"].append(f"PPTX parser limitation: {e}")
    return result
```

## PY FILE PARSING

User-provided Python files are never executed. Parse as text and look for useful references:
- SQL strings.
- column lists or mapping dictionaries.
- transformation constants.
- comments explaining business logic.
- inputs/output table names.

```python
def parse_py_as_text(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    return {
        "line_count": len(content.splitlines()),
        "content": content,
        "possible_sql_fragments": [],
        "possible_mapping_hints": [],
        "note": "Parsed as text only; not executed."
    }
```

## XML PARSING

```python
import xml.etree.ElementTree as ET

def parse_xml(filepath):
    result = {"root_tag": None, "elements": [], "parser_warnings": []}
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        result["root_tag"] = root.tag
        for elem in root.iter():
            result["elements"].append({
                "tag": elem.tag,
                "attrib": dict(elem.attrib),
                "text": (elem.text or "").strip()[:1000]
            })
    except Exception as e:
        result["parser_warnings"].append(str(e))
    return result
```

## YAML / YML PARSING

```python
def parse_yaml(filepath):
    result = {"data": None, "parser_warnings": []}
    try:
        import yaml
        with open(filepath, 'r', encoding='utf-8') as f:
            result["data"] = yaml.safe_load(f)
    except Exception as e:
        # Fallback: parse as plain text
        result["parser_warnings"].append(f"YAML structured parse failed: {e}")
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            result["text"] = f.read()
    return result
```

## REFERENCE STORE FILE PARSING

When `/refresh-reference-store` is invoked, the agent must parse files in `context/reference/raw/` (which may contain organizational STTMs, data models, DQ specs, SQL scripts, BRDs, and past run outputs).

**Classification heuristics for reference store files:**

| File Indicators | Classification |
|----------------|---------------|
| Headers contain "Source to Target" / "STTM" / 17-column structure | STTM artifact |
| Headers contain "Data Model" / "Attribute Name" / 14-column structure | Data Model artifact |
| Headers contain "DQ" / "DQ Check" / "Criticality" / 12-column structure | DQ artifact |
| Headers like "Purpose", "Scope", "Business Requirements" | BRD / requirements |
| File contains SQL statements (CREATE TABLE, SELECT, INSERT) | SQL script |
| Other structured content | Other (extract any useful patterns) |

**For each classified file, extract:**
- Source tables referenced and their usage patterns
- Column mappings (source → target, with transformation logic)
- Known transformations by type
- Entity design patterns (grain, column structure, naming)
- DQ rules that were applied
- Domain-specific knowledge

Use the same parsing strategies defined above (DOCX, XLSX, CSV, PDF, JSON, TXT/MD) based on file type. Save extracted patterns to `context/reference/processed/` per the schemas in `.claude/skills/design-agent/utilities/input-schema.md`.
