# Known Gaps

> Document everything you know is incomplete, missing, or uncertain about the inputs for this build. Being explicit about gaps helps the agent set confidence levels honestly and avoid silent assumptions.
>
> The agent treats this file as real evidence. If you say something is missing here, the agent will not pretend it has the answer.

## Missing Source Schemas

> Source tables or columns referenced in the STTM but not fully defined.

| Source Table | What's Missing | Impact | Workaround |
|-------------|---------------|--------|------------|
| [e.g., erp_product_master] | [e.g., Full column list not provided — only mapped columns are known] | [e.g., Agent cannot validate unmapped source columns] | [e.g., Proceed with mapped columns only] |

## Unresolved Lookups

> Dimension lookups or reference data that is not yet available or defined.

| Lookup | From Table | To Table | Status | Notes |
|--------|-----------|----------|--------|-------|
| [e.g., Currency conversion] | [e.g., f_sales] | [e.g., ref_currency] | [e.g., Reference table not yet built] | [e.g., Hardcode to USD for now, flag for Phase 2] |

## Ambiguous Business Rules

> Rules that are partially defined or where the team has not yet reached a decision.

- [e.g., How to handle returns — should they be negative line items in f_sales or a separate f_returns table? Decision pending.]
- [e.g., Customer deduplication logic across legacy CRM systems is still being defined.]

## Incomplete Transformation Logic

> STTM rows where the Transformation Logic is vague, missing, or marked as TBD.

| Table | Column | Current Logic | What's Needed |
|-------|--------|--------------|---------------|
| [e.g., f_sales] | [e.g., CHANNEL_CD] | [e.g., "Direct mapping"] | [e.g., Source values are numeric codes — mapping to ONLINE/STORE/WHOLESALE not yet provided] |

## Data Quality Concerns

> Known DQ issues in source data that the build should account for.

- [e.g., ~5% of customer email addresses are malformed or NULL in the CRM export]
- [e.g., Order dates before 2021-01-01 are unreliable due to a system migration]
- [e.g., Some product IDs appear in orders but not in the product master — orphaned references]

## Temporary Placeholders

> Anything in the current inputs that is explicitly a placeholder and will be replaced later.

| Location | Placeholder | Expected Resolution |
|----------|------------|-------------------|
| [e.g., STTM d_customer.REGION] | [e.g., Transformation Logic says "TBD"] | [e.g., Waiting on regional mapping file from business team] |

## Missing Input Files

> Input categories that would improve the build but are not yet available.

- [e.g., No legacy SQL provided — agent will have to infer load patterns from STTM alone]
- [e.g., No formal data model — relationships will be inferred from STTM source/target references]
- [e.g., DQ rules not provided for L0 staging tables]

## Open Questions

> Questions that need answers from the business or technical team before the build can be fully confident.

1. [e.g., Should the product dimension include discontinued products or only active ones?]
2. [e.g., What is the correct grain for the sales fact — order line or order header?]
3. [e.g., Is the fiscal calendar standard (Jan-Dec) or custom?]
