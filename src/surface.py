"""
Volatility smile and surface reliability utilities.

The functions in this module work with option quote datasets that already
contain implied-volatility estimates from bid, mid, and ask prices.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def prepare_surface_dataset(iv_quotes: pd.DataFrame) -> pd.DataFrame:
    """Return a surface-ready dataset with required derived fields."""
    frame = iv_quotes.copy()

    if "log_moneyness" not in frame.columns:
        if {"strike", "underlying_price"}.issubset(frame.columns):
            frame["log_moneyness"] = np.log(frame["strike"] / frame["underlying_price"])
        else:
            raise ValueError("Missing log_moneyness and cannot calculate it from strike and underlying_price.")

    if "moneyness" not in frame.columns:
        if {"strike", "underlying_price"}.issubset(frame.columns):
            frame["moneyness"] = frame["underlying_price"] / frame["strike"]
        else:
            raise ValueError("Missing moneyness and cannot calculate it from strike and underlying_price.")

    if "IV_range" not in frame.columns and {"IV_bid", "IV_ask"}.issubset(frame.columns):
        frame["IV_range"] = frame["IV_ask"] - frame["IV_bid"]

    if "IV_relative_range" not in frame.columns and {"IV_range", "IV_mid"}.issubset(frame.columns):
        frame["IV_relative_range"] = np.where(
            frame["IV_mid"] > 0,
            frame["IV_range"] / frame["IV_mid"],
            np.nan,
        )

    if "is_excluded" not in frame.columns:
        frame["is_excluded"] = False

    if "days_to_expiry" not in frame.columns and "time_to_maturity" in frame.columns:
        frame["days_to_expiry"] = frame["time_to_maturity"] * 365.25

    return frame


def select_smile_slice(
    iv_quotes: pd.DataFrame,
    expiration: str | None = None,
    option_type: str | None = None,
    retained_only: bool = True,
) -> pd.DataFrame:
    """Return one expiry and option-type slice for smile analysis."""
    frame = prepare_surface_dataset(iv_quotes)
    frame = frame.dropna(subset=["expiration", "option_type", "log_moneyness", "IV_mid"]).copy()

    if retained_only:
        frame = frame.loc[~frame["is_excluded"]].copy()

    if frame.empty:
        raise ValueError("No complete rows available for smile analysis.")

    if expiration is None:
        expiration = (
            frame.groupby("expiration")["IV_mid"]
            .count()
            .sort_values(ascending=False)
            .index[0]
        )

    if option_type is None:
        option_type = (
            frame.loc[frame["expiration"] == expiration]
            .groupby("option_type")["IV_mid"]
            .count()
            .sort_values(ascending=False)
            .index[0]
        )

    smile = frame.loc[
        (frame["expiration"] == expiration)
        & (frame["option_type"] == option_type)
    ].copy()

    if smile.empty:
        raise ValueError("No rows match the requested smile slice.")

    return smile.sort_values("log_moneyness")


def available_smile_slices(iv_quotes: pd.DataFrame) -> pd.DataFrame:
    """Return quote counts by expiry and option type."""
    frame = prepare_surface_dataset(iv_quotes)

    summary = (
        frame.groupby(["expiration", "option_type"], observed=True)
        .agg(
            total_quotes=("IV_mid", "size"),
            retained_quotes=("is_excluded", lambda x: int((~x.astype(bool)).sum())),
            complete_mid_iv_quotes=("IV_mid", lambda x: int(x.notna().sum())),
        )
        .reset_index()
        .sort_values(["expiration", "option_type"])
    )

    return summary


def build_surface_grid(
    iv_quotes: pd.DataFrame,
    retained_only: bool = True,
    iv_column: str = "IV_mid",
    moneyness_bins: int = 12,
) -> pd.DataFrame:
    """Build a binned volatility surface table from option quotes."""
    frame = prepare_surface_dataset(iv_quotes)

    if retained_only:
        frame = frame.loc[~frame["is_excluded"]].copy()

    required_columns = {"expiration", "days_to_expiry", "log_moneyness", iv_column}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    frame = frame.dropna(subset=["days_to_expiry", "log_moneyness", iv_column]).copy()

    if frame.empty:
        return pd.DataFrame(
            columns=[
                "expiration",
                "days_to_expiry",
                "log_moneyness_bin",
                "mean_log_moneyness",
                "median_iv",
                "quote_count",
            ]
        )

    frame["log_moneyness_bin"] = pd.cut(frame["log_moneyness"], bins=moneyness_bins)

    surface = (
        frame.groupby(["expiration", "log_moneyness_bin"], observed=True)
        .agg(
            days_to_expiry=("days_to_expiry", "median"),
            mean_log_moneyness=("log_moneyness", "mean"),
            median_iv=(iv_column, "median"),
            quote_count=(iv_column, "size"),
        )
        .reset_index()
        .sort_values(["days_to_expiry", "mean_log_moneyness"])
    )

    surface["log_moneyness_bin"] = surface["log_moneyness_bin"].astype(str)

    return surface


def clean_vs_unclean_surface_comparison(
    iv_quotes: pd.DataFrame,
    iv_column: str = "IV_mid",
    moneyness_bins: int = 12,
) -> pd.DataFrame:
    """Compare binned raw and cleaned implied-volatility surfaces."""
    raw_surface = build_surface_grid(
        iv_quotes,
        retained_only=False,
        iv_column=iv_column,
        moneyness_bins=moneyness_bins,
    )

    clean_surface = build_surface_grid(
        iv_quotes,
        retained_only=True,
        iv_column=iv_column,
        moneyness_bins=moneyness_bins,
    )

    comparison = raw_surface.merge(
        clean_surface,
        on=["expiration", "log_moneyness_bin"],
        how="outer",
        suffixes=("_raw", "_clean"),
    )

    comparison["days_to_expiry"] = comparison["days_to_expiry_clean"].fillna(
        comparison["days_to_expiry_raw"]
    )
    comparison["mean_log_moneyness"] = comparison["mean_log_moneyness_clean"].fillna(
        comparison["mean_log_moneyness_raw"]
    )
    comparison["iv_clean_minus_raw"] = comparison["median_iv_clean"] - comparison["median_iv_raw"]
    comparison["abs_iv_clean_minus_raw"] = comparison["iv_clean_minus_raw"].abs()

    return comparison.sort_values(["days_to_expiry", "mean_log_moneyness"])


def surface_reliability_diagnostics(iv_quotes: pd.DataFrame) -> pd.DataFrame:
    """Create reliability diagnostics by expiry and option type."""
    frame = prepare_surface_dataset(iv_quotes)

    if "spread_pct" not in frame.columns:
        frame["spread_pct"] = np.nan

    if "IV_relative_range" not in frame.columns:
        frame["IV_relative_range"] = np.nan

    diagnostics = (
        frame.groupby(["expiration", "option_type"], observed=True)
        .agg(
            total_quotes=("IV_mid", "size"),
            retained_quotes=("is_excluded", lambda x: int((~x.astype(bool)).sum())),
            excluded_quotes=("is_excluded", lambda x: int(x.astype(bool).sum())),
            complete_mid_iv_quotes=("IV_mid", lambda x: int(x.notna().sum())),
            median_spread_pct=("spread_pct", "median"),
            median_iv_mid=("IV_mid", "median"),
            median_iv_relative_range=("IV_relative_range", "median"),
            min_log_moneyness=("log_moneyness", "min"),
            max_log_moneyness=("log_moneyness", "max"),
            unique_strikes=("strike", "nunique") if "strike" in frame.columns else ("IV_mid", "size"),
        )
        .reset_index()
    )

    diagnostics["retention_rate"] = diagnostics["retained_quotes"] / diagnostics["total_quotes"]
    diagnostics["iv_completion_rate"] = diagnostics["complete_mid_iv_quotes"] / diagnostics["total_quotes"]
    diagnostics["log_moneyness_coverage"] = (
        diagnostics["max_log_moneyness"] - diagnostics["min_log_moneyness"]
    )

    diagnostics["reliability_score"] = (
        0.40 * diagnostics["retention_rate"].fillna(0)
        + 0.30 * diagnostics["iv_completion_rate"].fillna(0)
        + 0.20 * (1.0 - diagnostics["median_spread_pct"].fillna(1).clip(0, 1))
        + 0.10 * (1.0 - diagnostics["median_iv_relative_range"].fillna(1).clip(0, 1))
    )

    return diagnostics.sort_values(["reliability_score", "retained_quotes"], ascending=[False, False])


def smile_residuals(
    iv_quotes: pd.DataFrame,
    expiration: str | None = None,
    option_type: str | None = None,
    degree: int = 2,
) -> pd.DataFrame:
    """Fit a polynomial smile curve and return residuals for one slice."""
    smile = select_smile_slice(
        iv_quotes,
        expiration=expiration,
        option_type=option_type,
        retained_only=True,
    )

    smile = smile.dropna(subset=["log_moneyness", "IV_mid"]).copy()

    if len(smile) <= degree + 1:
        raise ValueError("Not enough points to fit the requested polynomial degree.")

    coefficients = np.polyfit(smile["log_moneyness"], smile["IV_mid"], deg=degree)
    fitted_values = np.polyval(coefficients, smile["log_moneyness"])

    residuals = smile.copy()
    residuals["fitted_IV_mid"] = fitted_values
    residuals["surface_residual"] = residuals["IV_mid"] - residuals["fitted_IV_mid"]

    return residuals
