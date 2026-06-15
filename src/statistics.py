"""
Return and volatility calculations.

These functions connect historical stock-price movement to the volatility input
that later appears in Black-Scholes pricing, implied volatility, Greeks, and
hedging simulations.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


def simple_returns(prices: pd.Series) -> pd.Series:
    """
    Calculate simple returns.

        R_t = (P_t / P_{t-1}) - 1
    """
    return prices.pct_change()


def log_returns(prices: pd.Series) -> pd.Series:
    """
    Calculate log returns.

        r_t = ln(P_t / P_{t-1})

    Log returns are common in finance because they add cleanly over time.
    """
    return np.log(prices / prices.shift(1))


def mean_return(returns: pd.Series) -> float:
    """Average daily return."""
    return float(returns.dropna().mean())


def variance(returns: pd.Series, sample: bool = True) -> float:
    """
    Return variance.

    The sample version uses n - 1 in the denominator, which is the usual choice
    when estimating volatility from historical data.
    """
    ddof = 1 if sample else 0
    return float(returns.dropna().var(ddof=ddof))


def standard_deviation(returns: pd.Series, sample: bool = True) -> float:
    """Daily return standard deviation."""
    ddof = 1 if sample else 0
    return float(returns.dropna().std(ddof=ddof))


def annualized_volatility(
    returns: pd.Series,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Annualize daily volatility.

    Annual variance is approximated as daily variance times 252. Since
    volatility is the square root of variance, daily volatility is scaled by
    sqrt(252).
    """
    daily_vol = standard_deviation(returns, sample=True)
    return float(daily_vol * math.sqrt(periods_per_year))


def z_scores(values: pd.Series) -> pd.Series:
    """Convert values into z-scores using the sample mean and standard deviation."""
    clean = values.dropna()
    mu = clean.mean()
    sigma = clean.std(ddof=1)

    if sigma == 0:
        raise ValueError("Standard deviation is zero, so z-scores are undefined.")

    return (values - mu) / sigma


def normal_pdf(x: np.ndarray, mean: float, std: float) -> np.ndarray:
    """
    Normal probability density function.

    This is used for plotting a normal curve against the empirical return
    histogram.
    """
    if std <= 0:
        raise ValueError("Standard deviation must be positive.")

    coefficient = 1.0 / (std * math.sqrt(2.0 * math.pi))
    exponent = -0.5 * ((x - mean) / std) ** 2
    return coefficient * np.exp(exponent)


def add_return_columns(prices: pd.DataFrame) -> pd.DataFrame:
    """Add simple and log returns to a price table."""
    required = {"Date", "Ticker", "Close"}
    missing = required - set(prices.columns)
    if missing:
        raise ValueError(f"Missing required column(s): {sorted(missing)}")

    result = prices.copy()
    result["SimpleReturn"] = simple_returns(result["Close"])
    result["LogReturn"] = log_returns(result["Close"])

    return result


def return_summary(returns: pd.Series) -> pd.DataFrame:
    """Create a compact summary table for daily returns and annualized volatility."""
    clean = returns.dropna()

    rows = {
        "observations": len(clean),
        "mean_daily_return": mean_return(clean),
        "daily_variance": variance(clean),
        "daily_volatility": standard_deviation(clean),
        "annualized_volatility": annualized_volatility(clean),
        "min_daily_return": float(clean.min()),
        "max_daily_return": float(clean.max()),
    }

    return pd.DataFrame(
        [{"Metric": key, "Value": value} for key, value in rows.items()]
    )
