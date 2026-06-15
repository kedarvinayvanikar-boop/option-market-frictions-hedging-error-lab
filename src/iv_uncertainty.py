"""
Implied-volatility uncertainty analysis.

The functions in this module measure how bid-ask spreads translate into
uncertainty in implied volatility. The input data should already contain
IV values solved from bid, mid, and ask prices.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def add_iv_uncertainty_metrics(
    iv_quotes: pd.DataFrame,
    iv_bid_col: str = "IV_bid",
    iv_mid_col: str = "IV_mid",
    iv_ask_col: str = "IV_ask",
) -> pd.DataFrame:
    """Add absolute and relative IV uncertainty measures."""
    frame = iv_quotes.copy()

    required_columns = {iv_bid_col, iv_mid_col, iv_ask_col}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required IV columns: {missing}")

    frame["IV_range"] = frame[iv_ask_col] - frame[iv_bid_col]
    frame["IV_relative_range"] = np.where(
        frame[iv_mid_col] > 0,
        frame["IV_range"] / frame[iv_mid_col],
        np.nan,
    )

    return frame


def add_moneyness_bucket(
    iv_quotes: pd.DataFrame,
    log_moneyness_col: str = "log_moneyness",
) -> pd.DataFrame:
    """Group contracts into log-moneyness buckets."""
    frame = iv_quotes.copy()

    if log_moneyness_col not in frame.columns:
        raise ValueError(f"Missing required column: {log_moneyness_col}")

    bins = [-np.inf, -0.10, -0.05, -0.02, 0.02, 0.05, 0.10, np.inf]
    labels = [
        "far_below_spot",
        "below_spot",
        "slightly_below_spot",
        "near_atm",
        "slightly_above_spot",
        "above_spot",
        "far_above_spot",
    ]

    frame["moneyness_bucket"] = pd.cut(
        frame[log_moneyness_col],
        bins=bins,
        labels=labels,
    )

    return frame


def add_expiry_bucket(
    iv_quotes: pd.DataFrame,
    days_col: str = "days_to_expiry",
) -> pd.DataFrame:
    """Group contracts into expiry buckets based on days to expiry."""
    frame = iv_quotes.copy()

    if days_col not in frame.columns:
        raise ValueError(f"Missing required column: {days_col}")

    bins = [-np.inf, 7, 30, 90, 180, np.inf]
    labels = [
        "0_to_7_days",
        "8_to_30_days",
        "31_to_90_days",
        "91_to_180_days",
        "181_plus_days",
    ]

    frame["expiry_bucket"] = pd.cut(
        frame[days_col],
        bins=bins,
        labels=labels,
    )

    return frame


def add_liquidity_bucket(
    iv_quotes: pd.DataFrame,
    spread_pct_col: str = "spread_pct",
    volume_col: str = "volume",
    open_interest_col: str = "openInterest",
) -> pd.DataFrame:
    """Assign a liquidity bucket using spread and activity fields."""
    frame = iv_quotes.copy()

    if spread_pct_col not in frame.columns:
        raise ValueError(f"Missing required column: {spread_pct_col}")

    volume = frame[volume_col] if volume_col in frame.columns else pd.Series(np.nan, index=frame.index)
    open_interest = (
        frame[open_interest_col]
        if open_interest_col in frame.columns
        else pd.Series(np.nan, index=frame.index)
    )

    low_activity = volume.fillna(0).lt(1) & open_interest.fillna(0).lt(1)

    conditions = [
        low_activity,
        frame[spread_pct_col].le(0.03),
        frame[spread_pct_col].le(0.10),
        frame[spread_pct_col].le(0.25),
    ]

    choices = [
        "low_activity",
        "tight_spread",
        "moderate_spread",
        "wide_spread",
    ]

    frame["liquidity_bucket"] = np.select(
        conditions,
        choices,
        default="very_wide_spread",
    )

    return frame


def prepare_iv_uncertainty_dataset(iv_quotes: pd.DataFrame) -> pd.DataFrame:
    """Add IV uncertainty metrics and analysis buckets."""
    frame = add_iv_uncertainty_metrics(iv_quotes)
    frame = add_moneyness_bucket(frame)
    frame = add_expiry_bucket(frame)
    frame = add_liquidity_bucket(frame)

    return frame


def iv_uncertainty_summary(
    iv_quotes: pd.DataFrame,
    group_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Summarize IV uncertainty by the selected grouping columns."""
    if group_columns is None:
        group_columns = ["option_type", "expiry_bucket", "moneyness_bucket", "liquidity_bucket"]

    required_columns = set(group_columns + ["IV_range", "IV_relative_range", "IV_mid"])
    missing_columns = required_columns.difference(iv_quotes.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    frame = iv_quotes.dropna(subset=["IV_range", "IV_relative_range"]).copy()

    summary = (
        frame.groupby(group_columns, observed=True)
        .agg(
            contract_count=("IV_range", "size"),
            mean_iv_mid=("IV_mid", "mean"),
            median_iv_mid=("IV_mid", "median"),
            mean_iv_range=("IV_range", "mean"),
            median_iv_range=("IV_range", "median"),
            max_iv_range=("IV_range", "max"),
            mean_iv_relative_range=("IV_relative_range", "mean"),
            median_iv_relative_range=("IV_relative_range", "median"),
        )
        .reset_index()
        .sort_values(["median_iv_relative_range", "contract_count"], ascending=[False, False])
    )

    return summary


def iv_uncertainty_by_expiry(iv_quotes: pd.DataFrame) -> pd.DataFrame:
    """Summarize IV uncertainty by expiry and option type."""
    return iv_uncertainty_summary(
        iv_quotes,
        group_columns=["expiration", "option_type"],
    ).sort_values(["expiration", "option_type"])


def iv_uncertainty_by_moneyness(iv_quotes: pd.DataFrame) -> pd.DataFrame:
    """Summarize IV uncertainty by moneyness bucket and option type."""
    return iv_uncertainty_summary(
        iv_quotes,
        group_columns=["moneyness_bucket", "option_type"],
    )


def iv_uncertainty_by_liquidity(iv_quotes: pd.DataFrame) -> pd.DataFrame:
    """Summarize IV uncertainty by liquidity bucket and option type."""
    return iv_uncertainty_summary(
        iv_quotes,
        group_columns=["liquidity_bucket", "option_type"],
    )


def _prepare_output_path(output_path: str | Path) -> Path:
    """Create the parent directory for a figure path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def _select_smile_slice(
    iv_quotes: pd.DataFrame,
    expiration: str | None = None,
    option_type: str | None = None,
) -> pd.DataFrame:
    """Return one expiry and option type slice for smile plotting."""
    frame = iv_quotes.dropna(subset=["log_moneyness", "IV_bid", "IV_mid", "IV_ask"]).copy()

    if frame.empty:
        raise ValueError("No complete IV rows available for smile plotting.")

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

    plot_data = frame.loc[
        (frame["expiration"] == expiration)
        & (frame["option_type"] == option_type)
    ].copy()

    if plot_data.empty:
        raise ValueError("No rows match the requested smile slice.")

    return plot_data.sort_values("log_moneyness")


def plot_iv_bid_mid_ask_smile(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
    expiration: str | None = None,
    option_type: str | None = None,
) -> Path:
    """Save a bid, mid, and ask implied-volatility smile plot."""
    output_path = _prepare_output_path(output_path)
    plot_data = _select_smile_slice(iv_quotes, expiration=expiration, option_type=option_type)

    selected_expiration = plot_data["expiration"].iloc[0]
    selected_option_type = plot_data["option_type"].iloc[0]

    plt.figure(figsize=(8, 5))
    plt.plot(plot_data["log_moneyness"], plot_data["IV_bid"], marker="o", label="IV Bid")
    plt.plot(plot_data["log_moneyness"], plot_data["IV_mid"], marker="o", label="IV Mid")
    plt.plot(plot_data["log_moneyness"], plot_data["IV_ask"], marker="o", label="IV Ask")
    plt.xlabel("Log-Moneyness ln(K / S)")
    plt.ylabel("Implied Volatility")
    plt.title(f"Bid, Mid, and Ask IV Smile: {selected_expiration} {selected_option_type}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_iv_uncertainty_heatmap(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Save a heatmap of median relative IV uncertainty."""
    output_path = _prepare_output_path(output_path)

    frame = iv_quotes.dropna(subset=["expiry_bucket", "moneyness_bucket", "IV_relative_range"]).copy()

    if frame.empty:
        raise ValueError("No rows available for IV uncertainty heatmap.")

    heatmap = (
        frame.groupby(["expiry_bucket", "moneyness_bucket"], observed=True)["IV_relative_range"]
        .median()
        .unstack()
    )

    plt.figure(figsize=(10, 5))
    image = plt.imshow(heatmap.values, aspect="auto")
    plt.colorbar(image, label="Median IV Relative Range")
    plt.xticks(range(len(heatmap.columns)), heatmap.columns.astype(str), rotation=45, ha="right")
    plt.yticks(range(len(heatmap.index)), heatmap.index.astype(str))
    plt.xlabel("Moneyness Bucket")
    plt.ylabel("Expiry Bucket")
    plt.title("Implied Volatility Uncertainty Heatmap")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_iv_uncertainty_by_expiry(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Save a chart of median IV uncertainty by expiry bucket."""
    output_path = _prepare_output_path(output_path)

    grouped = (
        iv_quotes.dropna(subset=["expiry_bucket", "IV_relative_range"])
        .groupby("expiry_bucket", observed=True)["IV_relative_range"]
        .median()
    )

    plt.figure(figsize=(8, 5))
    grouped.plot(kind="bar")
    plt.xlabel("Expiry Bucket")
    plt.ylabel("Median IV Relative Range")
    plt.title("IV Uncertainty by Expiry Bucket")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_iv_uncertainty_by_moneyness(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Save a chart of median IV uncertainty by moneyness bucket."""
    output_path = _prepare_output_path(output_path)

    grouped = (
        iv_quotes.dropna(subset=["moneyness_bucket", "IV_relative_range"])
        .groupby("moneyness_bucket", observed=True)["IV_relative_range"]
        .median()
    )

    plt.figure(figsize=(9, 5))
    grouped.plot(kind="bar")
    plt.xlabel("Moneyness Bucket")
    plt.ylabel("Median IV Relative Range")
    plt.title("IV Uncertainty by Moneyness Bucket")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path
