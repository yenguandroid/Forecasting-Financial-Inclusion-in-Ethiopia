"""
build_impact_refinements.py

Adds ONE new, data-calibrated impact_link record discovered during Task 3
validation: the starter/enriched dataset had NO impact_link connecting
Telebirr's launch (EVT_0001) directly to the Mobile Money Account Rate
(ACC_MM_ACCOUNT) indicator -- despite Telebirr obviously being the primary
driver of that indicator's existence. This produced a large validation gap
(see notebooks/task3_impact_modeling.ipynb, Section 5) that is closed here.

Calibration method (train/test style, not curve-fitting to both points):
  - TRAIN on the 2021-12-31 Findex checkpoint (4.7%), ~7.5 months after
    Telebirr's 17 May 2021 launch. At that point, Telebirr was the *only*
    mobile money product in the country, so essentially all of the observed
    4.7% can be attributed to it alone. This gives full_effect = 4.7 (pp),
    lag_months = 0. relationship_type is set to `direct`, which
    src/impact_model.py's RAMP_MONTHS_BY_RELATIONSHIP maps to a 3-month ramp
    (Telebirr's own effect is fully realized ~3 months after its launch,
    consistent with the 7.5-month-later Findex reading already showing the
    full 4.7% with no partial-ramp discount needed).
  - TEST on the 2024-11-29 Findex checkpoint (9.45%): combining this
    calibrated Telebirr effect (fully ramped: +4.7pp) with the existing
    M-Pesa link IMP_0007 (fully ramped by then: +5.0pp) predicts 9.7%,
    within 0.25pp (2.6% relative) of the actual 9.45% -- see the notebook
    for the full validation.

Run from the project root (after build_enrichment.py has already run):
    python build_impact_refinements.py
"""
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
ENRICHED_PATH = PROCESSED_DIR / "ethiopia_fi_unified_data_enriched.xlsx"
FINAL_PATH = PROCESSED_DIR / "ethiopia_fi_unified_data_final.xlsx"

COLLECTED_BY = "Yengusie Demilie Alene"  
COLLECTION_DATE = "2026-07-17"


def main():
    main_df = pd.read_excel(ENRICHED_PATH, sheet_name="ethiopia_fi_unified_data")
    links = pd.read_excel(ENRICHED_PATH, sheet_name="Impact_sheet")

    new_link = {c: None for c in links.columns}
    new_link.update(dict(
        record_id="IMP_0021", parent_id="EVT_0001", record_type="impact_link",
        pillar="ACCESS", indicator="Telebirr Launch effect on Mobile Money Account Rate (calibrated)",
        related_indicator="ACC_MM_ACCOUNT", relationship_type="direct",
        impact_direction="increase", impact_magnitude="high", impact_estimate=4.7,
        lag_months=0, evidence_basis="empirical", comparable_country=None,
        source_url="notebooks/task3_impact_modeling.ipynb#section-6-refine-your-estimates",
        confidence="medium", collected_by=COLLECTED_BY, collection_date=COLLECTION_DATE,
        notes=(
            "Calibrated (not independently sourced): the starter/enriched dataset had no "
            "impact_link from Telebirr's launch to ACC_MM_ACCOUNT at all, despite Telebirr "
            "being the obvious primary driver of that indicator's existence. Calibrated so "
            "that this link's fully-ramped effect (+4.7pp) matches the 2021-12-31 Findex "
            "reading (4.7%), when Telebirr was the only mobile money product in the market. "
            "Validated out-of-sample against the 2024-11-29 reading (9.45%): this link "
            "(+4.7pp, fully ramped) plus the existing M-Pesa link IMP_0007 (+5.0pp, fully "
            "ramped) predicts 9.7%, within 0.25pp of actual. Confidence set to medium, not "
            "high, because this is a single-point calibration, not an independently sourced "
            "estimate -- see notebooks/task3_impact_modeling.ipynb for full reasoning."
        ),
    ))

    links_refined = pd.concat([links, pd.DataFrame([new_link])[links.columns]], ignore_index=True)

    with pd.ExcelWriter(FINAL_PATH, engine="openpyxl") as writer:
        main_df.to_excel(writer, sheet_name="ethiopia_fi_unified_data", index=False)
        links_refined.to_excel(writer, sheet_name="Impact_sheet", index=False)

    main_df.to_csv(PROCESSED_DIR / "data.csv", index=False)
    links_refined.to_csv(PROCESSED_DIR / "impact_links.csv", index=False)

    print(f"impact_links: {len(links)} -> {len(links_refined)} (+1 calibrated link)")
    print(f"Written to {FINAL_PATH}")


if __name__ == "__main__":
    main()
