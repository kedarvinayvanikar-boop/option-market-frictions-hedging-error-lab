"""
Greek uncertainty from bid, mid, and ask implied volatilities.

This module calculates Black-Scholes Greeks using IV_bid, IV_mid, and IV_ask.
The ranges show how quote uncertainty can pass through to risk sensitivities.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib.pyplot as plt

from src.greeks import calculate_greeks_dict

GREEK_NAMES = ["delta", "gamma", "vega", "theta", "rho"]
IV_SOURCE_COLUMNS = {"bid": "IV_bid", "mid": "IV_mid", "ask": "IV_ask"}


def calculate_greeks_for_iv_sources(
    iv_quotes: pd.DataFrame,
    risk_free_rate: float,
    retained_only: bool = True,
) -> pd.DataFrame:
    """Calculate Greeks from IV_bid, IV_mid, and IV_ask in long format."""
    required_columns = {
        "contractSymbol",
        "option_type",
        "strike",
        "underlying_price",
        "time_to_maturity",
        "IV_bid",
        "IV_mid",
        "IV_ask",
    }
    missing_columns = required_columns.difference(iv_quotes.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    frame = iv_quotes.copy()
    if retained_only and "is_excluded" in frame.columns:
        frame = frame.loc[~frame["is_excluded"]].copy()

    records = []
    for _, row in frame.iterrows():
        for source_name, iv_column in IV_SOURCE_COLUMNS.items():
            implied_volatility = row[iv_column]
            if pd.isna(implied_volatility) or implied_volatility <= 0:
                records.append(
                    {
                        "contractSymbol": row["contractSymbol"],
                        "price_source": source_name,
                        "implied_volatility": implied_volatility,
                        "greek_status": "failed",
                        "failure_reason": "missing or nonpositive implied volatility",
                    }
                )
                continue

            try:
                values = calculate_greeks_dict(
                    S=float(row["underlying_price"]),
                    K=float(row["strike"]),
                    T=float(row["time_to_maturity"]),
                    r=float(risk_free_rate),
                    sigma=float(implied_volatility),
                    option_type=str(row["option_type"]),
                )
                records.append(
                    {
                        "contractSymbol": row["contractSymbol"],
                        "price_source": source_name,
                        "implied_volatility": implied_volatility,
                        "greek_status": "success",
                        "failure_reason": None,
                        **values,
                    }
                )
            except ValueError as exc:
                records.append(
                    {
                        "contractSymbol": row["contractSymbol"],
                        "price_source": source_name,
                        "implied_volatility": implied_volatility,
                        "greek_status": "failed",
                        "failure_reason": str(exc),
                    }
                )

    return pd.DataFrame(records)


def build_greek_wide_table(iv_quotes: pd.DataFrame, greek_results: pd.DataFrame) -> pd.DataFrame:
    """Attach bid, mid, and ask Greek columns to the option quote dataset."""
    pivoted = greek_results.pivot_table(
        index="contractSymbol",
        columns="price_source",
        values=GREEK_NAMES,
        aggfunc="first",
    )
    pivoted.columns = [f"{greek}_{source}" for greek, source in pivoted.columns]
    pivoted = pivoted.reset_index()

    merged = iv_quotes.merge(pivoted, on="contractSymbol", how="left")
    merged = merged.rename(
        columns={
            "delta_mid": "Delta_mid",
            "gamma_mid": "Gamma_mid",
            "vega_mid": "Vega_mid",
            "theta_mid": "Theta_mid",
            "rho_mid": "Rho_mid",
        }
    )
    return merged


def add_greek_uncertainty_ranges(greek_wide: pd.DataFrame) -> pd.DataFrame:
    """Add Greek uncertainty ranges using bid, mid, and ask calculations."""
    frame = greek_wide.copy()
    for greek_name in GREEK_NAMES:
        source_columns = [
            f"{greek_name}_bid",
            f"{greek_name}_mid",
            f"{greek_name}_ask",
        ]
        available_columns = [column for column in source_columns if column in frame.columns]
        if len(available_columns) >= 2:
            frame[f"{greek_name.capitalize()}_range"] = (
                frame[available_columns].max(axis=1) - frame[available_columns].min(axis=1)
            )
    return frame


def prepare_greek_uncertainty_dataset(
    iv_quotes: pd.DataFrame,
    risk_free_rate: float,
    retained_only: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return long Greek results and wide Greek uncertainty results."""
    greek_results = calculate_greeks_for_iv_sources(iv_quotes, risk_free_rate, retained_only)
    greek_wide = build_greek_wide_table(iv_quotes, greek_results)
    greek_wide = add_greek_uncertainty_ranges(greek_wide)
    return greek_results, greek_wide


def greek_uncertainty_summary(greek_wide: pd.DataFrame) -> pd.DataFrame:
    """Summarize Greek uncertainty by expiry and option type."""
    range_columns = [
        column for column in [
            "Delta_range",
            "Gamma_range",
            "Vega_range",
            "Theta_range",
            "Rho_range",
        ]
        if column in greek_wide.columns
    ]
    if not range_columns:
        raise ValueError("No Greek range columns found.")

    summary = (
        greek_wide.groupby(["expiration", "option_type"], observed=True)
        .agg(
            contract_count=("contractSymbol", "size"),
            **{f"median_{column}": (column, "median") for column in range_columns},
            **{f"max_{column}": (column, "max") for column in range_columns},
        )
        .reset_index()
        .sort_values(["expiration", "option_type"])
    )
    return summary


def greek_failure_summary(greek_results: pd.DataFrame) -> pd.DataFrame:
    """Return counts of Greek calculation failures."""
    failures = greek_results.loc[greek_results["greek_status"] != "success"].copy()
    if failures.empty:
        return pd.DataFrame(columns=["price_source", "failure_reason", "failure_count"])
    return (
        failures.groupby(["price_source", "failure_reason"], dropna=False)
        .size()
        .reset_index(name="failure_count")
        .sort_values("failure_count", ascending=False)
    )


def _prepare_output_path(output_path: str | Path) -> Path:
    """Create the parent directory for a figure path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def plot_greek_uncertainty_heatmap(
    greek_wide: pd.DataFrame,
    greek_name: str,
    output_path: str | Path,
    moneyness_bins: int = 8,
) -> Path:
    """Save a heatmap of Greek uncertainty by expiry and log-moneyness."""
    output_path = _prepare_output_path(output_path)
    range_column = f"{greek_name.capitalize()}_range"
    if range_column not in greek_wide.columns:
        raise ValueError(f"Missing required column: {range_column}")

    frame = greek_wide.dropna(subset=["expiration", "log_moneyness", range_column]).copy()
    if frame.empty:
        raise ValueError(f"No rows available for {greek_name} uncertainty heatmap.")

    frame["log_moneyness_bin"] = pd.cut(frame["log_moneyness"], bins=moneyness_bins).astype(str)
    heatmap = (
        frame.groupby(["expiration", "log_moneyness_bin"], observed=True)[range_column]
        .median()
        .unstack()
    )

    plt.figure(figsize=(10, 5))
    image = plt.imshow(heatmap.values, aspect="auto")
    plt.colorbar(image, label=f"Median {greek_name.capitalize()} Range")
    plt.xticks(range(len(heatmap.columns)), heatmap.columns.astype(str), rotation=45, ha="right")
    plt.yticks(range(len(heatmap.index)), heatmap.index.astype(str))
    plt.xlabel("Log-Moneyness Bin")
    plt.ylabel("Expiration")
    plt.title(f"{greek_name.capitalize()} Uncertainty Heatmap")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def plot_all_greek_uncertainty_heatmaps(
    greek_wide: pd.DataFrame,
    output_dir: str | Path = "figures",
) -> dict[str, Path]:
    """Save heatmaps for Delta, Gamma, Vega, and Theta uncertainty."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for greek_name in ["delta", "gamma", "vega", "theta"]:
        paths[greek_name] = plot_greek_uncertainty_heatmap(
            greek_wide,
            greek_name=greek_name,
            output_path=output_dir / f"{greek_name}_uncertainty_heatmap.png",
        )
    return paths


def insert_greek_results_to_database(
    db_path: str | Path,
    greek_results: pd.DataFrame,
    greek_wide: pd.DataFrame,
    snapshot_id: int,
) -> dict[str, int]:
    """Insert Greek result tables into an existing SQLite database."""
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        quote_map = dict(
            connection.execute(
                """
                SELECT contract_symbol, clean_quote_id
                FROM option_quotes_clean
                WHERE snapshot_id = ?;
                """,
                (snapshot_id,),
            ).fetchall()
        )

        greek_rows = []
        for _, row in greek_results.iterrows():
            clean_quote_id = quote_map.get(row["contractSymbol"])
            if clean_quote_id is None or row["greek_status"] != "success":
                continue
            greek_rows.append(
                (
                    clean_quote_id,
                    snapshot_id,
                    row["price_source"],
                    row["implied_volatility"],
                    row.get("delta"),
                    row.get("gamma"),
                    row.get("vega"),
                    row.get("theta"),
                    row.get("rho"),
                )
            )

        connection.executemany(
            """
            INSERT OR REPLACE INTO greek_results (
                clean_quote_id,
                snapshot_id,
                price_source,
                implied_volatility,
                delta,
                gamma,
                vega,
                theta,
                rho
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            greek_rows,
        )

        uncertainty_rows = []
        for _, row in greek_wide.iterrows():
            clean_quote_id = quote_map.get(row["contractSymbol"])
            if clean_quote_id is None:
                continue
            uncertainty_rows.append(
                (
                    clean_quote_id,
                    snapshot_id,
                    row.get("delta_bid"),
                    row.get("Delta_mid"),
                    row.get("delta_ask"),
                    row.get("Delta_range"),
                    row.get("gamma_bid"),
                    row.get("Gamma_mid"),
                    row.get("gamma_ask"),
                    row.get("Gamma_range"),
                    row.get("vega_bid"),
                    row.get("Vega_mid"),
                    row.get("vega_ask"),
                    row.get("Vega_range"),
                    row.get("theta_bid"),
                    row.get("Theta_mid"),
                    row.get("theta_ask"),
                    row.get("Theta_range"),
                    row.get("rho_bid"),
                    row.get("Rho_mid"),
                    row.get("rho_ask"),
                    row.get("Rho_range"),
                )
            )

        connection.executemany(
            """
            INSERT OR REPLACE INTO greek_uncertainty_results (
                clean_quote_id,
                snapshot_id,
                delta_bid,
                delta_mid,
                delta_ask,
                delta_range,
                gamma_bid,
                gamma_mid,
                gamma_ask,
                gamma_range,
                vega_bid,
                vega_mid,
                vega_ask,
                vega_range,
                theta_bid,
                theta_mid,
                theta_ask,
                theta_range,
                rho_bid,
                rho_mid,
                rho_ask,
                rho_range
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            uncertainty_rows,
        )
        connection.commit()

    return {
        "greek_results_inserted": len(greek_rows),
        "greek_uncertainty_rows_inserted": len(uncertainty_rows),
    }
