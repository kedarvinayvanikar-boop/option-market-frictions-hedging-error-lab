"""
Hedge-frequency and transaction-cost scenario analysis.

This module compares no hedge, fixed-frequency hedges, and an optional
event-triggered hedge across transaction-cost assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.hedging import HedgeContract, simulate_delta_hedge_many_paths


@dataclass(frozen=True)
class HedgeScenario:
    """One hedge-frequency and cost scenario."""
    scenario_name: str
    hedge_frequency: str
    hedge_mode: str
    rebalance_interval: int | None
    transaction_cost_bps: float
    event_delta_threshold: float | None = None


def build_default_scenarios(
    transaction_cost_bps_values: list[float] | tuple[float, ...] = (0.0, 1.0, 5.0, 10.0),
    include_event_trigger: bool = True,
    event_delta_threshold: float = 0.10,
) -> list[HedgeScenario]:
    """Build the default scenario grid."""
    frequency_specs = [
        ("no_hedge", "no hedge", "none", None),
        ("weekly", "weekly", "fixed", 5),
        ("every_2_days", "every 2 days", "fixed", 2),
        ("daily", "daily", "fixed", 1),
    ]

    if include_event_trigger:
        frequency_specs.append(("event_triggered", "event triggered", "event", None))

    scenarios = []

    for cost_bps in transaction_cost_bps_values:
        for name, frequency, mode, interval in frequency_specs:
            threshold = event_delta_threshold if mode == "event" else None
            scenarios.append(
                HedgeScenario(
                    scenario_name=f"{name}_{cost_bps:g}bps",
                    hedge_frequency=frequency,
                    hedge_mode=mode,
                    rebalance_interval=interval,
                    transaction_cost_bps=float(cost_bps),
                    event_delta_threshold=threshold,
                )
            )

    return scenarios


def run_hedge_scenario(
    paths: pd.DataFrame,
    contract: HedgeContract,
    scenario: HedgeScenario,
) -> pd.DataFrame:
    """Run one hedge scenario and return path-level results."""
    results, _ = simulate_delta_hedge_many_paths(
        paths=paths,
        contract=contract,
        transaction_cost_bps=scenario.transaction_cost_bps,
        hedge_mode=scenario.hedge_mode,
        rebalance_interval=scenario.rebalance_interval,
        event_delta_threshold=scenario.event_delta_threshold,
        store_path_details=False,
    )

    results.insert(0, "scenario_name", scenario.scenario_name)
    results.insert(1, "hedge_frequency", scenario.hedge_frequency)
    results.insert(2, "transaction_cost_bps", scenario.transaction_cost_bps)
    results.insert(3, "hedge_mode", scenario.hedge_mode)
    results.insert(4, "rebalance_interval", scenario.rebalance_interval)
    results.insert(5, "event_delta_threshold", scenario.event_delta_threshold)

    return results


def run_scenario_grid(
    paths: pd.DataFrame,
    contract: HedgeContract,
    transaction_cost_bps_values: list[float] | tuple[float, ...] = (0.0, 1.0, 5.0, 10.0),
    include_event_trigger: bool = True,
    event_delta_threshold: float = 0.10,
) -> pd.DataFrame:
    """Run the full hedge-frequency and transaction-cost scenario grid."""
    scenarios = build_default_scenarios(
        transaction_cost_bps_values=transaction_cost_bps_values,
        include_event_trigger=include_event_trigger,
        event_delta_threshold=event_delta_threshold,
    )

    scenario_results = [
        run_hedge_scenario(paths, contract, scenario)
        for scenario in scenarios
    ]

    return pd.concat(scenario_results, ignore_index=True)


def summarize_scenarios(scenario_results: pd.DataFrame) -> pd.DataFrame:
    """Summarize hedging error and transaction costs by scenario."""
    required = {
        "scenario_name",
        "hedge_frequency",
        "transaction_cost_bps",
        "hedging_error",
        "cumulative_transaction_cost",
        "rebalance_count",
    }
    missing = required.difference(scenario_results.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    summary = (
        scenario_results.groupby(
            ["scenario_name", "hedge_frequency", "transaction_cost_bps", "hedge_mode"],
            observed=True,
        )
        .agg(
            path_count=("path_id", "size"),
            mean_error=("hedging_error", "mean"),
            std_error=("hedging_error", "std"),
            p05_error=("hedging_error", lambda x: x.quantile(0.05)),
            p50_error=("hedging_error", lambda x: x.quantile(0.50)),
            p95_error=("hedging_error", lambda x: x.quantile(0.95)),
            mean_abs_error=("hedging_error", lambda x: x.abs().mean()),
            average_transaction_cost=("cumulative_transaction_cost", "mean"),
            max_transaction_cost=("cumulative_transaction_cost", "max"),
            average_rebalance_count=("rebalance_count", "mean"),
        )
        .reset_index()
    )

    summary["worst_5_percent_outcome"] = summary["p05_error"]
    summary["risk_cost_score"] = summary["mean_abs_error"] + summary["average_transaction_cost"]

    order = {
        "no hedge": 0,
        "weekly": 1,
        "every 2 days": 2,
        "daily": 3,
        "event triggered": 4,
    }
    summary["frequency_order"] = summary["hedge_frequency"].map(order).fillna(99)
    summary = summary.sort_values(["transaction_cost_bps", "frequency_order"]).drop(columns=["frequency_order"])

    return summary


def _prepare_output_path(output_path: str | Path) -> Path:
    """Create the parent directory for a figure path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def plot_transaction_cost_heatmap(
    scenario_summary: pd.DataFrame,
    output_path: str | Path,
    metric: str = "mean_abs_error",
) -> Path:
    """Save a heatmap by hedge frequency and transaction cost."""
    output_path = _prepare_output_path(output_path)

    heatmap = scenario_summary.pivot_table(
        index="hedge_frequency",
        columns="transaction_cost_bps",
        values=metric,
        aggfunc="mean",
        observed=True,
    )

    frequency_order = ["no hedge", "weekly", "every 2 days", "daily", "event triggered"]
    heatmap = heatmap.reindex([row for row in frequency_order if row in heatmap.index])

    plt.figure(figsize=(8, 5))
    image = plt.imshow(heatmap.values, aspect="auto")
    plt.colorbar(image, label=metric.replace("_", " ").title())
    plt.xticks(range(len(heatmap.columns)), [f"{x:g} bps" for x in heatmap.columns])
    plt.yticks(range(len(heatmap.index)), heatmap.index.astype(str))
    plt.xlabel("Transaction Cost Assumption")
    plt.ylabel("Hedge Frequency")
    plt.title("Transaction Cost and Hedge-Risk Heatmap")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_hedge_frequency_cost_frontier(
    scenario_summary: pd.DataFrame,
    output_path: str | Path,
    risk_metric: str = "std_error",
) -> Path:
    """Save a cost-risk frontier chart."""
    output_path = _prepare_output_path(output_path)

    plt.figure(figsize=(8, 5))

    for frequency, group in scenario_summary.groupby("hedge_frequency", observed=True):
        group = group.sort_values("transaction_cost_bps")
        plt.plot(
            group["average_transaction_cost"],
            group[risk_metric],
            marker="o",
            label=str(frequency),
        )

    plt.xlabel("Average Transaction Cost")
    plt.ylabel(risk_metric.replace("_", " ").title())
    plt.title("Hedge Frequency Cost-Risk Frontier")
    plt.legend(title="Hedge Frequency")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def plot_hedge_frequency_comparison(
    scenario_summary: pd.DataFrame,
    output_path: str | Path,
    metric: str = "std_error",
) -> Path:
    """Save a hedge-frequency comparison chart."""
    output_path = _prepare_output_path(output_path)

    frequency_order = ["no hedge", "weekly", "every 2 days", "daily", "event triggered"]
    plt.figure(figsize=(9, 5))

    for cost_bps, group in scenario_summary.groupby("transaction_cost_bps", observed=True):
        group = group.copy()
        group["frequency_order"] = group["hedge_frequency"].map(
            {name: index for index, name in enumerate(frequency_order)}
        )
        group = group.sort_values("frequency_order")
        plt.plot(
            group["hedge_frequency"],
            group[metric],
            marker="o",
            label=f"{cost_bps:g} bps",
        )

    plt.xlabel("Hedge Frequency")
    plt.ylabel(metric.replace("_", " ").title())
    plt.title("Hedge Frequency Comparison")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Transaction Cost")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def save_scenario_outputs(
    scenario_results: pd.DataFrame,
    scenario_summary: pd.DataFrame,
    output_dir: str | Path = "data/processed",
) -> dict[str, Path]:
    """Save scenario result tables."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results_path = output_dir / "scenario_results.csv"
    summary_path = output_dir / "scenario_summary.csv"

    scenario_results.to_csv(results_path, index=False)
    scenario_summary.to_csv(summary_path, index=False)

    return {
        "scenario_results": results_path,
        "scenario_summary": summary_path,
    }


def build_scenario_figures(
    scenario_summary: pd.DataFrame,
    output_dir: str | Path = "figures",
) -> dict[str, Path]:
    """Save standard scenario-analysis figures."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    return {
        "transaction_cost_heatmap": plot_transaction_cost_heatmap(
            scenario_summary,
            output_dir / "transaction_cost_heatmap.png",
            metric="mean_abs_error",
        ),
        "hedge_frequency_cost_frontier": plot_hedge_frequency_cost_frontier(
            scenario_summary,
            output_dir / "hedge_frequency_cost_frontier.png",
            risk_metric="std_error",
        ),
        "hedge_frequency_comparison": plot_hedge_frequency_comparison(
            scenario_summary,
            output_dir / "hedge_frequency_comparison.png",
            metric="std_error",
        ),
    }
