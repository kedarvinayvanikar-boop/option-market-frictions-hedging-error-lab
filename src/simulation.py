"""
Stock price path simulation utilities.

The module uses geometric Brownian motion as a simple model for simulated
stock paths. These paths are not forecasts. They are controlled scenarios used
to test hedging logic under many possible price paths.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def validate_simulation_inputs(
    starting_price: float,
    drift: float,
    volatility: float,
    time_horizon: float,
    steps: int,
    num_paths: int,
) -> None:
    """Validate geometric Brownian motion simulation inputs."""
    if starting_price <= 0:
        raise ValueError("starting_price must be positive.")
    if volatility < 0:
        raise ValueError("volatility cannot be negative.")
    if time_horizon <= 0:
        raise ValueError("time_horizon must be positive.")
    if steps <= 0:
        raise ValueError("steps must be positive.")
    if num_paths <= 0:
        raise ValueError("num_paths must be positive.")
    if not np.isfinite([starting_price, drift, volatility, time_horizon]).all():
        raise ValueError("starting_price, drift, volatility, and time_horizon must be finite.")


def simulate_gbm_paths(
    starting_price: float,
    drift: float,
    volatility: float,
    time_horizon: float,
    steps: int,
    num_paths: int,
    random_seed: int | None = None,
) -> pd.DataFrame:
    """
    Simulate stock price paths using geometric Brownian motion.

    The model uses the exact log-return step:

        S[t+1] = S[t] * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)

    where Z is a standard normal random draw.
    """
    validate_simulation_inputs(
        starting_price=starting_price,
        drift=drift,
        volatility=volatility,
        time_horizon=time_horizon,
        steps=steps,
        num_paths=num_paths,
    )

    rng = np.random.default_rng(random_seed)
    dt = time_horizon / steps

    random_shocks = rng.standard_normal(size=(steps, num_paths))
    log_returns = (
        (drift - 0.5 * volatility**2) * dt
        + volatility * np.sqrt(dt) * random_shocks
    )

    cumulative_log_returns = np.vstack(
        [
            np.zeros(num_paths),
            np.cumsum(log_returns, axis=0),
        ]
    )

    prices = starting_price * np.exp(cumulative_log_returns)
    time_grid = np.linspace(0.0, time_horizon, steps + 1)

    path_columns = [f"path_{path_id:04d}" for path_id in range(num_paths)]
    paths = pd.DataFrame(prices, columns=path_columns)
    paths.insert(0, "time_years", time_grid)
    paths.insert(1, "step", np.arange(steps + 1))

    return paths


def final_price_distribution(paths: pd.DataFrame) -> pd.Series:
    """Return the final simulated price from each path."""
    path_columns = [column for column in paths.columns if column.startswith("path_")]
    if not path_columns:
        raise ValueError("No path columns found.")

    return paths[path_columns].iloc[-1].copy()


def simulation_summary(paths: pd.DataFrame) -> pd.DataFrame:
    """Return summary statistics for simulated final prices and returns."""
    path_columns = [column for column in paths.columns if column.startswith("path_")]
    if not path_columns:
        raise ValueError("No path columns found.")

    starting_prices = paths[path_columns].iloc[0]
    final_prices = paths[path_columns].iloc[-1]
    total_returns = final_prices / starting_prices - 1.0

    summary = pd.DataFrame(
        {
            "metric": [
                "num_paths",
                "num_steps",
                "starting_price",
                "mean_final_price",
                "median_final_price",
                "std_final_price",
                "min_final_price",
                "max_final_price",
                "p05_final_price",
                "p95_final_price",
                "mean_total_return",
                "median_total_return",
                "p05_total_return",
                "p95_total_return",
            ],
            "value": [
                len(path_columns),
                len(paths) - 1,
                float(starting_prices.iloc[0]),
                float(final_prices.mean()),
                float(final_prices.median()),
                float(final_prices.std()),
                float(final_prices.min()),
                float(final_prices.max()),
                float(final_prices.quantile(0.05)),
                float(final_prices.quantile(0.95)),
                float(total_returns.mean()),
                float(total_returns.median()),
                float(total_returns.quantile(0.05)),
                float(total_returns.quantile(0.95)),
            ],
        }
    )

    return summary


def paths_to_long_format(paths: pd.DataFrame) -> pd.DataFrame:
    """Convert wide simulated paths into long format."""
    path_columns = [column for column in paths.columns if column.startswith("path_")]

    long_paths = paths.melt(
        id_vars=["time_years", "step"],
        value_vars=path_columns,
        var_name="path_id",
        value_name="stock_price",
    )

    return long_paths


def plot_sample_paths(
    paths: pd.DataFrame,
    output_path: str | Path,
    max_paths: int = 25,
) -> Path:
    """Save a plot of sample simulated stock paths."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    path_columns = [column for column in paths.columns if column.startswith("path_")]
    selected_columns = path_columns[:max_paths]

    if not selected_columns:
        raise ValueError("No path columns found.")

    plt.figure(figsize=(10, 5))
    for column in selected_columns:
        plt.plot(paths["time_years"], paths[column], linewidth=1)

    plt.xlabel("Time in Years")
    plt.ylabel("Simulated Stock Price")
    plt.title("Sample Simulated Stock Price Paths")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_final_price_distribution(
    paths: pd.DataFrame,
    output_path: str | Path,
    bins: int = 40,
) -> Path:
    """Save a histogram of final simulated stock prices."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    final_prices = final_price_distribution(paths)

    plt.figure(figsize=(9, 5))
    plt.hist(final_prices, bins=bins)
    plt.xlabel("Final Stock Price")
    plt.ylabel("Path Count")
    plt.title("Final Simulated Price Distribution")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def save_simulation_outputs(
    paths: pd.DataFrame,
    output_dir: str | Path = "data/processed",
    file_prefix: str = "gbm",
) -> dict[str, Path]:
    """Save simulated paths, final prices, and summary statistics."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths_path = output_dir / f"{file_prefix}_simulated_paths.csv"
    final_prices_path = output_dir / f"{file_prefix}_final_prices.csv"
    summary_path = output_dir / f"{file_prefix}_simulation_summary.csv"

    paths.to_csv(paths_path, index=False)
    final_price_distribution(paths).rename("final_price").to_csv(final_prices_path, index=False)
    simulation_summary(paths).to_csv(summary_path, index=False)

    return {
        "paths": paths_path,
        "final_prices": final_prices_path,
        "summary": summary_path,
    }


def build_simulation_figures(
    paths: pd.DataFrame,
    output_dir: str | Path = "figures",
) -> dict[str, Path]:
    """Save the standard simulation figures."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    return {
        "simulated_paths": plot_sample_paths(
            paths,
            output_dir / "simulated_paths.png",
        ),
        "final_price_distribution": plot_final_price_distribution(
            paths,
            output_dir / "final_price_distribution.png",
        ),
    }
