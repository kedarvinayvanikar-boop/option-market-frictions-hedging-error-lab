"""
Market data loading utilities.

The option-chain functions preserve vendor fields and add snapshot metadata so
each pull can be reproduced later. The price-history functions load the daily
close prices used for the return and volatility analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd


def current_utc_timestamp() -> str:
    """Return a compact UTC timestamp for snapshot filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")


def fetch_price_history(
    ticker_symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Download historical price data for one ticker using yfinance."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("Install yfinance before downloading market data.") from exc

    ticker = yf.Ticker(ticker_symbol)
    history = ticker.history(period=period, interval=interval)

    if history.empty:
        raise ValueError(f"No historical price data returned for {ticker_symbol}.")

    history = history.reset_index()
    history["ticker"] = ticker_symbol.upper()

    return history


def get_option_expiries(ticker_symbol: str) -> list[str]:
    """Return available option expiry dates for a ticker."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("Install yfinance before downloading option-chain data.") from exc

    ticker = yf.Ticker(ticker_symbol)
    expiries = list(ticker.options)

    if not expiries:
        raise ValueError(f"No option expiries returned for {ticker_symbol}.")

    return expiries


def _standardize_option_frame(
    option_frame: pd.DataFrame,
    ticker_symbol: str,
    expiry: str,
    option_type: str,
    snapshot_time_utc: str,
) -> pd.DataFrame:
    """Add consistent metadata fields to a raw option-chain frame."""
    if option_frame.empty:
        return option_frame.copy()

    frame = option_frame.copy()

    frame["ticker"] = ticker_symbol.upper()
    frame["expiration"] = expiry
    frame["option_type"] = option_type
    frame["snapshot_time_utc"] = snapshot_time_utc
    frame["source"] = "yfinance"

    if "bid" in frame.columns and "ask" in frame.columns:
        frame["mid_price"] = (frame["bid"] + frame["ask"]) / 2.0

    leading_columns = [
        "ticker",
        "expiration",
        "option_type",
        "snapshot_time_utc",
        "source",
    ]

    ordered_columns = leading_columns + [
        column for column in frame.columns if column not in leading_columns
    ]

    return frame[ordered_columns]


def fetch_option_chain_for_expiry(
    ticker_symbol: str,
    expiry: str,
    snapshot_time_utc: str | None = None,
) -> pd.DataFrame:
    """Download calls and puts for one option expiry."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError("Install yfinance before downloading option-chain data.") from exc

    snapshot_time_utc = snapshot_time_utc or datetime.now(timezone.utc).isoformat()
    ticker = yf.Ticker(ticker_symbol)
    chain = ticker.option_chain(expiry)

    calls = _standardize_option_frame(
        chain.calls,
        ticker_symbol=ticker_symbol,
        expiry=expiry,
        option_type="call",
        snapshot_time_utc=snapshot_time_utc,
    )

    puts = _standardize_option_frame(
        chain.puts,
        ticker_symbol=ticker_symbol,
        expiry=expiry,
        option_type="put",
        snapshot_time_utc=snapshot_time_utc,
    )

    combined = pd.concat([calls, puts], ignore_index=True)

    if combined.empty:
        raise ValueError(f"No option quotes returned for {ticker_symbol} {expiry}.")

    return combined


def fetch_option_chains(
    ticker_symbol: str,
    max_expiries: int = 4,
    expiries: Iterable[str] | None = None,
) -> pd.DataFrame:
    """
    Download option-chain quotes across multiple expiries.

    If expiries are not provided, the nearest available expiries are used.
    """
    if max_expiries <= 0:
        raise ValueError("max_expiries must be positive.")

    snapshot_time_utc = datetime.now(timezone.utc).isoformat()

    if expiries is None:
        selected_expiries = get_option_expiries(ticker_symbol)[:max_expiries]
    else:
        selected_expiries = list(expiries)[:max_expiries]

    if not selected_expiries:
        raise ValueError("At least one expiry is required.")

    frames = [
        fetch_option_chain_for_expiry(
            ticker_symbol=ticker_symbol,
            expiry=expiry,
            snapshot_time_utc=snapshot_time_utc,
        )
        for expiry in selected_expiries
    ]

    option_chain = pd.concat(frames, ignore_index=True)

    return option_chain


def save_option_chain_snapshot(
    option_chain: pd.DataFrame,
    output_dir: str | Path = "data/raw",
    ticker_symbol: str | None = None,
) -> Path:
    """Save a frozen option-chain snapshot as a CSV file."""
    if option_chain.empty:
        raise ValueError("Cannot save an empty option-chain snapshot.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if ticker_symbol is None:
        if "ticker" in option_chain.columns and not option_chain["ticker"].dropna().empty:
            ticker_symbol = str(option_chain["ticker"].dropna().iloc[0])
        else:
            ticker_symbol = "OPTIONS"

    timestamp = current_utc_timestamp()
    file_name = f"{ticker_symbol.upper()}_option_chain_snapshot_{timestamp}.csv"
    output_path = output_dir / file_name

    option_chain.to_csv(output_path, index=False)

    return output_path


def load_option_chain_snapshot(path: str | Path) -> pd.DataFrame:
    """Load a saved option-chain snapshot from CSV."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")

    return pd.read_csv(path)


def build_sample_option_chain(ticker_symbol: str = "SPY") -> pd.DataFrame:
    """
    Build a small option-chain sample with the same core fields as the live pull.

    The sample is only a fallback for workflow testing when live data is
    unavailable. It should not be used for empirical conclusions.
    """
    snapshot_time_utc = datetime.now(timezone.utc).isoformat()
    ticker_symbol = ticker_symbol.upper()

    rows = [
        {
            "ticker": ticker_symbol,
            "expiration": "2026-06-19",
            "option_type": "call",
            "snapshot_time_utc": snapshot_time_utc,
            "source": "sample",
            "contractSymbol": f"{ticker_symbol}260619C00580000",
            "lastTradeDate": snapshot_time_utc,
            "strike": 580.0,
            "lastPrice": 18.20,
            "bid": 18.00,
            "ask": 18.40,
            "change": 0.0,
            "percentChange": 0.0,
            "volume": 120,
            "openInterest": 2500,
            "impliedVolatility": 0.185,
            "inTheMoney": True,
            "contractSize": "REGULAR",
            "currency": "USD",
        },
        {
            "ticker": ticker_symbol,
            "expiration": "2026-06-19",
            "option_type": "call",
            "snapshot_time_utc": snapshot_time_utc,
            "source": "sample",
            "contractSymbol": f"{ticker_symbol}260619C00600000",
            "lastTradeDate": snapshot_time_utc,
            "strike": 600.0,
            "lastPrice": 8.75,
            "bid": 8.60,
            "ask": 8.90,
            "change": 0.0,
            "percentChange": 0.0,
            "volume": 300,
            "openInterest": 4200,
            "impliedVolatility": 0.195,
            "inTheMoney": False,
            "contractSize": "REGULAR",
            "currency": "USD",
        },
        {
            "ticker": ticker_symbol,
            "expiration": "2026-06-19",
            "option_type": "put",
            "snapshot_time_utc": snapshot_time_utc,
            "source": "sample",
            "contractSymbol": f"{ticker_symbol}260619P00580000",
            "lastTradeDate": snapshot_time_utc,
            "strike": 580.0,
            "lastPrice": 6.30,
            "bid": 6.10,
            "ask": 6.50,
            "change": 0.0,
            "percentChange": 0.0,
            "volume": 180,
            "openInterest": 3600,
            "impliedVolatility": 0.205,
            "inTheMoney": False,
            "contractSize": "REGULAR",
            "currency": "USD",
        },
        {
            "ticker": ticker_symbol,
            "expiration": "2026-06-19",
            "option_type": "put",
            "snapshot_time_utc": snapshot_time_utc,
            "source": "sample",
            "contractSymbol": f"{ticker_symbol}260619P00600000",
            "lastTradeDate": snapshot_time_utc,
            "strike": 600.0,
            "lastPrice": 14.10,
            "bid": 13.85,
            "ask": 14.35,
            "change": 0.0,
            "percentChange": 0.0,
            "volume": 210,
            "openInterest": 3900,
            "impliedVolatility": 0.215,
            "inTheMoney": True,
            "contractSize": "REGULAR",
            "currency": "USD",
        },
    ]

    sample = pd.DataFrame(rows)
    sample["mid_price"] = (sample["bid"] + sample["ask"]) / 2.0

    return sample


REQUIRED_PRICE_COLUMNS = {"Date", "Close"}


def load_price_csv(path: str | Path, ticker: str | None = None) -> pd.DataFrame:
    """
    Load daily close prices from a CSV file.

    Expected columns:
        Date, Close

    A Ticker column is optional. If the CSV does not include one, the ticker
    argument is used. If no ticker is provided, the ticker is recorded as
    UNKNOWN.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Price file not found: {csv_path}")

    prices = pd.read_csv(csv_path)

    missing = REQUIRED_PRICE_COLUMNS - set(prices.columns)
    if missing:
        raise ValueError(f"Missing required column(s): {sorted(missing)}")

    prices = prices.copy()
    prices["Date"] = pd.to_datetime(prices["Date"])
    prices["Close"] = pd.to_numeric(prices["Close"], errors="coerce")

    if "Ticker" not in prices.columns:
        prices["Ticker"] = ticker or "UNKNOWN"

    prices = prices.dropna(subset=["Date", "Close"])
    prices = prices.sort_values("Date").reset_index(drop=True)

    return prices[["Date", "Ticker", "Close"]]


def load_yfinance_prices(
    ticker: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Download daily close prices from yfinance.

    This function requires internet access and the yfinance package. The rest
    of the project does not depend on yfinance directly, which keeps the
    pipeline easier to test.
    """
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "yfinance is not installed. Install it with: pip install yfinance"
        ) from exc

    data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

    if data.empty:
        raise ValueError(f"No price data returned for {ticker}.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    if "Close" not in data.columns:
        raise ValueError("Downloaded data does not contain a Close column.")

    prices = data[["Close"]].reset_index()
    prices["Ticker"] = ticker

    return prices[["Date", "Ticker", "Close"]]


def load_prices(
    ticker: str = "SPY",
    start: str = "2024-01-01",
    end: str = "2025-01-01",
    csv_path: str | Path | None = None,
    use_yfinance: bool = False,
) -> pd.DataFrame:
    """
    Load prices from either a local CSV file or yfinance.

    For a reproducible notebook, use a local CSV. For live market data, set
    use_yfinance=True.
    """
    if csv_path is not None:
        return load_price_csv(csv_path, ticker=ticker)

    if use_yfinance:
        return load_yfinance_prices(ticker=ticker, start=start, end=end)

    raise ValueError("Provide csv_path or set use_yfinance=True.")
