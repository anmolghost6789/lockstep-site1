# source_inventory

Available source-system metadata and sample source data. This folder may contain the full source universe, not only sources that will be used in the current run. 03 - Discover_Sources selects the relevant sources after 02 - Standardize_Inputs builds the verified source universe.

Good inputs include:

- Source system inventory or data catalog export.
- Table/file lists with business descriptions.
- Column lists, data types, nullability, keys, and constraints.
- Primary key and foreign key definitions or candidates.
- Source-to-source relationship diagrams.
- Sample extracts with headers and representative values.
- DDL, schema exports, ERDs, catalog spreadsheets, CSV extracts, JSON/XML/YAML schema files.
- Source refresh frequency, volume, partition, CDC, and load-pattern notes.

Examples:

- `source_catalog_export.xlsx`
- `crm_tables_and_columns.csv`
- `erp_ddl.sql.txt`
- `raw_source_samples.zip`
- `source_relationships.pdf`

What the agent extracts:

- Systems, tables/files, columns, data types, keys, relationships, sample values, and confidence.
- The full verified source universe (`source_inventory.json`).
- Evidence IDs such as `SRC-014` used later in artifact `References` columns.

Do not worry if the inventory contains extra tables. Extra sources are normal; 03 - Discover_Sources will select what is needed.
