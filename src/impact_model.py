"""
impact_model.py

Translates impact_link records (event -> indicator relationships) into a
simple, transparent time-dynamic model that can predict how an indicator
moves in response to one or more events.

Modeling convention (documented in notebooks/task3_impact_modeling.ipynb):
  - `impact_estimate` is interpreted as an absolute change in the indicator's
    own unit: percentage points for `percentage`/`gap_pp` value_types, and
    absolute counts/currency for `count`/`currency_etb` value_types.
  - An event's effect on an indicator does NOT appear immediately. It is
    zero until `lag_months` after the event date, then ramps up LINEARLY
    over a `ramp_months` window to its full estimated value, and holds at
    that full value afterward (a "ramped step" function). This reflects
    behavioral/adoption responses building gradually rather than jumping
    instantly, while still respecting the lag before any effect begins.
  - `ramp_months` defaults to 6, but is shortened for `direct` relationships
    (effects show up faster) and lengthened for `enabling` relationships
    (effects require a downstream product/behavior change first).
  - Effects from multiple events on the same indicator are combined
    ADDITIVELY (independent, no interaction/saturation terms) -- a
    deliberate simplification, documented as a limitation.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

RAMP_MONTHS_BY_RELATIONSHIP = {
    "direct": 3,
    "indirect": 9,
    "enabling": 12,
}
DEFAULT_RAMP_MONTHS = 6

MAGNITUDE_FALLBACK_PP = {"low": 2.0, "medium": 6.0, "high": 12.0}


def months_between(start: pd.Timestamp, end: pd.Timestamp) -> float:
    """Fractional number of months from `start` to `end` (can be negative)."""
    return (end - start).days / 30.4375


def ramp_fraction(months_since_lag_end: float, ramp_months: float) -> float:
    """
    Fraction (0 to 1) of an event's full effect that has materialized.
    0 before the lag ends, linearly increasing to 1 over `ramp_months`,
    held at 1 thereafter.
    """
    if months_since_lag_end <= 0:
        return 0.0
    if ramp_months <= 0:
        return 1.0
    return min(1.0, months_since_lag_end / ramp_months)


def resolve_ramp_months(relationship_type: str) -> float:
    return RAMP_MONTHS_BY_RELATIONSHIP.get(relationship_type, DEFAULT_RAMP_MONTHS)


def resolve_effect_size(link_row: pd.Series) -> float:
    """
    Full (fully-ramped) effect size in the target indicator's own units,
    signed by impact_direction. Uses `impact_estimate` when present;
    otherwise falls back to a magnitude-based heuristic (documented as
    lower-confidence in the notebook).
    """
    sign = 1.0 if link_row["impact_direction"] == "increase" else -1.0
    if pd.notna(link_row.get("impact_estimate")):
        return abs(link_row["impact_estimate"]) * sign
    magnitude = link_row.get("impact_magnitude", "medium")
    return MAGNITUDE_FALLBACK_PP.get(magnitude, 6.0) * sign


@dataclass
class EventEffect:
    link_id: str
    event_id: str
    event_name: str
    event_date: pd.Timestamp
    full_effect: float
    lag_months: float
    ramp_months: float
    used_fallback_magnitude: bool

    def effect_at(self, as_of: pd.Timestamp) -> float:
        t = months_between(self.event_date, as_of)
        months_since_lag_end = t - self.lag_months
        return self.full_effect * ramp_fraction(months_since_lag_end, self.ramp_months)


def build_event_effects(links: pd.DataFrame, events: pd.DataFrame, indicator_code: str) -> list:
    """
    Return a list of EventEffect objects for every impact_link targeting
    `indicator_code`, joined against the events table for event dates/names.
    """
    sub = links[links["related_indicator"] == indicator_code].merge(
        events[["record_id", "indicator", "observation_date"]],
        left_on="parent_id", right_on="record_id", suffixes=("", "_event"),
    )
    effects = []
    for _, row in sub.iterrows():
        effects.append(EventEffect(
            link_id=row["record_id"],
            event_id=row["parent_id"],
            event_name=row["indicator_event"],
            event_date=row["observation_date_event"],
            full_effect=resolve_effect_size(row),
            lag_months=row["lag_months"] if pd.notna(row["lag_months"]) else 0,
            ramp_months=resolve_ramp_months(row["relationship_type"]),
            used_fallback_magnitude=pd.isna(row.get("impact_estimate")),
        ))
    return effects


def predict_indicator(baseline_value: float, baseline_date: pd.Timestamp,
                       as_of: pd.Timestamp, effects: list,
                       clip_percentage: bool = False) -> float:
    """
    Predicted indicator value at `as_of`, starting from `baseline_value` at
    `baseline_date` and adding every applicable event effect (additive
    combination of independent events -- see module docstring).
    """
    total_effect = sum(e.effect_at(as_of) for e in effects if e.event_date >= baseline_date - pd.Timedelta(days=1))
    value = baseline_value + total_effect
    if clip_percentage:
        value = max(0.0, min(100.0, value))
    return value


def predict_trajectory(baseline_value: float, baseline_date: pd.Timestamp,
                        effects: list, end_date: pd.Timestamp,
                        freq: str = "MS", clip_percentage: bool = False) -> pd.DataFrame:
    """Monthly predicted trajectory of an indicator from baseline_date to end_date."""
    dates = pd.date_range(baseline_date, end_date, freq=freq)
    values = [predict_indicator(baseline_value, baseline_date, d, effects, clip_percentage) for d in dates]
    return pd.DataFrame({"date": dates, "predicted_value": values})
