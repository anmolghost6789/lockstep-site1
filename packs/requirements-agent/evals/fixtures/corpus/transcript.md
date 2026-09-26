# Kickoff Workshop — Order Analytics Refresh (synthetic eval fixture)

Date: 2026-03-02 · Attendees: Priya (Product), Sam (Data Eng), Lena (Compliance)

**Priya:** The core need is that the operations team can see yesterday's orders
in the analytics dashboard each morning. Right now they wait for a manual export.

**Sam:** So we ingest the orders feed nightly and land it in the warehouse. The
dashboard reads from there. Requirement REQ-014 in the charter already covers the
nightly ingestion — let's keep that ID.

**Priya:** It should be fast — the team gets frustrated when it's slow.  <!-- vague, no number -->

**Sam:** We also want to track an on-time-delivery KPI on the dashboard.

**Priya:** Yes, on-time-delivery rate is the headline metric.  <!-- KPI named, NO target value given -->

**Lena:** Orders contain customer email and phone. Those are PII — they must be
masked before anything is written to the warehouse. Retention is 7 years for the
order records.

**Sam:** I had 5 years in my notes for retention, not 7.  <!-- contradiction: 5 vs 7 years -->

**Lena:** Let's flag that — finance owns the final retention number.

**Priya:** Failure handling: if the nightly feed is missing or malformed, the team
should be alerted and yesterday's data kept, not overwritten with empty data.
