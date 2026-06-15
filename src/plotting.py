"""
Plotting utilities for volatility smile and surface reliability analysis.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from src.surface import (
    clean_vs_unclean_surface_comparison,
    prepare_surface_dataset,
    select_smile_slice,
    smile_residuals,
    surface_reliability_diagnostics,
)


def _prepare_output_path(output_path: str | Path) -> Path:
    """Create the parent directory for a figure path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def plot_iv_mid_smiles(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
    expirations: list[str] | None = None,
    option_type: str = "call",
    max_expirations: int = 4,
) -> Path:
    """Save IV-mid smiles across selected expiries."""
    output_path = _prepare_output_path(output_path)
    frame = prepare_surface_dataset(iv_quotes)
    frame = frame.loc[
        (~frame["is_excluded"])
        & (frame["option_type"] == option_type)
        & frame["IV_mid"].notna()
        & frame["log_moneyness"].notna()
    ].copy()

    if frame.empty:
        raise ValueError("No retained IV_mid rows available for smile plotting.")

    if expirations is None:
        expirations = (
            frame.groupby("expiration")["IV_mid"]
            .count()
            .sort_values(ascending=False)
            .head(max_expirations)
            .index
            .tolist()
        )

    plt.figure(figsize=(9, 5))

    for expiration in expirations:
        slice_data = frame.loc[frame["expiration"] == expiration].sort_values("log_moneyness")
        if not slice_data.empty:
            plt.plot(
                slice_data["log_moneyness"],
                slice_data["IV_mid"],
                marker="o",
                label=str(expiration),
            )

    plt.xlabel("Log-Moneyness ln(K / S)")
    plt.ylabel("Mid Implied Volatility")
    plt.title(f"IV Mid Smiles by Expiry: {option_type}")
    plt.legend(title="Expiration")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_iv_bid_mid_ask_smile(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
    expiration: str | None = None,
    option_type: str | None = None,
) -> Path:
    """Save one smile with bid, mid, and ask implied volatility."""
    output_path = _prepare_output_path(output_path)
    smile = select_smile_slice(
        iv_quotes,
        expiration=expiration,
        option_type=option_type,
        retained_only=True,
    )

    required_columns = ["IV_bid", "IV_mid", "IV_ask"]
    missing_columns = [column for column in required_columns if column not in smile.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Missing required IV columns: {missing}")

    selected_expiration = smile["expiration"].iloc[0]
    selected_option_type = smile["option_type"].iloc[0]

    plt.figure(figsize=(8, 5))
    plt.plot(smile["log_moneyness"], smile["IV_bid"], marker="o", label="IV Bid")
    plt.plot(smile["log_moneyness"], smile["IV_mid"], marker="o", label="IV Mid")
    plt.plot(smile["log_moneyness"], smile["IV_ask"], marker="o", label="IV Ask")
    plt.xlabel("Log-Moneyness ln(K / S)")
    plt.ylabel("Implied Volatility")
    plt.title(f"Bid, Mid, and Ask IV Smile: {selected_expiration} {selected_option_type}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_clean_vs_unclean_surface(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Save a chart comparing binned clean and raw surface medians."""
    output_path = _prepare_output_path(output_path)

    comparison = clean_vs_unclean_surface_comparison(iv_quotes)
    plot_data = comparison.dropna(
        subset=["mean_log_moneyness", "median_iv_raw", "median_iv_clean"]
    ).copy()

    if plot_data.empty:
        raise ValueError("No overlapping clean and raw surface points available.")

    plot_data = plot_data.sort_values(["days_to_expiry", "mean_log_moneyness"]).reset_index(drop=True)
    plot_data["surface_point"] = range(1, len(plot_data) + 1)

    plt.figure(figsize=(10, 5))
    plt.plot(plot_data["surface_point"], plot_data["median_iv_raw"], marker="o", label="Raw")
    plt.plot(plot_data["surface_point"], plot_data["median_iv_clean"], marker="o", label="Cleaned")
    plt.xlabel("Binned Surface Point")
    plt.ylabel("Median IV Mid")
    plt.title("Cleaned vs Raw Volatility Surface")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_volatility_surface_reliability(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """Save a chart of surface reliability scores by expiry and option type."""
    output_path = _prepare_output_path(output_path)

    diagnostics = surface_reliability_diagnostics(iv_quotes)
    diagnostics = diagnostics.sort_values(["expiration", "option_type"]).copy()
    diagnostics["surface_slice"] = diagnostics["expiration"].astype(str) + " " + diagnostics["option_type"].astype(str)

    plt.figure(figsize=(10, 5))
    plt.bar(diagnostics["surface_slice"], diagnostics["reliability_score"])
    plt.xlabel("Surface Slice")
    plt.ylabel("Reliability Score")
    plt.title("Volatility Surface Reliability")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_surface_residuals(
    iv_quotes: pd.DataFrame,
    output_path: str | Path,
    expiration: str | None = None,
    option_type: str | None = None,
) -> Path:
    """Save residuals from a simple fitted smile curve."""
    output_path = _prepare_output_path(output_path)
    residual_data = smile_residuals(
        iv_quotes,
        expiration=expiration,
        option_type=option_type,
        degree=2,
    ).sort_values("log_moneyness")

    selected_expiration = residual_data["expiration"].iloc[0]
    selected_option_type = residual_data["option_type"].iloc[0]

    plt.figure(figsize=(8, 5))
    plt.axhline(0.0, linewidth=1)
    plt.scatter(residual_data["log_moneyness"], residual_data["surface_residual"])
    plt.xlabel("Log-Moneyness ln(K / S)")
    plt.ylabel("IV Mid Residual")
    plt.title(f"Smile Fit Residuals: {selected_expiration} {selected_option_type}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path
