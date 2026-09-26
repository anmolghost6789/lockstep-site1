# Project Scope — Order Analytics Refresh (synthetic eval fixture)

## Objective
Replace the manual daily order export with an automated nightly pipeline so the
operations team sees the prior day's orders in the analytics dashboard each morning.

## In scope
- Nightly ingestion of the orders feed into the warehouse (charter REQ-014).
- On-time-delivery KPI surfaced on the dashboard.
- PII masking of customer contact fields before warehouse write.

## Out of scope
- Real-time/streaming ingestion.
- Dashboard redesign.

## Known open points
- Retention period for order records (5 vs 7 years — finance to confirm).
- "Fast" refresh expectation is not yet quantified.
