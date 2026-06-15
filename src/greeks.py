"""
Black-Scholes Greeks for European options.

The functions use the same no-dividend Black-Scholes assumptions as the
pricing module. Greeks are local sensitivities, so they describe small changes
around the current input values.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from src.black_scholes import d1, d2, normal_cdf, normal_pdf

OptionType = Literal["call", "put"]


@dataclass(frozen=True)
class Greeks:
    """Container for Black-Scholes Greek values."""
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def _validate_greek_inputs(S: float, K: float, T: float, r: float, sigma: float) -> None:
    """Validate inputs for Greek calculations."""
    if S <= 0:
        raise ValueError("S must be positive.")
    if K <= 0:
        raise ValueError("K must be positive.")
    if T <= 0:
        raise ValueError("T must be positive for Greek calculations.")
    if sigma <= 0:
        raise ValueError("sigma must be positive for Greek calculations.")
    if not all(math.isfinite(x) for x in [S, K, T, r, sigma]):
        raise ValueError("Inputs must be finite numbers.")


def delta(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType) -> float:
    """Return Black-Scholes delta."""
    _validate_greek_inputs(S, K, T, r, sigma)
    option_type = option_type.lower()
    d_1 = d1(S, K, T, r, sigma)

    if option_type == "call":
        return normal_cdf(d_1)
    if option_type == "put":
        return normal_cdf(d_1) - 1.0

    raise ValueError("option_type must be 'call' or 'put'.")


def gamma(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Return Black-Scholes gamma."""
    _validate_greek_inputs(S, K, T, r, sigma)
    d_1 = d1(S, K, T, r, sigma)
    return normal_pdf(d_1) / (S * sigma * math.sqrt(T))


def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """
    Return Black-Scholes vega.

    The value is the price change for a 1.00 change in volatility. Divide by
    100 to express vega per one volatility point.
    """
    _validate_greek_inputs(S, K, T, r, sigma)
    d_1 = d1(S, K, T, r, sigma)
    return S * normal_pdf(d_1) * math.sqrt(T)


def theta(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType) -> float:
    """
    Return annualized Black-Scholes theta.

    The value is the model's sensitivity to the passage of one year. Divide by
    365 to approximate theta per calendar day.
    """
    _validate_greek_inputs(S, K, T, r, sigma)
    option_type = option_type.lower()
    d_1 = d1(S, K, T, r, sigma)
    d_2 = d2(S, K, T, r, sigma)
    time_decay = -(S * normal_pdf(d_1) * sigma) / (2.0 * math.sqrt(T))

    if option_type == "call":
        return time_decay - r * K * math.exp(-r * T) * normal_cdf(d_2)
    if option_type == "put":
        return time_decay + r * K * math.exp(-r * T) * normal_cdf(-d_2)

    raise ValueError("option_type must be 'call' or 'put'.")


def rho(S: float, K: float, T: float, r: float, sigma: float, option_type: OptionType) -> float:
    """Return Black-Scholes rho."""
    _validate_greek_inputs(S, K, T, r, sigma)
    option_type = option_type.lower()
    d_2 = d2(S, K, T, r, sigma)

    if option_type == "call":
        return K * T * math.exp(-r * T) * normal_cdf(d_2)
    if option_type == "put":
        return -K * T * math.exp(-r * T) * normal_cdf(-d_2)

    raise ValueError("option_type must be 'call' or 'put'.")


def calculate_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> Greeks:
    """Return all Black-Scholes Greeks for one option."""
    return Greeks(
        delta=delta(S, K, T, r, sigma, option_type),
        gamma=gamma(S, K, T, r, sigma),
        vega=vega(S, K, T, r, sigma),
        theta=theta(S, K, T, r, sigma, option_type),
        rho=rho(S, K, T, r, sigma, option_type),
    )


def calculate_greeks_dict(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> dict[str, float]:
    """Return Greeks as a dictionary."""
    values = calculate_greeks(S, K, T, r, sigma, option_type)
    return {
        "delta": values.delta,
        "gamma": values.gamma,
        "vega": values.vega,
        "theta": values.theta,
        "rho": values.rho,
    }


def theta_per_day(theta_annualized: float) -> float:
    """Convert annualized theta to an approximate calendar-day theta."""
    return theta_annualized / 365.0


def vega_per_vol_point(vega_value: float) -> float:
    """Convert vega per 1.00 volatility change to vega per 1 volatility point."""
    return vega_value / 100.0
