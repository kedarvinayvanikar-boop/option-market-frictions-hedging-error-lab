"""
Black-Scholes pricing functions for European options.

The functions in this module provide a reusable pricing baseline for option
valuation, implied volatility calculations, Greek calculations, and hedging
analysis.
"""

from __future__ import annotations

import math
from typing import Literal

OptionType = Literal["call", "put"]


def normal_pdf(x: float) -> float:
    """Return the standard normal probability density at x."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def normal_cdf(x: float) -> float:
    """Return the standard normal cumulative probability at x."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _validate_inputs(S: float, K: float, T: float, r: float, sigma: float) -> None:
    """Validate common Black-Scholes inputs."""
    if S <= 0:
        raise ValueError("S must be positive.")
    if K <= 0:
        raise ValueError("K must be positive.")
    if T < 0:
        raise ValueError("T cannot be negative.")
    if sigma < 0:
        raise ValueError("sigma cannot be negative.")
    if not all(math.isfinite(x) for x in [S, K, T, r, sigma]):
        raise ValueError("Inputs must be finite numbers.")


def d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Return d1 from the Black-Scholes formula."""
    _validate_inputs(S, K, T, r, sigma)
    if T == 0:
        raise ValueError("d1 is undefined at expiry.")
    if sigma == 0:
        raise ValueError("d1 is undefined when sigma is zero.")

    numerator = math.log(S / K) + (r + 0.5 * sigma * sigma) * T
    denominator = sigma * math.sqrt(T)
    return numerator / denominator


def d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Return d2 from the Black-Scholes formula."""
    return d1(S, K, T, r, sigma) - sigma * math.sqrt(T)


def call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Price a European call option using the Black-Scholes formula."""
    _validate_inputs(S, K, T, r, sigma)

    if T == 0:
        return max(S - K, 0.0)

    if sigma == 0:
        discounted_strike = K * math.exp(-r * T)
        return max(S - discounted_strike, 0.0)

    d_1 = d1(S, K, T, r, sigma)
    d_2 = d_1 - sigma * math.sqrt(T)

    return S * normal_cdf(d_1) - K * math.exp(-r * T) * normal_cdf(d_2)


def put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Price a European put option using the Black-Scholes formula."""
    _validate_inputs(S, K, T, r, sigma)

    if T == 0:
        return max(K - S, 0.0)

    if sigma == 0:
        discounted_strike = K * math.exp(-r * T)
        return max(discounted_strike - S, 0.0)

    d_1 = d1(S, K, T, r, sigma)
    d_2 = d_1 - sigma * math.sqrt(T)

    return K * math.exp(-r * T) * normal_cdf(-d_2) - S * normal_cdf(-d_1)


def option_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> float:
    """Price a European call or put option."""
    option_type = option_type.lower()

    if option_type == "call":
        return call_price(S, K, T, r, sigma)
    if option_type == "put":
        return put_price(S, K, T, r, sigma)

    raise ValueError("option_type must be 'call' or 'put'.")


def intrinsic_value(S: float, K: float, option_type: OptionType) -> float:
    """Return the intrinsic value of a call or put."""
    if S <= 0:
        raise ValueError("S must be positive.")
    if K <= 0:
        raise ValueError("K must be positive.")

    option_type = option_type.lower()

    if option_type == "call":
        return max(S - K, 0.0)
    if option_type == "put":
        return max(K - S, 0.0)

    raise ValueError("option_type must be 'call' or 'put'.")


def put_call_parity_gap(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> float:
    """
    Return the put-call parity difference.

    For European options with no dividends:
        call - put = S - K * exp(-rT)

    A value near zero means the implementation is internally consistent.
    """
    _validate_inputs(S, K, T, r, sigma)

    call = call_price(S, K, T, r, sigma)
    put = put_price(S, K, T, r, sigma)
    parity_value = S - K * math.exp(-r * T)

    return call - put - parity_value
