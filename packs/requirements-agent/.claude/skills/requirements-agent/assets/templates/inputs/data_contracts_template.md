# Data Contracts

> Document source systems, interfaces, schemas, mappings, quality expectations,
> and constraints when they are relevant to the requested outputs.

## Source System 1: [Name]

### Overview
- **System Name:** [source or target system]
- **Provider / Owner:** [external provider or internal owner]
- **Data Type:** [records, events, documents, metrics, or other payload]
- **Delivery Method:** [e.g., SFTP weekly CSV drop; REST API pull every 15 min; Event stream via Kafka; Batch file drop]
- **Delivery Frequency:** [e.g., Weekly, every Monday; Real-time streaming; Daily at 02:00 UTC]
- **File Format:** [e.g., CSV pipe-delimited, JSON Lines, Parquet, API JSON]
- **Encoding:** [e.g., UTF-8]
- **Approximate Volume:** [e.g., ~500K rows per weekly file; ~20M events/day]

### Key Fields
| Field Name | Data Type | Description | PII? |
|-----------|-----------|-------------|------|
| [e.g., ndc_code] | [VARCHAR] | [National Drug Code] | [No] |
| [e.g., prescriber_id] | [VARCHAR] | [De-identified prescriber identifier] | [No] |
| [e.g., trx_units] | [INTEGER] | [Total prescription units] | [No] |

### SLAs
- [e.g., Data available by Tuesday 6 AM EST]
- [e.g., 99.5% availability]
- [e.g., Reconciliation within ±2% of vendor LAAD report]

### Known Issues
- [e.g., Historical data before 2020 uses a different product coding scheme]
- [e.g., ~3% of records have missing prescriber_id]

## Source System 2: [Name]

(Repeat the same structure for each source system)

## Cross-System Relationships
- [source identifier maps to canonical entity through a named key]
- [codes conform across systems through a governed reference]
- [records join through an evidenced relationship and grain]
