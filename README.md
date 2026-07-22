# Ethiopia Financial Inclusion Forecast

A project to understand, enrich, and forecast Ethiopia's financial inclusion
trajectory (Access and Usage) using a unified events/observations/targets
dataset and modeled impact relationships.

## Project Status

- [x] Task 1 — Data Exploration and Enrichment
- [x] Task 2 — Exploratory Data Analysis
- [x] Task 3 — Event Impact Modeling
- [x] Task 4 — Forecasting Access and Usage (2025-2027)

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
   temporal coverage heatmap (indicator x year), and identification of
   9 of 20 indicators with 2 or fewer total observations.
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

## Task 3 Summary

`notebooks/task3_impact_modeling.ipynb` — translates `impact_links` records
into a working predictive model:

1. **Understand the impact data** — joins `impact_links` to events via
   `parent_id`, summarizing which events affect which indicators and by how
   much (2 links have no numeric estimate and are explicitly flagged rather
   than guessed at).
2. **Functional form** (`src/impact_model.py`) — each event's effect is a
   "ramped step": zero until `lag_months` after the event, then a **linear
   ramp** to its full estimated value over a `ramp_months` window (3/9/12
   months depending on whether the relationship is `direct`/`indirect`/
   `enabling`), held constant afterward. Multiple events combine additively.
3. **Comparable-country evidence** — 4 links (Kenya x2, Tanzania, India)
   reviewed and explicitly flagged as motivating, not validating, estimates.
4. **Association matrix** — events x indicators, signed estimated effect in
   each indicator's own unit. Exported to
   `reports/event_indicator_association_matrix.csv` and as a heatmap figure.
5. **Validation** — tested directly against the task's own example:
   Telebirr (May 2021) and Mobile Money Account Rate (4.7% -> 9.45%,
   2021-2024). The *original* linked data badly under-predicted this
   (0% and 5.0% respectively) because **no link existed connecting Telebirr
   to this indicator at all**.
6. **Refinement** — added one new, data-calibrated link (`IMP_0021`):
   trained on the 2021 checkpoint (+4.7pp), validated out-of-sample against
   the 2024 checkpoint (predicts 9.7% vs. actual 9.45%, 0.25pp error).
   Implemented in `build_impact_refinements.py`, producing
   `data/processed/ethiopia_fi_unified_data_final.xlsx`.
7. **Methodology, assumptions, and limitations** — fully documented in the
   notebook's final section, including what would most improve the model.

**Two real bugs found and fixed while building this** (both documented in
the notebook and git history): a sign-flip error that double-negated
`decrease`-direction links in the association matrix, and a color-scale
distortion in the heatmap caused by one indicator's absolute-count units
(1,000,000) swamping every percentage-point-scale cell.

Run the pipeline in order:
```bash
python build_enrichment.py            # Task 1 output
python build_impact_refinements.py    # Task 3 output (needs Task 1 output first)
pytest tests/ -v
```

## Task 4 Summary

`notebooks/task4_forecasting.ipynb` — forecasts both targets through 2027:

1. **Define targets** — Account Ownership Rate (Access, 4 real Findex
   points) and Digital Payment Usage (Usage). Corrected a target mix-up
   before forecasting anything: the existing `ACC_MM_ACCOUNT` indicator is
   NOT the same as Findex's "Digital Payment Usage" — researched and added
   the real, correctly-defined Usage figures instead (`build_task4_targets.py`,
   `data_enrichment_log_task4.md`). Also confirmed via research that
   Ethiopia has 4 real Findex points (2014-2024), not 5 (2011-2024) as the
   task brief's framing suggested — Ethiopia joined Findex in 2014.
2. **Select approach** — trend regression (linear AND log, compared
   directly), an event-augmented model reusing Task 3's `src/impact_model.py`
   (adding only the *incremental*, not-yet-realized portion of an event's
   effect to avoid double-counting), and scenario analysis.
3. **Generate forecasts** — baseline trend, with-events, and
   optimistic/base/pessimistic scenarios for 2025-2027, for both targets.
4. **Quantify uncertainty** — real OLS 95% prediction intervals for Access
   (n=4, flagged as wide/indicative given so few points); for Usage (n=2,
   zero residual degrees of freedom), an honest scenario range built from
   explicit stated growth-rate assumptions instead of a fabricated
   statistical interval (confirmed via test that statsmodels correctly
   returns NaN here rather than a misleadingly narrow interval).
5. **Interpret results** — the log trend (not linear) is used as the
   baseline, since linear extrapolation ignores Access's well-documented
   deceleration; the Fayda Digital ID rollout is identified as the single
   largest lever for Access in this window (its long lag means its full
   effect lands almost entirely in 2026); Usage is forecast essentially
   flat across every scenario through 2027.

Headline forecast (base scenario): **Access ~50% (2025) → ~61% (2026-2027)**,
missing the NFIS-II's 70%-by-2025 target under all but the most optimistic
assumptions; **Usage ~21-22%** through 2027, essentially unchanged from 2024.

New module: `src/forecasting.py` (trend fitting with prediction intervals,
incremental event-effect calculation, both scenario-building functions) —
14 new tests in `tests/test_forecasting.py`.

Run the full pipeline in order:
```bash
python build_enrichment.py            # Task 1 output
python build_impact_refinements.py    # Task 3 output
python build_task4_targets.py         # Task 4 output
pytest tests/ -v
```
