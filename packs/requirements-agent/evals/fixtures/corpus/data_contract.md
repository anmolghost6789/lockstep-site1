# Data Contract — Orders Feed (synthetic eval fixture)

Source: `orders_feed` (nightly CSV drop) → Target: `warehouse.fact_orders`

| Source field | Target column | Type | Notes |
|---|---|---|---|
| order_id | order_id | string | natural key |
| order_ts | order_ts | timestamp | source event time |
| customer_email | customer_email_masked | string | PII — mask before write |
| customer_phone | customer_phone_masked | string | PII — mask before write |
| delivered_on_time | delivered_on_time | boolean | feeds on-time-delivery KPI |
| amount | amount | decimal(12,2) | order value |

Load pattern: nightly full refresh of the prior day's partition. If the feed is
missing or fails structural validation, retain the existing partition and alert.
