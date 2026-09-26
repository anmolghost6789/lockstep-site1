# DOCX export preferences

Read this only when branding or formatting instructions are present.

## Sources

The renderer loads these canonical files when present, in this order:

```text
context/branding/branding_preferences.json
context/branding/docx_export_preferences.json
```

The second file overrides the first. An explicit `--branding <file>` argument
loads only that file. The renderer never scans for arbitrary JSON files.

Use `.claude/skills/requirements-agent/assets/templates/inputs/docx_export_preferences.example.json`
as the shape guide.

## Supported fields

| Field | Scope |
|---|---|
| `client_name`, `project_name`, `logo_path` | Core branding |
| `primary_color`, `accent_color`, `font_name` | Core branding |
| `footer_text`, `confidentiality` | Core branding |
| `docx.font_name` | DOCX-specific |
| `docx.heading_color` | DOCX-specific |
| `docx.table_header_color` | DOCX-specific |
| `docx.footer_text`, `docx.confidentiality` | DOCX-specific |
| `docx.include_cover_page`, `docx.include_footer` | DOCX-specific |
| `docx.toc_max_level` | DOCX-specific |
| `docx.margins_inches.top|bottom|left|right` | DOCX-specific |

## Rules

- Convert free-form user instructions into supported JSON fields only.
- Record unsupported or ambiguous requests in open items or source notes.
- Persist normalized instructions to `context/branding/docx_export_preferences.json`.
- Set `logo_path` only when the intended logo is explicit. Prefer a run-root
  relative path such as `context/branding/logos/client-logo.png`.
- If `logo_path` is absent, export without a logo. If it is configured but
  missing or unusable, fail the export instead of silently omitting it.
- Markdown remains the source of truth; DOCX is an on-demand export.
