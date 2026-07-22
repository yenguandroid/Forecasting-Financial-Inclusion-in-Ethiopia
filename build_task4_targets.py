"""
build_task4_targets.py

Task 4 forecasts two indicators: Account Ownership Rate (Access) and
Digital Payment Usage (Usage). ACC_OWNERSHIP already exists in the dataset
with 4 real Findex points (2014, 2017, 2021, 2024). However, no indicator
in the existing dataset matches Findex's actual "Digital Payment Usage"
definition (% of adults who made or received a digital payment in the past
year) -- the closest existing indicator, ACC_MM_ACCOUNT (Mobile Money
Account Rate), measures something related but different (having a mobile
money account, not having made/received ANY digital payment through any
channel).

Using ACC_MM_ACCOUNT as a stand-in for "Digital Payment Usage" would
materially overstate the forecast (it is on a much steeper trajectory:
4.7% -> 9.45%, 2021-2024). This script instead adds the real,
Findex-defined Digital Payment Usage figures for Ethiopia, researched and
cited below, so Task 4 forecasts the actual target the task specifies.

Sources (see full citations in data_enrichment_log_task4.md):
  - 2021: ~20% of Ethiopian adults made or received a digital payment
    (World Bank Africa Can End Poverty blog, based on Global Findex 2021).
  - 2024: ~21% (derived: AfricaNenda's Global Findex 2025 analysis reports
    Ethiopia's digital payment adoption grew "5%" in relative terms and by
    "just 1 percentage point" in absolute terms between 2021 and 2024 --
    solving for a base consistent with both figures gives ~20% -> ~21%).

Run from the project root (after build_impact_refinements.py has already run):
    python build_task4_targets.py
"""
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")
FINAL_PATH = PROCESSED_DIR / "ethiopia_fi_unified_data_final.xlsx"
TASK4_PATH = PROCESSED_DIR / "ethiopia_fi_unified_data_task4.xlsx"

COLLECTED_BY = "Yengusie Demilie Alene" 
COLLECTION_DATE = "2026-07-21"


def main():
    main_df = pd.read_excel(FINAL_PATH, sheet_name="ethiopia_fi_unified_data")
    links = pd.read_excel(FINAL_PATH, sheet_name="Impact_sheet")

    cols = main_df.columns.tolist()

    def blank_row():
        return {c: None for c in cols}

    def digital_payment_obs(record_id, observation_date, value_numeric, source_url,
                             original_text, confidence, notes):
        row = blank_row()
        row.update(dict(
            record_id=record_id, record_type="observation", pillar="USAGE",
            indicator="Digital Payment Usage", indicator_code="USG_DIGITAL_PAYMENT",
            indicator_direction="higher_better", value_numeric=value_numeric,
            value_type="percentage", unit="%",
            observation_date=pd.Timestamp(observation_date),
            fiscal_year=pd.Timestamp(observation_date).year,
            gender="all", location="national",
            source_name="World Bank Global Findex (via secondary analysis)",
            source_type="research", source_url=source_url, confidence=confidence,
            collected_by=COLLECTED_BY, collection_date=COLLECTION_DATE,
            original_text=original_text, notes=notes,
        ))
        return row

    new_rows = [
        digital_payment_obs(
            "REC_0042", "2021-12-31", 20.0,
            "https://blogs.worldbank.org/en/africacan/mobile-phone-technology-could-expand-equitable-access-financial-services-ethiopia",
            "Only 42% of account holders -- 20% of adults -- used their accounts for "
            "digital payments in the year prior to the Global Findex survey",
            "medium",
            "This is the Findex-defined 'Digital Payment Usage' target for Task 4 "
            "(% of adults who made or received a digital payment), NOT the same as "
            "ACC_MM_ACCOUNT (Mobile Money Account Rate). Distinguishing these matters: "
            "ACC_MM_ACCOUNT rose from 4.7% (2021) to 9.45% (2024), a much steeper "
            "trajectory than Digital Payment Usage's near-flat 20% -> ~21%. Confidence "
            "medium: figure is stated directly in a World Bank blog post but is itself "
            "a secondary restatement of the underlying 2021 Findex microdata, not a "
            "direct World Bank Findex table citation.",
        ),
        digital_payment_obs(
            "REC_0043", "2024-11-29", 21.0,
            "https://www.africanenda.org/en/blog/2025/the-global-findex-2025-could-instant-payments-be-driving-financial-inclusion-in-africa",
            "Ethiopia ... saw more modest growth of 5% in account ownership and 5% in "
            "digital payment adoption in the years after the launch of its IPS, "
            "EthSwitch ... the change appeared as a difference of just 1 percentage "
            "point between 2021 and 2024",
            "medium",
            "Value is DERIVED, not directly quoted: AfricaNenda's Global Findex 2025 "
            "analysis reports both a ~5% relative growth rate and a 1 percentage-point "
            "absolute change for Ethiopia's digital payment adoption between 2021 and "
            "2024. Solving x*1.05 - x = 1pp gives x ~ 20pp (2021) and ~21pp (2024), "
            "consistent with REC_0042's independently-sourced 2021 figure -- two "
            "independent sources triangulating on the same ~20% starting point. "
            "Confidence set to medium given the derivation step; treat this 2024 value "
            "as approximate (20.5-21.5% would be an equally defensible read of the "
            "same source).",
        ),
    ]

    main_task4 = pd.concat([main_df, pd.DataFrame(new_rows)[cols]], ignore_index=True)

    with pd.ExcelWriter(TASK4_PATH, engine="openpyxl") as writer:
        main_task4.to_excel(writer, sheet_name="ethiopia_fi_unified_data", index=False)
        links.to_excel(writer, sheet_name="Impact_sheet", index=False)

    main_task4.to_csv(PROCESSED_DIR / "data.csv", index=False)

    print(f"Main sheet: {len(main_df)} -> {len(main_task4)} records (+{len(new_rows)} Digital Payment Usage observations)")
    print(f"Written to {TASK4_PATH}")


if __name__ == "__main__":
    main()
