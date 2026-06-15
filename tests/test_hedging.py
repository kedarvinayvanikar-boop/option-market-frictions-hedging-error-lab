import numpy as np
import pandas as pd
import pytest

from src.hedging import (
    HedgeContract,
    hedging_error_summary,
    option_payoff,
    simulate_delta_hedge_many_paths,
    simulate_delta_hedge_one_path,
)


def test_option_payoff_call():
    assert option_payoff(105.0, 100.0, "call") == pytest.approx(5.0)
    assert option_payoff(95.0, 100.0, "call") == pytest.approx(0.0)


def test_option_payoff_put():
    assert option_payoff(95.0, 100.0, "put") == pytest.approx(5.0)
    assert option_payoff(105.0, 100.0, "put") == pytest.approx(0.0)


def test_option_payoff_rejects_invalid_type():
    with pytest.raises(ValueError):
        option_payoff(100.0, 100.0, "straddle")


def test_one_path_outputs_expected_columns():
    stock_prices = np.array([100.0, 101.0, 99.0, 102.0])
    time_grid = np.array([0.0, 1 / 365.25, 2 / 365.25, 3 / 365.25])

    contract = HedgeContract(
        option_type="call",
        strike=100.0,
        maturity_years=3 / 365.25,
        risk_free_rate=0.04,
        volatility=0.25,
    )

    path_table, result = simulate_delta_hedge_one_path(
        stock_prices=stock_prices,
        time_grid=time_grid,
        contract=contract,
        transaction_cost_bps=5.0,
    )

    assert len(path_table) == 4
    assert "hedging_error" in result
    assert "cumulative_transaction_cost" in result
    assert result["cumulative_transaction_cost"] >= 0.0


def test_many_paths_returns_one_result_per_path():
    paths = pd.DataFrame(
        {
            "time_years": [0.0, 1 / 365.25, 2 / 365.25],
            "step": [0, 1, 2],
            "path_0000": [100.0, 101.0, 102.0],
            "path_0001": [100.0, 99.0, 98.0],
        }
    )

    contract = HedgeContract(
        option_type="call",
        strike=100.0,
        maturity_years=2 / 365.25,
        risk_free_rate=0.04,
        volatility=0.25,
    )

    results, details = simulate_delta_hedge_many_paths(
        paths=paths,
        contract=contract,
        transaction_cost_bps=2.0,
        store_path_details=True,
    )

    assert len(results) == 2
    assert details is not None
    assert set(results["path_id"]) == {"path_0000", "path_0001"}


def test_summary_contains_requested_metrics():
    hedge_results = pd.DataFrame(
        {
            "hedging_error": [-1.0, 0.5, 2.0],
            "cumulative_transaction_cost": [0.1, 0.2, 0.3],
            "rebalance_count": [10, 12, 11],
        }
    )

    summary = hedging_error_summary(hedge_results)

    metrics = set(summary["metric"])
    assert "mean_hedging_error" in metrics
    assert "std_hedging_error" in metrics
    assert "p05_hedging_error" in metrics
    assert "p95_hedging_error" in metrics
    assert "average_transaction_cost" in metrics
