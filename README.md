# DSA Compliance Intelligence

A production-quality dbt + DuckDB analytics project for Digital Services Act (DSA)
transparency reporting. Built to demonstrate how compliance-oriented data infrastructure
should work: auditable, tested, documented, and fair

---

## Data Sources

**Primary:** DSA Transparency Report XLSX (2025 annual report)
- Sheet 5: Own-initiative illegal content enforcement
- Sheet 6: Own-initiative Terms and Conditions enforcement
- Sheet 7: Internal complaints and appeals data
- Sheet 8: Automated moderation system performance metrics
- Sheet 3: Government orders from EU member states
- Sheet 4: User-submitted notices and Trusted Flagger reports

**Secondary (attempted):** EU DSA Transparency Database API
- Endpoint: `https://transparency.dsa.ec.europa.eu/api/v1/statements`
- Status: API returned 405 during ingestion; gracefully skipped
- Architecture: ingestion pipeline handles this automatically

---

## Project Architecture

```
dsa-compliance-dbt/
|-- scripts/
|   |-- ingest.py           # Reads XLSX, writes to DuckDB raw schema + seed CSVs
|-- seeds/                  # CSV snapshots of each XLSX sheet
|-- models/
|   |-- staging/            # Source-faithful cleaning layer (views)
|   |   |-- stg_spotify_dsa_removals.sql
|   |   |-- stg_spotify_dsa_appeals.sql
|   |   |-- sources.yml
|   |   |-- schema.yml
|   |-- intermediate/       # Business logic and derived metrics (views)
|   |   |-- int_enforcement_trends.sql
|   |   |-- int_appeal_outcomes.sql
|   |   |-- int_enforcement_equity.sql
|   |   |-- schema.yml
|   |-- marts/              # Final tables for stakeholders (tables)
|       |-- mart_enforcement_summary.sql
|       |-- mart_regulatory_summary.sql
|       |-- mart_equity_audit.sql
|       |-- schema.yml
|-- macros/
|   |-- custom_macros.sql   # is_high_risk_category, safe_divide, period_over_period
|-- tests/
|   |-- assert_appeals_not_exceed_removals.sql
|-- dashboard.py            # Streamlit app
|-- profiles.yml            # dbt-duckdb connection config
|-- dbt_project.yml
```

**Why staging / intermediate / mart?** For non-technical readers:

- **Staging** is where raw data gets cleaned and standardized. Column names are
  normalized, nulls are handled, data types are cast. Nothing is derived yet.
- **Intermediate** is where business logic lives. This is where we compute appeal
  rates, automation ratios, trend rankings, and the equity metrics. Each model
  has a single, clear responsibility.
- **Marts** are the tables that stakeholders actually query. They join intermediate
  models together into denormalized, self-explanatory tables designed for specific
  audiences: legal teams, policy leads, dashboards.

---

## The Equity Audit

**What it measures:**

For each content category, we compute the enforcement rate as the category's removal
count relative to the per-category platform average. Categories where this rate exceeds
1.5x the average are flagged for potential disparate impact review.

We also compute:
- Z-scores: how many standard deviations above or below the mean each category sits
- Share deviation: each category's actual share of total removals vs its expected uniform share
- Severity tiers: critical (greater than 3x), high (greater than 2x), moderate (greater than 1.5x), within norms

**Why fairness metrics belong in T&S infrastructure:**

Content moderation decisions are not neutral. Automated systems trained on historical
data can encode existing biases, suppressing content from under-represented communities
at higher rates than the platform average. The 1.5x threshold is analogous to the
EEOC 4/5ths rule applied to content enforcement rather than employment.

Surfacing this in auditable, version-controlled dbt models means:
1. It runs automatically every time new data is ingested
2. It is testable (dbt tests validate the flags and severity classifications)
3. It is explainable: the methodology note is embedded in every row of `mart_equity_audit`
4. It creates an audit trail for DSA Article 34 systemic risk documentation

**What overturn rates would add:**

The public DSA report does not disclose category-level appeal outcomes. A production
version would join to an internal case management source to surface per-category
reversal rates. A category with a high removal rate *and* a high overturn rate is the
strongest signal of systematic over-enforcement.

---

## Technical Decisions

**Why dbt tests matter in compliance**

In most analytics pipelines, tests are optional. In compliance infrastructure, they
are the contract. Every `not_null`, `accepted_values`, and `unique` test is a
documented assertion about what the data guarantees. If the source data breaks one
of these assertions, the pipeline fails loudly rather than silently producing incorrect
reports.

The custom test `assert_appeals_not_exceed_removals` encodes domain logic: a user
cannot appeal a decision that was never made. If this test fails, it signals a join
error or data quality problem upstream, not a legitimate data anomaly.

**Why the LAG macro is structured the way it is**

The `period_over_period` macro wraps a `LAG()` window function. In a single-period
dataset (one annual report), time-series LAG does not show temporal change. The macro
is applied across category rankings to demonstrate the pattern. The model is designed
to produce meaningful time-series comparisons automatically once a second year of data
is ingested, without any schema changes.

**What a production version would add**

- Incremental models (`is_incremental()`) to efficiently process new reporting periods
- Source freshness checks with `freshness:` blocks in `sources.yml`
- Integration with internal case management data for category-level overturn rates
- dbt Cloud or Airflow orchestration for automated runs on report publication
- Row-level access controls for legal vs engineering audience segments
- Exposure definitions in `exposures.yml` linking marts to the dashboard

---

## How to run

**1. Install dependencies**

```bash
pip install dbt-duckdb pandas openpyxl requests streamlit plotly duckdb
```

**2. Run ingestion**

Place the DSA Transparency Report XLSX on your Desktop or in `data/`, then:

```bash
python scripts/ingest.py
```

This reads the XLSX, loads each sheet into the `raw` schema of `dev.duckdb`,
and saves seed CSVs to `seeds/`.

**3. Run dbt**

```bash
dbt seed          # Load seed CSVs
dbt run           # Build all models
dbt test          # Run all 53 tests
dbt docs generate # Build documentation site
dbt docs serve    # Open interactive DAG at localhost:8080
```

**4. Launch the dashboard**

```bash
streamlit run dashboard.py
```

---

## Test coverage

53 tests total:
- `not_null` on all key columns across all models
- `unique` on all primary keys
- `accepted_values` on categorical columns (enforcement_type, severity, trend_direction)
- Custom test: `assert_appeals_not_exceed_removals`
- Source schema validation via `sources.yml`
