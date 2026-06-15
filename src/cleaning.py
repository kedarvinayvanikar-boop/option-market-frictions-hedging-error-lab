"""
Option-chain cleaning utilities.

The functions in this module keep raw quote data separate from cleaned quote
data. Raw vendor fields are preserved where possible, and cleaning decisions
are added as explicit flags.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


NUMERIC_COLUMNS = [
    "strike",
    "lastPrice",
    "bid",
    "ask",
    "change",
    "percentChange",
    "volume",
    "openInterest",
    "impliedVolatility",
]


def _to_utc_datetime(series: pd.Series) -> pd.Series:
    """Convert a pandas Series to timezone-aware UTC datetimes."""
    return pd.to_datetime(series, errors="coerce", utc=True)


def _snapshot_time_series(option_chain: pd.DataFrame) -> pd.Series:
    """Return snapshot times, using the current UTC time when missing."""
    if "snapshot_time_utc" in option_chain.columns:
        snapshot_time = _to_utc_datetime(option_chain["snapshot_time_utc"])
    else:
        snapshot_time = pd.Series(pd.NaT, index=option_chain.index, dtype="datetime64[ns, UTC]")

    current_time = pd.Timestamp(datetime.now(timezone.utc))
    return snapshot_time.fillna(current_time)


def coerce_option_columns(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Convert core quote columns to numeric types where available."""
    frame = option_chain.copy()

    for column in NUMERIC_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "option_type" in frame.columns:
        frame["option_type"] = frame["option_type"].astype(str).str.lower()

    return frame


def add_quote_metrics(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Add mid price, bid-ask spread, and percentage spread."""
    frame = option_chain.copy()

    frame["mid_price"] = (frame["bid"] + frame["ask"]) / 2.0
    frame["bid_ask_spread"] = frame["ask"] - frame["bid"]

    frame["spread_pct"] = np.where(
        frame["mid_price"] > 0,
        frame["bid_ask_spread"] / frame["mid_price"],
        np.nan,
    )

    return frame


def add_time_to_maturity(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Add days and years to option expiry."""
    frame = option_chain.copy()

    expiration = _to_utc_datetime(frame["expiration"])

    expiration_is_date_only = frame["expiration"].astype(str).str.len().le(10)
    expiration = expiration.where(
        ~expiration_is_date_only,
        expiration + pd.Timedelta(hours=23, minutes=59, seconds=59),
    )

    snapshot_time = _snapshot_time_series(frame)

    frame["expiration_datetime_utc"] = expiration
    frame["snapshot_datetime_utc"] = snapshot_time
    frame["days_to_expiry"] = (expiration - snapshot_time).dt.total_seconds() / 86_400.0
    frame["time_to_maturity"] = frame["days_to_expiry"] / 365.25

    return frame


def add_moneyness(option_chain: pd.DataFrame, underlying_price: float) -> pd.DataFrame:
    """
    Add moneyness and log-moneyness.

    Moneyness is defined as S / K, where S is the underlying price and K is the
    option strike. Log-moneyness is defined as ln(K / S), which is commonly used
    when plotting volatility smiles.
    """
    if underlying_price <= 0:
        raise ValueError("underlying_price must be positive.")

    frame = option_chain.copy()
    frame["underlying_price"] = float(underlying_price)

    frame["moneyness"] = np.where(
        frame["strike"] > 0,
        frame["underlying_price"] / frame["strike"],
        np.nan,
    )

    frame["log_moneyness"] = np.where(
        frame["strike"] > 0,
        np.log(frame["strike"] / frame["underlying_price"]),
        np.nan,
    )

    return frame


def add_exclusion_flags(
    option_chain: pd.DataFrame,
    max_spread_pct: float = 0.40,
    min_volume: int = 1,
    min_open_interest: int = 1,
) -> pd.DataFrame:
    """Add quote-quality exclusion flags."""
    frame = option_chain.copy()

    volume = frame["volume"] if "volume" in frame.columns else pd.Series(np.nan, index=frame.index)
    open_interest = (
        frame["openInterest"] if "openInterest" in frame.columns else pd.Series(np.nan, index=frame.index)
    )

    frame["flag_missing_bid_ask"] = frame["bid"].isna() | frame["ask"].isna()
    frame["flag_negative_bid_ask"] = (frame["bid"] < 0) | (frame["ask"] < 0)
    frame["flag_crossed_market"] = frame["ask"] < frame["bid"]
    frame["flag_zero_bid"] = frame["bid"] <= 0
    frame["flag_zero_ask"] = frame["ask"] <= 0
    frame["flag_invalid_mid"] = frame["mid_price"].isna() | (frame["mid_price"] <= 0)
    frame["flag_wide_spread"] = frame["spread_pct"].isna() | (frame["spread_pct"] > max_spread_pct)
    frame["flag_missing_strike"] = frame["strike"].isna()
    frame["flag_nonpositive_strike"] = frame["strike"] <= 0
    frame["flag_missing_expiration"] = frame["expiration_datetime_utc"].isna()
    frame["flag_expired_contract"] = frame["time_to_maturity"].isna() | (frame["time_to_maturity"] <= 0)

    low_volume = volume.fillna(0) < min_volume
    low_open_interest = open_interest.fillna(0) < min_open_interest
    frame["flag_low_liquidity"] = low_volume & low_open_interest

    flag_columns = [column for column in frame.columns if column.startswith("flag_")]
    frame["is_excluded"] = frame[flag_columns].any(axis=1)

    return frame


def add_exclusion_reason(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Add a compact primary exclusion reason for each quote."""
    frame = option_chain.copy()

    reason_order = [
        ("flag_missing_bid_ask", "missing bid/ask"),
        ("flag_negative_bid_ask", "negative bid/ask"),
        ("flag_crossed_market", "crossed market"),
        ("flag_zero_bid", "zero bid"),
        ("flag_zero_ask", "zero ask"),
        ("flag_invalid_mid", "invalid mid price"),
        ("flag_wide_spread", "wide spread"),
        ("flag_missing_strike", "missing strike"),
        ("flag_nonpositive_strike", "nonpositive strike"),
        ("flag_missing_expiration", "missing expiration"),
        ("flag_expired_contract", "expired contract"),
        ("flag_low_liquidity", "low liquidity"),
    ]

    reasons = pd.Series("retained", index=frame.index, dtype="object")

    for flag_column, reason in reason_order:
        if flag_column in frame.columns:
            reasons = reasons.mask((reasons == "retained") & frame[flag_column], reason)

    frame["exclusion_reason"] = reasons

    return frame


def clean_option_chain(
    option_chain: pd.DataFrame,
    underlying_price: float,
    max_spread_pct: float = 0.40,
    min_volume: int = 1,
    min_open_interest: int = 1,
) -> pd.DataFrame:
    """Return an option-chain dataset with quote-quality fields and flags."""
    required_columns = {"bid", "ask", "strike", "expiration"}
    missing_columns = required_columns.difference(option_chain.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required option-chain columns: {missing}")

    frame = coerce_option_columns(option_chain)
    frame = add_quote_metrics(frame)
    frame = add_time_to_maturity(frame)
    frame = add_moneyness(frame, underlying_price=underlying_price)
    frame = add_exclusion_flags(
        frame,
        max_spread_pct=max_spread_pct,
        min_volume=min_volume,
        min_open_interest=min_open_interest,
    )
    frame = add_exclusion_reason(frame)

    return frame


def retained_quotes(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Return quotes that pass the quote-quality filters."""
    if "is_excluded" not in option_chain.columns:
        raise ValueError("The option-chain dataset does not contain exclusion flags.")

    return option_chain.loc[~option_chain["is_excluded"]].copy()


def excluded_quotes(option_chain: pd.DataFrame) -> pd.DataFrame:
    """Return quotes removed by the quote-quality filters."""
    if "is_excluded" not in option_chain.columns:
        raise ValueError("The option-chain dataset does not contain exclusion flags.")

    return option_chain.loc[option_chain["is_excluded"]].copy()


def save_cleaned_option_chain(
    option_chain: pd.DataFrame,
    output_dir: str | Path = "data/processed",
    file_name: str = "cleaned_option_chain.csv",
) -> Path:
    """Save the cleaned option-chain dataset as a CSV file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / file_name
    option_chain.to_csv(output_path, index=False)

    return output_path
