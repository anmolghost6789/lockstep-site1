# Branding and Document Preferences

Put reusable document branding and output preferences here, for example:

- Logo files
- Color/style guidance
- DOCX export preferences
- Footer/header text
- Confidentiality labels
- Client-approved document style rules

When users provide natural-language DOCX appearance instructions, normalize the
supported settings into `context/branding/docx_export_preferences.json`. Keep
logo files under this folder and reference the chosen logo with `logo_path`
when the intended logo is clear.

Branding affects presentation. It must not create requirements unless the user explicitly says it is a source requirement.
