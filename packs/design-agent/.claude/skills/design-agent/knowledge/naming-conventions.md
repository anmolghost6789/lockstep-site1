
# NAMING CONVENTIONS

## PRIORITY ORDER
1. Client-specific conventions (from input documents or human clarification) — ALWAYS first
2. Conventions observed in source data or completed project examples — second
3. Default conventions below — fallback

## DEFAULT TABLE NAMING

| Layer | Pattern | Example |
|-------|---------|---------|
| L0 (Raw) | `{l0_prefix}_{source_table_lower}` | `rw_jpm_trn` |
| L1 (Staging) | `{client_short}_{l1_prefix}_{source_short}_{entity}` | `az_wk_jpm_trn` |
| L2+ Dimension | `d_{entity}` | `d_atc`, `d_cmpny` |
| L2+ Fact | `f_{entity}` | `f_trn`, `f_sales` |
| L2+ Reference | `ref_{entity}` | `ref_composition` |
| L2+ Cross-Reference | `xref_{entity}` | `xref_pdt` |

Table names should be lowercase with underscores. Keep names concise but descriptive.

## DEFAULT COLUMN NAMING

- Convention: UPPER_SNAKE_CASE
- Examples: `CMPNY_CD`, `PACK_CD`, `ATC_SK`, `INRT_DT`
- Abbreviation rules:
  - Use standard abbreviations consistently: CD (Code), NM (Name), DT (Date), SK (Surrogate Key), ID (Identifier), AMT (Amount), QTY (Quantity), PCT (Percent), NUM (Number), DESC (Description), FLG (Flag), IND (Indicator), CAT (Category), TYP (Type), GRP (Group), LVL (Level)
  - Do NOT abbreviate if the result is ambiguous
  - Match client abbreviation style if they have one

## SURROGATE KEY NAMING

Pattern: `{TABLE_SHORT_NAME}_SK`
- `d_atc` → `ATC_SK`
- `d_cmpny` → `CMPNY_SK`
- `d_product` → `PDT_SK` or `PRODUCT_SK` (match client style)
- `f_trn` → composite key or `TRN_SK` depending on design

## SCHEMA NAMING

Default pattern: `{client_short}_{layer_prefix}`
- L0: `{client}_rw` (raw)
- L1: `{client}_wk` (work/staging)
- L2: `{client}_dw` (data warehouse)
- L3+: `{client}_dm` (data mart)

Example: `aicedp_jp_rw`, `aicedp_jp_wk`, `aicedp_jp_dw`

## DATABASE NAMING

Default pattern: `{client_db}_{env}`
- `{env}` is an environment placeholder that stays as literal text (e.g., `aicedp_db_{env}`)
- The actual environment (dev, qa, prod) is substituted at deployment time

## CRITICAL RULES

1. **Never mix conventions within a run.** If you learn the client uses a specific pattern, apply it everywhere.
2. **Preserve source column names in L0.** L0 columns mirror source exactly (only add SK and audit columns).
3. **Apply conventions starting from L1.** L1 and above use standardized names.
4. **When source has non-English column names** (e.g., Japanese), the L0 columns keep original names. L1+ columns use English equivalents with proper naming conventions.
5. **Do not guess abbreviations.** If unsure how to abbreviate a term, ask the human or use the full word.
