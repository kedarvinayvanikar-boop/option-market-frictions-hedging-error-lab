"""
Quote-quality summaries and visuals for option-chain data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def exclusion_reason_summary(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Return counts by primary exclusion reason."""
    if "exclusion_reason" not in option_chain.columns:
        raise ValueError("The option-chain dataset does not contain exclusion_reason.")

    summary = (
        option_chain["exclusion_reason"]
        .value_counts(dropna=False)
        .rename_axis("exclusion_reason")
        .reset_index(name="contract_count")
    )

    summary["share_of_contracts"] = summary["contract_count"] / len(option_chain)

    return summary


def data_quality_summary(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Return high-level quote-quality metrics."""
    if "is_excluded" not in option_chain.columns:
        raise ValueError("The option-chain dataset does not contain is_excluded.")

    retained = option_chain.loc[~option_chain["is_excluded"]]
    excluded = option_chain.loc[option_chain["is_excluded"]]

    summary = pd.DataFrame(
        {
            "metric": [
                "total_contracts",
                "retained_contracts",
                "excluded_contracts",
                "excluded_share",
                "unique_expiries",
                "median_spread_pct_retained",
                "mean_spread_pct_retained",
                "median_days_to_expiry_retained",
            ],
            "value": [
                len(option_chain),
                len(retained),
                len(excluded),
                len(excluded) / len(option_chain) if len(option_chain) else 0.0,
                option_chain["expiration"].nunique() if "expiration" in option_chain.columns else None,
                retained["spread_pct"].median() if "spread_pct" in retained.columns else None,
                retained["spread_pct"].mean() if "spread_pct" in retained.columns else None,
                retained["days_to_expiry"].median() if "days_to_expiry" in retained.columns else None,
            ],
        }
    )

    return summary


def spread_by_expiry(option_chain: pd.DataFrame, retained_only: bool = True) -> pd.DataFrame:
    """Return median spread percentage by expiry."""
    frame = option_chain.copy()

    if retained_only and "is_excluded" in frame.columns:
        frame = frame.loc[~frame["is_excluded"]]

    grouped = (
        frame.groupby("expiration", dropna=False)
        .agg(
            contract_count=("contractSymbol", "count") if "contractSymbol" in frame.columns else ("strike", "count"),
            median_spread_pct=("spread_pct", "median"),
            mean_spread_pct=("spread_pct", "mean"),
        )
        .reset_index()
        .sort_values("expiration")
    )

    return grouped


def spread_by_moneyness_bin(
    option_chain: pd.DataFrame,
    retained_only: bool = True,
    bins: int = 10,
) -> pd.DataFrame:
    """Return average spread percentage by log-moneyness bin."""
    frame = option_chain.copy()

    if retained_only and "is_excluded" in frame.columns:
        frame = frame.loc[~frame["is_excluded"]]

    frame = frame.dropna(subset=["log_moneyness", "spread_pct"]).copy()

    if frame.empty:
        return pd.DataFrame(
            columns=[
                "log_moneyness_bin",
                "contract_count",
                "mean_log_moneyness",
                "median_spread_pct",
                "mean_spread_pct",
            ]
        )

    frame["log_moneyness_bin"] = pd.cut(frame["log_moneyness"], bins=bins)

    grouped = (
        frame.groupby("log_moneyness_bin", observed=True)
        .agg(
            contract_count=("spread_pct", "size"),
            mean_log_moneyness=("log_moneyness", "mean"),
            median_spread_pct=("spread_pct", "median"),
            mean_spread_pct=("spread_pct", "mean"),
        )
        .reset_index()
    )

    grouped["log_moneyness_bin"] = grouped["log_moneyness_bin"].astype(str)

    return grouped


def _prepare_output_path(output_path: str | Path) -> Path:
    """Create parent folders for a figure output path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def plot_data_cleaning_summary(option_chain: pd.DataFrame, output_path: str | Path) -> Path:
    """Save a bar chart showing retained and excluded contract counts."""
    output_path = _prepare_output_path(output_path)

    counts = pd.Series(
        {
            "retained": int((~option_chain["is_excluded"]).sum()),
            "excluded": int(option_chain["is_excluded"].sum()),
        }
    )

    plt.figure(figsize=(7, 5))
    counts.plot(kind="bar")
    plt.title("Option Quote Cleaning Summary")
    plt.xlabel("Quote Status")
    plt.ylabel("Contract Count")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_spread_by_moneyness(option_chain: pd.DataFrame, output_path: str | Path) -> Path:
    """Save a scatter plot of percentage spread by log-moneyness."""
    output_path = _prepare_output_path(output_path)

    frame = option_chain.loc[~option_chain["is_excluded"]].dropna(
        subset=["log_moneyness", "spread_pct"]
    )

    plt.figure(figsize=(8, 5))
    plt.scatter(frame["log_moneyness"], frame["spread_pct"])
    plt.title("Bid-Ask Spread by Log-Moneyness")
    plt.xlabel("Log-Moneyness ln(K / S)")
    plt.ylabel("Bid-Ask Spread / Mid Price")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_spread_by_expiry(option_chain: pd.DataFrame, output_path: str | Path) -> Path:
    """Save a bar chart of median percentage spread by expiry."""
    output_path = _prepare_output_path(output_path)

    grouped = spread_by_expiry(option_chain, retained_only=True)

    plt.figure(figsize=(9, 5))
    plt.bar(grouped["expiration"].astype(str), grouped["median_spread_pct"])
    plt.title("Median Bid-Ask Spread by Expiry")
    plt.xlabel("Expiration")
    plt.ylabel("Median Bid-Ask Spread / Mid Price")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path
