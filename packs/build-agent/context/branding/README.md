# `context/branding/`

DOCX rendering preferences for build deliverables (pipeline READMEs, runbooks, technical specs).

Drop a `branding_preferences.json` here matching the schema in `branding_preferences.example.json`. The `md_to_docx.py` renderer (under `.claude/skills/build-agent/scripts/`) reads it when exporting markdown to Word.
