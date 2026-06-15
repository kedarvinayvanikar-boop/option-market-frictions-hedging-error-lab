"""
Short-expiry option risk dashboard utilities.

The functions in this module group options by days to expiry and summarize how
Gamma, Theta, Vega, bid-ask spread, and IV uncertainty change across short
maturities.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DTE_BUCKET_ORDER = [
    "0_to_1_DTE",
    "2_to_7_DTE",
    "8_to_14_DTE",
    "15_to_30_DTE",
    "31_to_60_DTE",
    "61_plus_DTE",
]


def add_dte_bucket(
    option_data: pd.DataFrame,
    days_col: str = "days_to_expiry",
) -> pd.DataFrame:
    """Add days-to-expiry buckets for short-expiry analysis."""
    frame = option_data.copy()

    if days_col not in frame.columns:
        raise ValueError(f"Missing required column: {days_col}")

    days = pd.to_numeric(frame[days_col], errors="coerce")

    conditions = [
        days.ge(0) & days.le(1),
        days.gt(1) & days.le(7),
        days.gt(7) & days.le(14),
        days.gt(14) & days.le(30),
        days.gt(30) & days.le(60),
        days.gt(60),
    ]

    frame["dte_bucket"] = np.select(
        conditions,
        DTE_BUCKET_ORDER,
        default="unbucketed",
    )

    frame.loc[~frame["dte_bucket"].isin(DTE_BUCKET_ORDER), "dte_bucket"] = pd.NA

    frame["dte_bucket"] = pd.Categorical(
        frame["dte_bucket"],
        categories=DTE_BUCKET_ORDER,
        ordered=True,
    )

    return frame


def prepare_short_expiry_dataset(
    option_data: pd.DataFrame,
    max_days: int = 60,
    retained_only: bool = True,
) -> pd.DataFrame:
    """Prepare a dataset for short-expiry risk analysis."""
    frame = option_data.copy()

    if retained_only and "is_excluded" in frame.columns:
        frame = frame.loc[~frame["is_excluded"]].copy()

    if "days_to_expiry" not in frame.columns:
        if "time_to_maturity" in frame.columns:
            frame["days_to_expiry"] = pd.to_numeric(frame["time_to_maturity"], errors="coerce") * 365.25
        else:
            raise ValueError("Missing days_to_expiry and time_to_maturity.")

    frame = add_dte_bucket(frame)
    frame = frame.loc[frame["days_to_expiry"].between(0, max_days, inclusive="both")].copy()

    return frame


def _first_existing_column(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first column from candidates that exists in the DataFrame."""
    for column in candidates:
        if column in frame.columns:
            return column
    return None


def short_expiry_risk_summary(option_data: pd.DataFrame) -> pd.DataFrame:
    """Summarize short-expiry risk metrics by DTE bucket and option type."""
    frame = option_data.copy()

    gamma_col = _first_existing_column(frame, ["Gamma_mid", "gamma_mid"])
    theta_col = _first_existing_column(frame, ["Theta_mid", "theta_mid"])
    vega_col = _first_existing_column(frame, ["Vega_mid", "vega_mid"])
    iv_uncertainty_col = _first_existing_column(frame, ["IV_relative_range", "IV_range"])
    spread_col = _first_existing_column(frame, ["spread_pct"])

    required_columns = ["dte_bucket", "option_type", "contractSymbol", "days_to_expiry"]
    for column in required_columns:
        if column not in frame.columns:
            raise ValueError(f"Missing required column: {column}")

    aggregation = {
        "contract_count": ("contractSymbol", "size"),
        "median_days_to_expiry": ("days_to_expiry", "median"),
    }

    if gamma_col:
        aggregation["median_gamma"] = (gamma_col, "median")
        aggregation["max_gamma"] = (gamma_col, "max")

    if theta_col:
        aggregation["median_theta"] = (theta_col, "median")
        aggregation["median_abs_theta"] = (theta_col, lambda x: x.abs().median())

    if vega_col:
        aggregation["median_vega"] = (vega_col, "median")

    if iv_uncertainty_col:
        aggregation["median_iv_uncertainty"] = (iv_uncertainty_col, "median")
        aggregation["max_iv_uncertainty"] = (iv_uncertainty_col, "max")

    if spread_col:
        aggregation["median_spread_pct"] = (spread_col, "median")
        aggregation["max_spread_pct"] = (spread_col, "max")

    summary = (
        frame.groupby(["dte_bucket", "option_type"], observed=True)
        .agg(**aggregation)
        .reset_index()
        .sort_values(["dte_bucket", "option_type"])
    )

    return summary


def dte_metric_summary(
    option_data: pd.DataFrame,
    metric_col: str,
    group_by_option_type: bool = True,
) -> pd.DataFrame:
    """Return a median metric summary by DTE bucket."""
    frame = option_data.dropna(subset=["dte_bucket", metric_col]).copy()

    if frame.empty:
        return pd.DataFrame()

    group_columns = ["dte_bucket", "option_type"] if group_by_option_type else ["dte_bucket"]

    summary = (
        frame.groupby(group_columns, observed=True)
        .agg(
            contract_count=(metric_col, "size"),
            median_value=(metric_col, "median"),
            mean_value=(metric_col, "mean"),
            max_value=(metric_col, "max"),
            min_value=(metric_col, "min"),
        )
        .reset_index()
        .sort_values(group_columns)
    )

    return summary


def short_expiry_risk_score(option_data: pd.DataFrame) -> pd.DataFrame:
    """
    Add a simple short-expiry risk score.

    The score combines normalized Gamma, absolute Theta, IV uncertainty, and
    spread percentage. It is a diagnostic ranking, not a trading signal.
    """
    frame = option_data.copy()

    gamma_col = _first_existing_column(frame, ["Gamma_mid", "gamma_mid"])
    theta_col = _first_existing_column(frame, ["Theta_mid", "theta_mid"])
    iv_col = _first_existing_column(frame, ["IV_relative_range", "IV_range"])
    spread_col = _first_existing_column(frame, ["spread_pct"])

    components = []

    if gamma_col:
        components.append(frame[gamma_col].rank(pct=True))

    if theta_col:
        components.append(frame[theta_col].abs().rank(pct=True))

    if iv_col:
        components.append(frame[iv_col].rank(pct=True))

    if spread_col:
        components.append(frame[spread_col].rank(pct=True))

    if components:
        frame["short_expiry_risk_score"] = sum(components) / len(components)
    else:
        frame["short_expiry_risk_score"] = np.nan

    return frame


def _prepare_output_path(output_path: str | Path) -> Path:
    """Create the parent directory for a figure path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def plot_metric_by_dte(
    option_data: pd.DataFrame,
    metric_col: str,
    output_path: str | Path,
    title: str,
    ylabel: str,
    group_by_option_type: bool = True,
) -> Path:
    """Save a DTE bucket chart for one metric."""
    output_path = _prepare_output_path(output_path)
    summary = dte_metric_summary(
        option_data,
        metric_col=metric_col,
        group_by_option_type=group_by_option_type,
    )

    if summary.empty:
        raise ValueError(f"No data available for metric: {metric_col}")

    plt.figure(figsize=(9, 5))

    if group_by_option_type and "option_type" in summary.columns:
        for option_type, group in summary.groupby("option_type", observed=True):
            group = group.sort_values("dte_bucket")
            plt.plot(
                group["dte_bucket"].astype(str),
                group["median_value"],
                marker="o",
                label=str(option_type),
            )
        plt.legend(title="Option Type")
    else:
        summary = summary.sort_values("dte_bucket")
        plt.plot(summary["dte_bucket"].astype(str), summary["median_value"], marker="o")

    plt.xlabel("DTE Bucket")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_gamma_by_dte(option_data: pd.DataFrame, output_path: str | Path) -> Path:
    """Save Gamma by DTE chart."""
    gamma_col = _first_existing_column(option_data, ["Gamma_mid", "gamma_mid"])
    if gamma_col is None:
        raise ValueError("No Gamma column found.")

    return plot_metric_by_dte(
        option_data,
        metric_col=gamma_col,
        output_path=output_path,
        title="Gamma by DTE Bucket",
        ylabel="Median Gamma",
    )


def plot_theta_by_dte(option_data: pd.DataFrame, output_path: str | Path) -> Path:
    """Save Theta by DTE chart."""
    theta_col = _first_existing_column(option_data, ["Theta_mid", "theta_mid"])
    if theta_col is None:
        raise ValueError("No Theta column found.")

    frame = option_data.copy()
    frame["abs_theta"] = frame[theta_col].abs()

    return plot_metric_by_dte(
        frame,
        metric_col="abs_theta",
        output_path=output_path,
        title="Absolute Theta by DTE Bucket",
        ylabel="Median Absolute Theta",
    )


def plot_vega_by_dte(option_data: pd.DataFrame, output_path: str | Path) -> Path:
    """Save Vega by DTE chart."""
    vega_col = _first_existing_column(option_data, ["Vega_mid", "vega_mid"])
    if vega_col is None:
        raise ValueError("No Vega column found.")

    return plot_metric_by_dte(
        option_data,
        metric_col=vega_col,
        output_path=output_path,
        title="Vega by DTE Bucket",
        ylabel="Median Vega",
    )


def plot_iv_uncertainty_by_dte(option_data: pd.DataFrame, output_path: str | Path) -> Path:
    """Save IV uncertainty by DTE chart."""
    iv_col = _first_existing_column(option_data, ["IV_relative_range", "IV_range"])
    if iv_col is None:
        raise ValueError("No IV uncertainty column found.")

    return plot_metric_by_dte(
        option_data,
        metric_col=iv_col,
        output_path=output_path,
        title="IV Uncertainty by DTE Bucket",
        ylabel="Median IV Uncertainty",
    )


def plot_spread_pct_by_dte(option_data: pd.DataFrame, output_path: str | Path) -> Path:
    """Save spread percentage by DTE chart."""
    if "spread_pct" not in option_data.columns:
        raise ValueError("No spread_pct column found.")

    return plot_metric_by_dte(
        option_data,
        metric_col="spread_pct",
        output_path=output_path,
        title="Bid-Ask Spread Percentage by DTE Bucket",
        ylabel="Median Spread Percentage",
    )


def plot_short_expiry_gamma_theta(option_data: pd.DataFrame, output_path: str | Path) -> Path:
    """Save a combined normalized Gamma and absolute Theta chart."""
    output_path = _prepare_output_path(output_path)

    gamma_col = _first_existing_column(option_data, ["Gamma_mid", "gamma_mid"])
    theta_col = _first_existing_column(option_data, ["Theta_mid", "theta_mid"])

    if gamma_col is None or theta_col is None:
        raise ValueError("Gamma and Theta columns are required.")

    frame = option_data.copy()
    frame["abs_theta"] = frame[theta_col].abs()

    summary = (
        frame.groupby("dte_bucket", observed=True)
        .agg(
            median_gamma=(gamma_col, "median"),
            median_abs_theta=("abs_theta", "median"),
        )
        .reset_index()
        .sort_values("dte_bucket")
    )

    if summary.empty:
        raise ValueError("No data available for combined Gamma and Theta chart.")

    summary["gamma_index"] = summary["median_gamma"] / summary["median_gamma"].max()
    summary["abs_theta_index"] = summary["median_abs_theta"] / summary["median_abs_theta"].max()

    plt.figure(figsize=(9, 5))
    plt.plot(summary["dte_bucket"].astype(str), summary["gamma_index"], marker="o", label="Gamma Index")
    plt.plot(summary["dte_bucket"].astype(str), summary["abs_theta_index"], marker="o", label="Absolute Theta Index")
    plt.xlabel("DTE Bucket")
    plt.ylabel("Indexed Median Value")
    plt.title("Short-Expiry Gamma and Theta Risk")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def build_short_expiry_dashboard_outputs(
    option_data: pd.DataFrame,
    output_dir: str | Path = "figures",
) -> dict[str, Path]:
    """Save all short-expiry dashboard figures."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "short_expiry_gamma_theta": plot_short_expiry_gamma_theta(
            option_data,
            output_dir / "short_expiry_gamma_theta.png",
        ),
        "gamma_by_dte": plot_gamma_by_dte(
            option_data,
            output_dir / "gamma_by_dte.png",
        ),
        "theta_by_dte": plot_theta_by_dte(
            option_data,
            output_dir / "theta_by_dte.png",
        ),
        "vega_by_dte": plot_vega_by_dte(
            option_data,
            output_dir / "vega_by_dte.png",
        ),
        "iv_uncertainty_by_dte": plot_iv_uncertainty_by_dte(
            option_data,
            output_dir / "iv_uncertainty_by_dte.png",
        ),
        "spread_percentage_by_dte": plot_spread_pct_by_dte(
            option_data,
            output_dir / "spread_percentage_by_dte.png",
        ),
    }

    return outputs
