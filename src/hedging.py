"""
Delta-hedging simulation utilities with configurable rebalance rules.

The module supports no hedge, fixed-frequency hedging, and a simple
event-triggered hedge. It is designed for scenario analysis across hedge
frequencies and transaction-cost assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.black_scholes import option_price
from src.greeks import delta as option_delta


@dataclass(frozen=True)
class HedgeContract:
    """Parameters for one European option hedge simulation."""
    option_type: str
    strike: float
    maturity_years: float
    risk_free_rate: float
    volatility: float
    position: int = 1


def option_payoff(stock_price: float, strike: float, option_type: str) -> float:
    """Return the European option payoff at expiry."""
    option_type = option_type.lower()

    if option_type == "call":
        return max(stock_price - strike, 0.0)
    if option_type == "put":
        return max(strike - stock_price, 0.0)

    raise ValueError("option_type must be 'call' or 'put'.")


def _path_columns(paths: pd.DataFrame) -> list[str]:
    """Return simulated path columns from a wide path DataFrame."""
    columns = [column for column in paths.columns if column.startswith("path_")]
    if not columns:
        raise ValueError("No path columns found. Expected columns like path_0000.")
    return columns


def _remaining_time(maturity_years: float, elapsed_time: float) -> float:
    """Return remaining option time to expiry."""
    return max(maturity_years - elapsed_time, 0.0)


def _option_value_or_payoff(stock_price: float, contract: HedgeContract, remaining_time: float) -> float:
    """Return option model value before expiry and payoff at expiry."""
    if remaining_time <= 0.0:
        return option_payoff(stock_price, contract.strike, contract.option_type)

    return option_price(
        stock_price,
        contract.strike,
        remaining_time,
        contract.risk_free_rate,
        contract.volatility,
        contract.option_type,
    )


def _delta_or_zero(stock_price: float, contract: HedgeContract, remaining_time: float) -> float:
    """Return Delta before expiry and zero at terminal time."""
    if remaining_time <= 0.0:
        return 0.0

    return option_delta(
        stock_price,
        contract.strike,
        remaining_time,
        contract.risk_free_rate,
        contract.volatility,
        contract.option_type,
    )


def _should_rebalance(
    step: int,
    final_step: int,
    current_delta: float,
    stock_position: float,
    hedge_mode: str,
    rebalance_interval: int | None,
    event_delta_threshold: float | None,
    position: int,
) -> bool:
    """Return whether the hedge should be rebalanced at this step."""
    if step >= final_step:
        return True

    if hedge_mode == "none":
        return False

    if hedge_mode == "fixed":
        if rebalance_interval is None or rebalance_interval <= 0:
            raise ValueError("rebalance_interval must be positive for fixed hedging.")
        return step % rebalance_interval == 0

    if hedge_mode == "event":
        if event_delta_threshold is None or event_delta_threshold <= 0:
            raise ValueError("event_delta_threshold must be positive for event hedging.")
        current_net_delta = position * current_delta + stock_position
        return abs(current_net_delta) >= event_delta_threshold

    raise ValueError("hedge_mode must be 'none', 'fixed', or 'event'.")


def simulate_delta_hedge_one_path(
    stock_prices: np.ndarray,
    time_grid: np.ndarray,
    contract: HedgeContract,
    transaction_cost_bps: float = 0.0,
    hedge_mode: str = "fixed",
    rebalance_interval: int | None = 1,
    event_delta_threshold: float | None = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Simulate delta hedging for one stock path.

    A fixed hedge rebalances every N time steps. A no-hedge scenario buys the
    option and holds it. An event-triggered hedge rebalances when net Delta
    drifts beyond a threshold.
    """
    if len(stock_prices) != len(time_grid):
        raise ValueError("stock_prices and time_grid must have the same length.")
    if len(stock_prices) < 2:
        raise ValueError("At least two time points are required.")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps cannot be negative.")

    transaction_cost_rate = transaction_cost_bps / 10_000.0
    final_step = len(stock_prices) - 1

    first_stock_price = float(stock_prices[0])
    first_time = float(time_grid[0])
    first_remaining_time = _remaining_time(contract.maturity_years, first_time)
    first_option_value = _option_value_or_payoff(first_stock_price, contract, first_remaining_time)
    first_delta = _delta_or_zero(first_stock_price, contract, first_remaining_time)

    if hedge_mode == "none":
        target_stock_position = 0.0
    else:
        target_stock_position = -contract.position * first_delta

    stock_trade = target_stock_position
    trade_notional = abs(stock_trade) * first_stock_price
    transaction_cost = trade_notional * transaction_cost_rate

    cash_account = (
        -contract.position * first_option_value
        - stock_trade * first_stock_price
        - transaction_cost
    )

    stock_position = target_stock_position
    cumulative_transaction_cost = transaction_cost

    rows = [
        {
            "step": 0,
            "time_years": first_time,
            "stock_price": first_stock_price,
            "remaining_time": first_remaining_time,
            "option_value": first_option_value,
            "delta": first_delta,
            "target_stock_position": target_stock_position,
            "stock_trade": stock_trade,
            "cash_account": cash_account,
            "transaction_cost": transaction_cost,
            "cumulative_transaction_cost": cumulative_transaction_cost,
            "rebalanced": abs(stock_trade) > 1e-12,
            "hedge_portfolio_value": stock_position * first_stock_price + cash_account,
            "option_position_value": contract.position * first_option_value,
            "combined_position_value": (
                contract.position * first_option_value
                + stock_position * first_stock_price
                + cash_account
            ),
        }
    ]

    for step in range(1, len(stock_prices)):
        stock_price = float(stock_prices[step])
        current_time = float(time_grid[step])
        previous_time = float(time_grid[step - 1])
        dt = current_time - previous_time

        if dt < -1e-12:
            raise ValueError("time_grid must be nondecreasing.")

        cash_account *= np.exp(contract.risk_free_rate * max(dt, 0.0))

        remaining_time = _remaining_time(contract.maturity_years, current_time)
        option_value = _option_value_or_payoff(stock_price, contract, remaining_time)
        current_delta = _delta_or_zero(stock_price, contract, remaining_time)

        rebalance_now = _should_rebalance(
            step=step,
            final_step=final_step,
            current_delta=current_delta,
            stock_position=stock_position,
            hedge_mode=hedge_mode,
            rebalance_interval=rebalance_interval,
            event_delta_threshold=event_delta_threshold,
            position=contract.position,
        )

        if step == final_step or remaining_time <= 0.0:
            target_stock_position = 0.0
        elif rebalance_now:
            target_stock_position = -contract.position * current_delta
        else:
            target_stock_position = stock_position

        stock_trade = target_stock_position - stock_position
        trade_notional = abs(stock_trade) * stock_price
        transaction_cost = trade_notional * transaction_cost_rate

        cash_account += -stock_trade * stock_price - transaction_cost
        stock_position = target_stock_position
        cumulative_transaction_cost += transaction_cost

        hedge_portfolio_value = stock_position * stock_price + cash_account
        option_position_value = contract.position * option_value
        combined_position_value = option_position_value + hedge_portfolio_value

        rows.append(
            {
                "step": step,
                "time_years": current_time,
                "stock_price": stock_price,
                "remaining_time": remaining_time,
                "option_value": option_value,
                "delta": current_delta,
                "target_stock_position": target_stock_position,
                "stock_trade": stock_trade,
                "cash_account": cash_account,
                "transaction_cost": transaction_cost,
                "cumulative_transaction_cost": cumulative_transaction_cost,
                "rebalanced": abs(stock_trade) > 1e-12,
                "hedge_portfolio_value": hedge_portfolio_value,
                "option_position_value": option_position_value,
                "combined_position_value": combined_position_value,
            }
        )

    path_table = pd.DataFrame(rows)

    terminal_stock_price = float(stock_prices[-1])
    terminal_payoff = option_payoff(terminal_stock_price, contract.strike, contract.option_type)
    terminal_row = path_table.iloc[-1]

    result = {
        "terminal_stock_price": terminal_stock_price,
        "option_payoff": terminal_payoff,
        "hedge_portfolio_value": float(terminal_row["hedge_portfolio_value"]),
        "option_position_value": contract.position * terminal_payoff,
        "combined_position_value": float(terminal_row["combined_position_value"]),
        "hedging_error": float(terminal_row["combined_position_value"]),
        "cumulative_transaction_cost": float(terminal_row["cumulative_transaction_cost"]),
        "rebalance_count": int(path_table["rebalanced"].sum()),
    }

    return path_table, result


def simulate_delta_hedge_many_paths(
    paths: pd.DataFrame,
    contract: HedgeContract,
    transaction_cost_bps: float = 0.0,
    hedge_mode: str = "fixed",
    rebalance_interval: int | None = 1,
    event_delta_threshold: float | None = None,
    store_path_details: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Simulate delta hedging across many stock price paths."""
    if "time_years" not in paths.columns:
        raise ValueError("paths must contain a time_years column.")

    path_cols = _path_columns(paths)
    time_grid = paths["time_years"].to_numpy(dtype=float)

    result_rows = []
    detail_tables = []

    for path_col in path_cols:
        stock_prices = paths[path_col].to_numpy(dtype=float)
        path_table, result = simulate_delta_hedge_one_path(
            stock_prices=stock_prices,
            time_grid=time_grid,
            contract=contract,
            transaction_cost_bps=transaction_cost_bps,
            hedge_mode=hedge_mode,
            rebalance_interval=rebalance_interval,
            event_delta_threshold=event_delta_threshold,
        )

        result["path_id"] = path_col
        result_rows.append(result)

        if store_path_details:
            path_table = path_table.copy()
            path_table.insert(0, "path_id", path_col)
            detail_tables.append(path_table)

    results = pd.DataFrame(result_rows)
    details = pd.concat(detail_tables, ignore_index=True) if store_path_details else None

    return results, details


def hedging_error_summary(hedge_results: pd.DataFrame) -> pd.DataFrame:
    """Return summary statistics for hedging error and transaction costs."""
    errors = hedge_results["hedging_error"]
    costs = hedge_results["cumulative_transaction_cost"]

    return pd.DataFrame(
        {
            "metric": [
                "path_count",
                "mean_hedging_error",
                "std_hedging_error",
                "p05_hedging_error",
                "p50_hedging_error",
                "p95_hedging_error",
                "mean_abs_hedging_error",
                "average_transaction_cost",
                "average_rebalance_count",
            ],
            "value": [
                len(hedge_results),
                errors.mean(),
                errors.std(),
                errors.quantile(0.05),
                errors.quantile(0.50),
                errors.quantile(0.95),
                errors.abs().mean(),
                costs.mean(),
                hedge_results["rebalance_count"].mean(),
            ],
        }
    )


def plot_hedging_error_histogram(
    hedge_results: pd.DataFrame,
    output_path: str | Path,
    bins: int = 50,
) -> Path:
    """Save a hedging error histogram."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if "hedging_error" not in hedge_results.columns:
        raise ValueError("hedge_results must contain hedging_error.")

    plt.figure(figsize=(9, 5))
    plt.hist(hedge_results["hedging_error"], bins=bins)
    plt.xlabel("Hedging Error")
    plt.ylabel("Path Count")
    plt.title("Delta-Hedging Error Distribution")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_transaction_cost_distribution(
    hedge_results: pd.DataFrame,
    output_path: str | Path,
    bins: int = 50,
) -> Path:
    """Save a transaction cost distribution chart."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if "cumulative_transaction_cost" not in hedge_results.columns:
        raise ValueError("hedge_results must contain cumulative_transaction_cost.")

    plt.figure(figsize=(9, 5))
    plt.hist(hedge_results["cumulative_transaction_cost"], bins=bins)
    plt.xlabel("Cumulative Transaction Cost")
    plt.ylabel("Path Count")
    plt.title("Transaction Cost Distribution")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def save_hedging_outputs(
    hedge_results: pd.DataFrame,
    summary: pd.DataFrame,
    output_dir: str | Path = "data/processed",
) -> dict[str, Path]:
    """Save hedging result tables."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results_path = output_dir / "hedge_results.csv"
    summary_path = output_dir / "hedging_error_summary.csv"

    hedge_results.to_csv(results_path, index=False)
    summary.to_csv(summary_path, index=False)

    return {
        "hedge_results": results_path,
        "hedging_error_summary": summary_path,
    }


def build_hedging_figures(
    hedge_results: pd.DataFrame,
    output_dir: str | Path = "figures",
) -> dict[str, Path]:
    """Save standard hedging simulation figures."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    return {
        "hedging_error_histogram": plot_hedging_error_histogram(
            hedge_results,
            output_dir / "hedging_error_histogram.png",
        ),
        "transaction_cost_distribution": plot_transaction_cost_distribution(
            hedge_results,
            output_dir / "transaction_cost_distribution.png",
        ),
    }
