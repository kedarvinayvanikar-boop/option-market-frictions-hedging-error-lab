import pytest

from src.black_scholes import call_price, put_price
from src.implied_vol import (
    calculate_iv_results,
    discounted_bound_check,
    implied_vol_bisection,
    solver_failure_summary,
    solver_success_summary,
)

import pandas as pd


def test_bisection_recovers_call_volatility():
    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.04
    sigma = 0.25

    price = call_price(S, K, T, r, sigma)
    result = implied_vol_bisection(price, S, K, T, r, "call")

    assert result.solver_status == "success"
    assert result.implied_volatility == pytest.approx(sigma, abs=1e-6)


def test_bisection_recovers_put_volatility():
    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.04
    sigma = 0.30

    price = put_price(S, K, T, r, sigma)
    result = implied_vol_bisection(price, S, K, T, r, "put")

    assert result.solver_status == "success"
    assert result.implied_volatility == pytest.approx(sigma, abs=1e-6)


def test_nonpositive_price_fails():
    result = implied_vol_bisection(0.0, 100.0, 100.0, 0.5, 0.04, "call")

    assert result.solver_status == "failed"
    assert result.failure_reason == "nonpositive option price"


def test_price_above_upper_bound_fails():
    result = implied_vol_bisection(150.0, 100.0, 100.0, 0.5, 0.04, "call")

    assert result.solver_status == "failed"
    assert result.failure_reason == "price above no-arbitrage upper bound"


def test_discounted_bound_check_for_valid_price():
    reason = discounted_bound_check(8.0, 100.0, 100.0, 0.5, 0.04, "call")

    assert reason is None


def test_batch_iv_results_contains_bid_mid_ask():
    clean_quotes = pd.DataFrame(
        {
            "contractSymbol": ["TEST_CALL", "TEST_PUT"],
            "option_type": ["call", "put"],
            "strike": [100.0, 100.0],
            "underlying_price": [100.0, 100.0],
            "time_to_maturity": [0.5, 0.5],
            "bid": [
                call_price(100.0, 100.0, 0.5, 0.04, 0.20),
                put_price(100.0, 100.0, 0.5, 0.04, 0.20),
            ],
            "mid_price": [
                call_price(100.0, 100.0, 0.5, 0.04, 0.25),
                put_price(100.0, 100.0, 0.5, 0.04, 0.25),
            ],
            "ask": [
                call_price(100.0, 100.0, 0.5, 0.04, 0.30),
                put_price(100.0, 100.0, 0.5, 0.04, 0.30),
            ],
            "is_excluded": [False, False],
        }
    )

    results = calculate_iv_results(clean_quotes, risk_free_rate=0.04)

    assert set(results["price_source"]) == {"bid", "mid", "ask"}
    assert len(results) == 6
    assert (results["solver_status"] == "success").all()


def test_solver_success_summary():
    iv_results = pd.DataFrame(
        {
            "price_source": ["bid", "bid", "mid", "ask"],
            "solver_status": ["success", "failed", "success", "success"],
        }
    )

    summary = solver_success_summary(iv_results)

    bid_success_rate = summary.loc[summary["price_source"] == "bid", "success_rate"].iloc[0]
    assert bid_success_rate == pytest.approx(0.5)


def test_solver_failure_summary_empty_when_no_failures():
    iv_results = pd.DataFrame(
        {
            "price_source": ["bid", "mid", "ask"],
            "solver_status": ["success", "success", "success"],
            "failure_reason": [None, None, None],
        }
    )

    summary = solver_failure_summary(iv_results)

    assert summary.empty
