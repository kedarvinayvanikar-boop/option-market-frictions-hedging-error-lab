"""
Option payoff functions.

This module keeps the first part of the project focused on the core payoff
relationships that sit underneath later pricing, Greek, and hedging work.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def call_payoff(stock_prices: ArrayLike, strike: float) -> np.ndarray:
    """
    Payoff of a long call at expiry.

    A call option has value when the stock finishes above the strike.
    If S is the stock price at expiry and K is the strike, the payoff is:

        max(S - K, 0)
    """
    s = np.asarray(stock_prices, dtype=float)
    return np.maximum(s - strike, 0.0)


def put_payoff(stock_prices: ArrayLike, strike: float) -> np.ndarray:
    """
    Payoff of a long put at expiry.

    A put option has value when the stock finishes below the strike.
    If S is the stock price at expiry and K is the strike, the payoff is:

        max(K - S, 0)
    """
    s = np.asarray(stock_prices, dtype=float)
    return np.maximum(strike - s, 0.0)


def long_call_profit(stock_prices: ArrayLike, strike: float, premium: float) -> np.ndarray:
    """
    Profit of a long call position.

    The buyer pays the option premium upfront, so profit is the expiry payoff
    minus the premium paid.
    """
    return call_payoff(stock_prices, strike) - premium


def long_put_profit(stock_prices: ArrayLike, strike: float, premium: float) -> np.ndarray:
    """
    Profit of a long put position.

    The buyer pays the option premium upfront, so profit is the expiry payoff
    minus the premium paid.
    """
    return put_payoff(stock_prices, strike) - premium


def short_call_profit(stock_prices: ArrayLike, strike: float, premium: float) -> np.ndarray:
    """
    Profit of a short call position.

    The seller receives the premium upfront but is responsible for the call
    payoff owed to the buyer at expiry.
    """
    return premium - call_payoff(stock_prices, strike)


def short_put_profit(stock_prices: ArrayLike, strike: float, premium: float) -> np.ndarray:
    """
    Profit of a short put position.

    The seller receives the premium upfront but is responsible for the put
    payoff owed to the buyer at expiry.
    """
    return premium - put_payoff(stock_prices, strike)


def breakeven_long_call(strike: float, premium: float) -> float:
    """Stock price where a long call position breaks even."""
    return strike + premium


def breakeven_long_put(strike: float, premium: float) -> float:
    """Stock price where a long put position breaks even."""
    return strike - premium


if __name__ == "__main__":
    prices = np.array([80, 90, 100, 110, 120], dtype=float)
    strike = 100.0
    premium = 5.0

    print("Stock prices:", prices)
    print("Call payoff:", call_payoff(prices, strike))
    print("Put payoff:", put_payoff(prices, strike))
    print("Long call profit:", long_call_profit(prices, strike, premium))
    print("Long put profit:", long_put_profit(prices, strike, premium))
