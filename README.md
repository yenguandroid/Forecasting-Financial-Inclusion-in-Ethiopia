# Ethiopia Financial Inclusion Forecast

A project to understand, enrich, and forecast Ethiopia's financial inclusion
trajectory (Access and Usage) using a unified events/observations/targets
dataset and modeled impact relationships.

## Project Status

- [x] Task 1 — Data Exploration and Enrichment
- [x] Task 2 — Exploratory Data Analysis
- [ ] Task 3 — (upcoming)

## Project Structure

```
├── .github/workflows/     # CI
├── data/
│   ├── raw/                # Starter dataset (as provided)
│   └── processed/          # Analysis-ready data
├── notebooks/               # Exploration notebooks
├── src/                     # Reusable analysis code
├── dashboard/                # app.py (Streamlit/Dash, upcoming task)
├── tests/                    # Unit tests
├── models/                   # Trained model artifacts (upcoming task)
├── reports/figures/          # Exported charts
├── requirements.txt
└── README.md
```

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Task 1 Summary

- `notebooks/task1_exploration.ipynb` — schema understanding + exploration
  (record counts by type/pillar/source/confidence, temporal range, indicator
  coverage, event catalog, impact_link review).
- `build_enrichment.py` — adds 8 new observations, 4 new events, and 6 new
  impact_links to the starter dataset, each with a real cited source. Run it
  from the project root:
  ```bash
  python build_enrichment.py
  ```
  Output: `data/processed/ethiopia_fi_unified_data_enriched.xlsx` (+ CSV exports).
- `data_enrichment_log.md` — full documentation of every addition (source,
  exact quote, confidence, rationale), plus a data-quality finding in the
  starter data itself.
- `tests/test_data_loader.py` — validates schema compliance, referential
  integrity (`impact_link.parent_id` -> real event, `related_indicator` ->
  real indicator_code), and that new records are complete.

Run the tests:
```bash
pytest tests/ -v
```

## Task 2 Summary

`notebooks/task2_eda.ipynb` — full EDA covering all 7 required areas:

1. **Dataset overview** — record/pillar/source/confidence breakdowns, a
   temporal coverage heatmap:  23 of 25 indicator_codes have 2 or fewer total observations — these cannot support any real trend analysis on their own and are better used as single reference points
  (e.g., "as of mid-2025, X was Y") than as time series. Only 2 indicators (most notably
  ACC_OWNERSHIP, with all 4 Findex survey waves) have enough observations to analyze
  an actual trend rather than a single snapshot or a two-point before/after comparison.
2. **Access analysis** — the account ownership trajectory (2014-2024) vs. the
   2025 NFIS-II target, growth rates between Findex waves, the gender gap,
   and a direct investigation of the 2021-2024 slowdown (+3pp despite 65M+
   mobile money accounts opened).
3. **Usage analysis** — mobile money penetration trend, the registered-vs-
   active gap (quantified: ~66% of M-Pesa's registered users are 90-day
   active), and P2P vs. ATM transaction volumes.
4. **Infrastructure & enablers** — 4G coverage, internet penetration, and
   Fayda digital ID enrollment trends, and a discussion of which could serve
   as leading indicators ahead of the next (~3-year-cadence) Findex survey.
5. **Event timeline** — all 14 cataloged events plotted and overlaid on the
   ownership/mobile-money and P2P trend charts, with an honest assessment of
   what can (and can't) be visually confirmed given the data's temporal
   resolution.
6. **Correlation analysis** — a deliberately-caveated approach given how
   sparse most indicators are (a formal correlation matrix would be
   statistically meaningless here), plus a full synthesis of the
   `impact_links` table itself (which pillars/indicators are most targeted,
   direction and evidence-basis breakdowns).
7. **Key insights & data quality assessment** — 5 documented insights, each
   with supporting evidence citations, plus a full data quality writeup
   (coverage gaps, confidence composition, and a genuine data-entry bug found
   and fixed during this analysis — see below).

**A bug found and fixed along the way:** while building this notebook, a
`TypeError` surfaced while loading the enriched dataset. Root cause: record
`REC_0006` (a critical 2024 Findex account-ownership observation) has its
`comparable_country` / `collected_by` / `collection_date` / `notes` columns
shifted by one in the **original starter data** — `collection_date` contains
free text instead of a date. `src/data_loader.py` was hardened to degrade
individual bad date cells to a missing value instead of crashing the whole
load, with a regression test guarding against it reappearing silently. The
underlying measured value (49%, ACC_OWNERSHIP) was unaffected and used as-is.

Figures are also exported to `reports/figures/` for use outside the notebook.

Run the tests (schema validation + regression checks + EDA-finding guards):
```bash
pytest tests/ -v
```
