"""
Build a compact JSON bundle of pipeline results for the interactive dashboard.

The dashboard is a static artifact, so large per-path tables (scenario_results
and hedge_results) are aggregated into histograms here rather than embedded in
full.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROCESSED_DIR = Path("data/processed")
OUTPUT_PATH = Path("data/processed/dashboard_data.json")


def _records(df: pd.DataFrame, columns: list[str] | None = None, round_to: int = 6) -> list[dict]:
    frame = df[columns].copy() if columns else df.copy()
    for column in frame.columns:
        if frame[column].dtype == float:
            frame[column] = frame[column].round(round_to)
    return frame.to_dict(orient="records")


def build() -> dict:
    out: dict = {}

    data_quality = pd.read_csv(PROCESSED_DIR / "data_quality_summary.csv")
    exclusions = pd.read_csv(PROCESSED_DIR / "exclusion_reason_summary.csv")
    out["data_quality"] = _records(data_quality, round_to=4)
    out["exclusion_reasons"] = _records(exclusions, round_to=4)

    iv = pd.read_csv(PROCESSED_DIR / "iv_uncertainty_analysis.csv")
    iv_columns = [
        "contractSymbol", "expiration", "option_type", "strike", "log_moneyness", "moneyness",
        "days_to_expiry", "IV_bid", "IV_mid", "IV_ask", "IV_range", "IV_relative_range",
        "moneyness_bucket", "expiry_bucket", "liquidity_bucket", "spread_pct", "is_excluded",
    ]
    out["iv_quotes"] = _records(iv, iv_columns)

    out["iv_by_expiry"] = _records(pd.read_csv(PROCESSED_DIR / "iv_uncertainty_by_expiry.csv"), round_to=6)
    out["iv_by_moneyness"] = _records(pd.read_csv(PROCESSED_DIR / "iv_uncertainty_by_moneyness.csv"), round_to=6)

    greeks = pd.read_csv(PROCESSED_DIR / "greek_uncertainty_results.csv")
    greek_columns = [
        "contractSymbol", "expiration", "option_type", "strike", "log_moneyness", "days_to_expiry",
        "Delta_mid", "Gamma_mid", "Vega_mid", "Theta_mid",
        "Delta_range", "Gamma_range", "Vega_range", "Theta_range", "is_excluded",
    ]
    out["greeks"] = _records(greeks, [c for c in greek_columns if c in greeks.columns])

    out["short_expiry_summary"] = _records(pd.read_csv(PROCESSED_DIR / "short_expiry_risk_summary.csv"))
    out["surface_diagnostics"] = _records(pd.read_csv(PROCESSED_DIR / "surface_diagnostics.csv"), round_to=4)

    scenario_summary = pd.read_csv(PROCESSED_DIR / "scenario_summary.csv")
    out["scenario_summary"] = _records(scenario_summary)

    scenario_results = pd.read_csv(PROCESSED_DIR / "scenario_results.csv")
    lo, hi = scenario_results["hedging_error"].quantile([0.001, 0.999])
    bins = np.linspace(lo, hi, 31)
    out["hedging_error_bins"] = np.round(bins, 4).tolist()

    histograms: dict[str, list[int]] = {}
    for name, group in scenario_results.groupby("scenario_name"):
        counts, _ = np.histogram(group["hedging_error"], bins=bins)
        histograms[name] = counts.tolist()
    out["scenario_histograms"] = histograms

    paths = pd.read_csv(PROCESSED_DIR / "gbm_simulated_paths.csv")
    path_columns = [c for c in paths.columns if c.startswith("path_")][:15]
    sample_paths = paths[["time_years"] + path_columns].round(4)
    out["sample_paths"] = sample_paths.to_dict(orient="records")

    return out


def main() -> None:
    data = build()
    OUTPUT_PATH.write_text(json.dumps(data))
    print(f"Wrote {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
