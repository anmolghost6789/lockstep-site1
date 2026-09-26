# Domain Context

> Provide domain-specific information that helps the agent understand the business area this data serves. This is separate from enterprise-level standards — it covers the specific business domain, its data sources, key entities, and domain-specific logic.

## Domain Overview

- **Domain / Business Area:** [e.g., Sales Analytics, Clinical Trials, Supply Chain, Customer 360]
- **Business Owner / Stakeholder:** [e.g., VP of Sales, Data Analytics Team]
- **Purpose:** [e.g., Build a unified sales reporting layer combining CRM, ERP, and e-commerce data]

## Key Business Entities

> List the major business entities in this domain and what they represent. This helps the agent understand what the tables mean, not just what they contain.

| Entity | Description | Source System | Key Identifier |
|--------|-------------|---------------|----------------|
| Customer | End consumer or business account | CRM | customer_id |
| Product | Item available for sale | ERP Product Master | product_id |
| Order | Sales transaction | E-Commerce Platform | order_id |
| Store | Physical retail location | Retail Ops | store_id |

## Source Systems

> Describe each source system that feeds data into this domain.

### Source System 1: [Name]

- **System Type:** [e.g., CRM, ERP, flat file, API, third-party vendor]
- **Data Format:** [e.g., CSV, Parquet, API JSON, database extract]
- **Delivery Method:** [e.g., SFTP drop, API pull, CDC stream, manual upload]
- **Delivery Frequency:** [e.g., daily at 2 AM UTC, real-time, weekly]
- **Data Quality Notes:** [e.g., customer emails are sometimes malformed, dates use mixed formats]
- **Known Quirks:** [e.g., historical data before 2020 uses a different customer ID scheme]

### Source System 2: [Name]

- **System Type:**
- **Data Format:**
- **Delivery Method:**
- **Delivery Frequency:**
- **Data Quality Notes:**
- **Known Quirks:**

> Add more source systems as needed.

## Domain-Specific Business Rules

> Describe business rules that are specific to this domain. These are rules that affect how data should be transformed, joined, filtered, or interpreted.

### Metrics and Calculations

| Metric | Definition | Notes |
|--------|-----------|-------|
| [e.g., Net Revenue] | [e.g., Quantity * Unit Price * (1 - Discount/100) - Returns] | [e.g., Excludes tax] |
| [e.g., Active Customer] | [e.g., Customer with at least one order in the last 12 months] | [e.g., Based on ORDER_DATE] |

### Classification Rules

> How are entities classified or segmented?

- [e.g., Customer segments: Enterprise (>$1M annual), SMB ($100K-$1M), Consumer (<$100K)]
- [e.g., Product status: ACTIVE = available for sale, DISCONTINUED = no longer sold but still in historical data]

### Temporal Rules

- **Fiscal Calendar:** [e.g., Standard calendar year, or fiscal year starts April 1]
- **Time Zone:** [e.g., All timestamps stored in UTC, reporting in local time]
- **Historical Retention:** [e.g., Keep 7 years of transactional history, 3 years of aggregated]

### SCD Behavior

> For dimensions that track history, describe the business expectation.

- [e.g., Customer segment changes should be tracked historically (SCD2) because reporting needs to show segment at time of sale]
- [e.g., Product name changes are overwritten (SCD1) because historical name is not meaningful]

## Domain Data Relationships

> Describe how the major entities relate to each other from a business perspective. The formal FK/PK relationships go in the Data Model template — this section is for business-level context.

- [e.g., A customer can have many orders. An order has many line items. Each line item refers to one product.]
- [e.g., Store-to-region mapping is maintained in a separate reference table updated quarterly.]
- [e.g., Some products are sold through multiple channels with different pricing — the price at time of sale is what matters.]

## Data Volume Expectations

| Table / Entity | Approximate Row Count | Growth Rate | Notes |
|---------------|----------------------|-------------|-------|
| [e.g., Orders] | [e.g., 2M rows] | [e.g., ~10K/day] | [e.g., Seasonal spike in Q4] |
| [e.g., Products] | [e.g., 50K rows] | [e.g., ~100/month] | [e.g., Slow growth] |
| [e.g., Customers] | [e.g., 500K rows] | [e.g., ~1K/day] | [e.g., Includes inactive] |

## Known Domain Gaps

> List things you know are incomplete, inconsistent, or problematic in this domain's data. This helps the agent set confidence levels appropriately.

- [e.g., Product cost data is missing for products loaded before 2022]
- [e.g., Some customer records have duplicate IDs across two legacy CRM systems — deduplication logic is still being defined]
- [e.g., Channel attribution for online orders is unreliable before March 2024]
