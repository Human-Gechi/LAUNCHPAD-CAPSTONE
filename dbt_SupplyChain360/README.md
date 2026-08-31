# SupplyChain360 — dbt Project

A dbt project that transforms raw retail/supply-chain data (transactions, inventory, shipments, products, stores, suppliers, warehouses) into clean, analytics-ready models on Snowflake. The project follows a **staging → intermediate → marts** layering pattern, with most of the actual business logic — cleaning, enrichment, financial calculations, and status classification — expressed in SQL across those layers.

This README focuses on **what the SQL is doing** at each layer rather than just the dbt scaffolding.

---

## SQL Skills Demonstrated

This project is a working example of turning raw, messy operational data into business-usable metrics — the core of what's asked of a business analyst working with a data warehouse.

| Skill | Where it shows up |
|---|---|
| **Data cleaning & standardization** | Four reusable macros (`clean_id`, `clean_string`, `clean_number`, `clean_decimal`) apply consistent type-casting, null-handling, and default values across every source table, instead of repeating logic per model |
| **Defensive query design** | `abs()` guards against bad negative values from source; `nullif()` prevents divide-by-zero in every ratio/percentage calculation; fallback ID sentinels prevent silent row loss on `NULL` joins |
| **Translating business rules into SQL** | Profit/loss classification, inventory stock-status tiers, delivery delay classification, and warehouse efficiency ratings are all built from nested `CASE` logic tied to real operational thresholds |
| **Financial calculation** | Gross revenue, cost basis, discount amount, net profit/loss, and profit margin % are computed and tiered into a `financial_status` per transaction — effectively a P&L calculation in SQL |
| **KPI construction** | Delivery delay days, transit days, and warehouse error rate (`total_internal_delays / total_shipments_processed`) are derived metrics feeding directly into operational ratings |
| **Aggregation & grain control** | Fact tables aggregate to deliberately chosen grains (product/store/supplier, region, warehouse) using `SUM`, `AVG`, `COUNT(DISTINCT ...)`, and `MIN`/`MAX` |
| **Data quality testing** | Four custom SQL tests (`positive_value`, `no_whitespace`, `is_date_type`, `assert_shipment_date`) validate the data automatically rather than trusting it on faith |
| **Change tracking** | Type-2 snapshots (`strategy='check'`) capture how dimension attributes (price, category, region, etc.) change over time |
| **Incremental/production thinking** | `is_incremental()` watermarking on `ingestion_date` means re-running the project only processes new data, not the full history |

---

## Data Flow

```
sources (raw tables)
   │
   ▼
staging/          → 1:1 cleaned views/incremental models per source table
   │
   ▼
intermediate/     → joins + business-rule calculations (profit, delays, stock health)
   │
   ▼
marts/            → dimension & fact tables, aggregated for reporting
```

Sources cover seven raw tables: `transactions`, `inventory`, `products`, `stores`, `suppliers`, `warehouses`, and `shipments`, each ingested from a mix of RDS, S3, and Sheets extracts (tracked via `origin` and `*_extraction_date` columns carried through every staging model).

---

## Staging Layer (`models/staging/`)

Each staging model does the same job: take a raw source table and produce a de-duplicated, type-safe, standardized version of it. The heavy lifting is done through **four reusable macros** rather than repeating cleaning logic per model:

| Macro | Purpose | SQL pattern |
|---|---|---|
| `clean_id(column, default)` | Standardizes ID columns | `upper(trim(coalesce(cast(col as varchar), default)))` |
| `clean_string(column, default)` | Standardizes free-text columns | `trim(coalesce(cast(col as varchar), default))` |
| `clean_number(column, default)` | Standardizes integer-like columns | `coalesce(abs(cast(col as number)), default)` |
| `clean_decimal(column, default)` | Standardizes money/decimal columns | `coalesce(abs(cast(col as decimal(10,2))), default)` |

Using `abs()` inside `clean_number`/`clean_decimal` guards against negative values slipping through from source (e.g. a negative `quantity_sold`), and every ID gets a fallback sentinel (`'PROD-XXXX'`, `'STORE-XXXX'`, `'WH-XXX'`, etc.) so joins downstream never silently drop rows on `NULL`.

A few staging models go beyond simple cleaning:

- **`stg_transactions.sql`** — computes `net_revenue` inline as
  `quantity_sold * unit_price * (1 - discount_pct)`, cast to `decimal(10,2)`, and converts a microsecond epoch (`transaction_timestamp`) into a proper `timestamp_tz` via `to_timestamp_tz(cast(... as number) / 1000000)`.
- **`stg_stores.sql`** — normalizes inconsistent inbound date formats for `store_open_date` by trying three patterns in sequence (`DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD`) with `coalesce`, falling back to `current_date` if none parse.
- **`stg_transactions`, `stg_shipments`, `stg_inventory`** are `materialized: incremental`, filtered with `WHERE ingestion_date > (SELECT max(ingestion_date) FROM {{ this }})` — so re-running the project only processes newly-ingested rows rather than the full source history.

All staging models are `SELECT DISTINCT` to absorb duplicate rows introduced by upstream extraction.

---

## Intermediate Layer (`models/intermediate/`)

This is where the raw, cleaned tables get joined together and turned into business metrics. Each model encodes a specific rule set as a `CASE` expression:

- **`int_transactions_enriched.sql`** — joins transactions to products, then computes:
  - `gross_revenue` = `quantity_sold * selling_unit_price`
  - `total_expenses` = `quantity_sold * supplier_unit_price` (cost basis, from the product record rather than the sale)
  - `discount_amount` = `gross_revenue - net_revenue`
  - `net_profit_loss` = `net_revenue - total_expenses`
  - `profit_margin_pct` = `(net_profit_loss / gross_revenue) * 100`, guarded with `nullif()` to avoid divide-by-zero
  - `financial_status` — a `CASE` that buckets each transaction into `Loss`, `Breakeven`, `Profit (Discounted)`, or `Full Profit (No Discount)` by comparing revenue, expenses, and gross revenue.

- **`int_inventory_health.sql`** — joins inventory to products and derives `stock_to_threshold_ratio = quantity_available / reorder_threshold`, then classifies each warehouse/product pair into `Stock-Out`, `Below Reorder Threshold`, `Healthy` (ratio between 1.0–3.0), or `Sufficient`.

- **`int_shipments_performance.sql`** — joins shipments to products and stores, computes `delivery_delay_days` via `DATEDIFF(DAY, expected_delivery_date, actual_delivery_date)`, and classifies each shipment as `Early`, `Late`, or `On time`.

- **`int_warehouse_to_store_efficiency.sql`** — joins shipments to both stores and warehouses to classify the shipping lane (`Local (Same City)`, `Regional (Same State)`, `Long-Haul (Inter-State)`) and combines that with `transit_days` (`DATEDIFF('day', shipment_date, actual_delivery_date)`) to flag `High Delay Risk`, `Warehouse Delay`, or `Good Route`.

- **`int_supplier_products.sql`** — a straightforward `LEFT JOIN` linking every product back to its supplier's name, category, and country; kept as a `view` since it does no aggregation.

Most intermediate models are `materialized: incremental`, keyed on natural composite keys (e.g. `['shipment_id', 'warehouse_id']`, `['warehouse_id', 'store_id', 'shipment_id']`) so re-runs only reprocess new `ingestion_date` batches.

---

## Marts Layer (`models/marts/`)

Marts are `materialized: table` and split into dimensions and facts:

**Dimensions** (`dim_products`, `dim_stores`, `dim_supplier`, `dim_warehouses`) are thin, deduplicated selects off the staging layer — no additional logic, just the columns needed for BI joins.

**Facts** carry the aggregation logic:

- **`fct_transactions.sql`** — grains down to `product_id, store_id, supplier_id` (plus product attributes) and aggregates `int_transactions_enriched` into totals (`total_quantity_sold`, `total_gross_revenue`, `total_net_revenue`, `total_net_profit_loss`), an averaged `avg_profit_margin_pct`, a distinct transaction count, and first/last transaction dates.
- **`fct_regional_sales.sql`** — joins transactions to stores and rolls sales up to `region` level (`total_quantity_sold`, `total_revenue`).
- **`fct_inventory.sql`** — a pass-through select of the pre-computed stock health fields from `int_inventory_health`.
- **`fct_warehouse_efficiency.sql`** — aggregates `int_warehouse_to_store_efficiency` per warehouse: `total_shipments_processed` (distinct shipment count), `avg_transit_days`, `total_internal_delays` (count of `Warehouse Delay` routes), then derives `warehouse_error_rate_pct = total_internal_delays * 100.0 / total_shipments_processed` and an `efficiency_rating` (`High Efficiency` < 5% error rate, `Standard` 5–15%, else `Bottleneck Detected`).

---

## Testing (`tests/generic/`)

Four custom generic tests enforce data quality rules directly in SQL:

- **`positive_value`** — fails if any row in a column is `< 0`.
- **`no_whitespace`** — fails if a column's value differs from its trimmed version (catches leading/trailing whitespace that slipped past cleaning).
- **`is_date_type`** — fails if a column can't be parsed by `TRY_TO_DATE`, used to validate that "date-looking" columns are actually valid dates.
- **`assert_shipment_date`** (singular test) — fails if any shipment's `shipment_date` is on/after its `actual_delivery_date` or `expected_delivery_date`, catching logically impossible shipment timelines.

## Snapshots (`snapshots/`)

Type-2 (`strategy='check'`) snapshots track slowly-changing attributes over time for `products`, `stores`, `suppliers`, and `warehouses` — e.g. a product's `unit_price`, `category`, or `brand` changing, or a store's `region` or `store_open_date` changing — with `invalidate_hard_delete=True` so hard-deleted source rows are marked invalid rather than silently dropped.

## Analyses (`analyses/`)

`top_products.sql` — an ad-hoc query (not materialized) against `int_inventory_health` that surfaces the top 10 product/warehouse combinations by stockout event count.

---

## Project Config

- **Warehouse:** Snowflake (`profile: snowflake_credentials`)
- **Schema routing:** `STAGING_SUPPLYCHAIN`, `INTERMEDIATE_SUPPLYCHAIN`, `MARTS_SUPPLYCHAIN` — set per-layer in `dbt_project.yml`, with a custom `generate_schema_name` macro that uses the custom schema name directly rather than the default `<target_schema>_<custom_schema>` concatenation dbt normally applies.
- **Materializations by layer:** staging → `view`, intermediate → `incremental`, marts → `table`.

## Running the Project

```bash
dbt run          # build all models in dependency order
dbt test         # run schema + custom generic tests
dbt snapshot      # capture slowly-changing dimension state
```
