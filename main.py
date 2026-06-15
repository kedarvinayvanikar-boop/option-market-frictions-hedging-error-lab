"""
End-to-end pipeline for the option market frictions and hedging error lab.

Running this script regenerates every processed table, the SQLite database,
and every figure under data/ and figures/ from the raw option-chain snapshot
in data/raw/. Each stage mirrors the corresponding analysis notebook so the
notebooks and this script stay consistent with each other.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import (
    COMPILED_DIR,
    DATA_DIR,
    DATABASE_DIR,
    FIGURES_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    ensure_project_directories,
)

RISK_FREE_RATE = 0.04
UNDERLYING_PRICE = 600.0
TICKER = "SPY"
SNAPSHOT_TIME_UTC = "2026-06-14T16:00:00+00:00"


def stage_clean_quotes() -> pd.DataFrame:
    """Clean the raw option-chain snapshot and save quote-quality figures."""
    from src.cleaning import clean_option_chain, save_cleaned_option_chain
    from src.quote_quality import (
        data_quality_summary,
        exclusion_reason_summary,
        plot_data_cleaning_summary,
        plot_spread_by_expiry,
        plot_spread_by_moneyness,
    )

    raw_options = pd.read_csv(RAW_DATA_DIR / "sample_option_chain_snapshot.csv")

    cleaned = clean_option_chain(
        raw_options,
        underlying_price=UNDERLYING_PRICE,
        max_spread_pct=0.40,
        min_volume=1,
        min_open_interest=1,
    )

    save_cleaned_option_chain(cleaned, output_dir=PROCESSED_DATA_DIR, file_name="cleaned_option_chain.csv")
    data_quality_summary(cleaned).to_csv(PROCESSED_DATA_DIR / "data_quality_summary.csv", index=False)
    exclusion_reason_summary(cleaned).to_csv(PROCESSED_DATA_DIR / "exclusion_reason_summary.csv", index=False)

    plot_data_cleaning_summary(cleaned, FIGURES_DIR / "data_cleaning_summary.png")
    plot_spread_by_moneyness(cleaned, FIGURES_DIR / "bid_ask_spread_by_moneyness.png")
    plot_spread_by_expiry(cleaned, FIGURES_DIR / "bid_ask_spread_by_expiry.png")

    print(f"[1/10] Cleaned option chain: {len(cleaned)} contracts, "
          f"{int(cleaned['is_excluded'].sum())} excluded")
    return cleaned


def stage_build_database() -> tuple[Path, int]:
    """Create the SQLite database and load the raw and cleaned snapshots."""
    from src.database import populate_database_from_csv, table_counts

    db_path = DATABASE_DIR / "options_frictions_lab.db"
    db_path.unlink(missing_ok=True)

    summary = populate_database_from_csv(
        db_path=db_path,
        schema_path="sql/schema.sql",
        raw_csv_path=RAW_DATA_DIR / "sample_option_chain_snapshot.csv",
        clean_csv_path=PROCESSED_DATA_DIR / "cleaned_option_chain.csv",
        ticker=TICKER,
        snapshot_time_utc=SNAPSHOT_TIME_UTC,
        source="sample",
    )

    counts = table_counts(db_path)
    counts.to_csv(PROCESSED_DATA_DIR / "database_row_counts.csv", index=False)

    print(f"[2/10] Database populated: snapshot {summary['snapshot_id']}, "
          f"{summary['clean_quote_count']} clean quotes")
    return db_path, summary["snapshot_id"]


def stage_implied_volatility(cleaned: pd.DataFrame, db_path: Path, snapshot_id: int) -> pd.DataFrame:
    """Solve bid, mid, and ask implied volatility for every retained contract."""
    from src.database import insert_iv_results_to_database
    from src.implied_vol import (
        build_iv_wide_table,
        calculate_iv_results,
        calculate_iv_uncertainty,
        plot_solver_failure_heatmap,
        solver_failure_summary,
        solver_success_summary,
        vendor_iv_comparison,
    )

    iv_results = calculate_iv_results(
        cleaned,
        risk_free_rate=RISK_FREE_RATE,
        method="bisection",
        retained_only=True,
    )
    iv_results.to_csv(PROCESSED_DATA_DIR / "iv_results.csv", index=False)

    solver_success_summary(iv_results).to_csv(PROCESSED_DATA_DIR / "iv_solver_success_summary.csv", index=False)
    solver_failure_summary(iv_results).to_csv(PROCESSED_DATA_DIR / "iv_failure_summary.csv", index=False)

    iv_wide = build_iv_wide_table(cleaned, iv_results)
    iv_wide = calculate_iv_uncertainty(iv_wide)
    iv_wide.to_csv(PROCESSED_DATA_DIR / "iv_uncertainty_results.csv", index=False)

    vendor_comparison = vendor_iv_comparison(iv_wide)
    if not vendor_comparison.empty:
        vendor_comparison.to_csv(PROCESSED_DATA_DIR / "computed_vs_vendor_iv.csv", index=False)

    plot_solver_failure_heatmap(
        cleaned,
        iv_results,
        FIGURES_DIR / "solver_failure_heatmap.png",
        moneyness_bins=8,
    )

    insert_iv_results_to_database(db_path, iv_results, iv_wide, snapshot_id)

    success_rate = (iv_results["solver_status"] == "success").mean()
    print(f"[3/10] Implied volatility solved: {len(iv_results)} solves, "
          f"{success_rate:.1%} success rate")
    return iv_wide


def stage_iv_uncertainty(iv_wide: pd.DataFrame) -> pd.DataFrame:
    """Bucket IV uncertainty by moneyness, expiry, and liquidity."""
    from src.iv_uncertainty import (
        iv_uncertainty_by_expiry,
        iv_uncertainty_by_liquidity,
        iv_uncertainty_by_moneyness,
        iv_uncertainty_summary,
        plot_iv_bid_mid_ask_smile,
        plot_iv_uncertainty_by_expiry,
        plot_iv_uncertainty_by_moneyness,
        plot_iv_uncertainty_heatmap,
        prepare_iv_uncertainty_dataset,
    )

    iv_analysis = prepare_iv_uncertainty_dataset(iv_wide)
    iv_analysis.to_csv(PROCESSED_DATA_DIR / "iv_uncertainty_analysis.csv", index=False)

    iv_uncertainty_summary(iv_analysis).to_csv(PROCESSED_DATA_DIR / "iv_uncertainty_summary.csv", index=False)
    iv_uncertainty_by_expiry(iv_analysis).to_csv(PROCESSED_DATA_DIR / "iv_uncertainty_by_expiry.csv", index=False)
    iv_uncertainty_by_moneyness(iv_analysis).to_csv(PROCESSED_DATA_DIR / "iv_uncertainty_by_moneyness.csv", index=False)
    iv_uncertainty_by_liquidity(iv_analysis).to_csv(PROCESSED_DATA_DIR / "iv_uncertainty_by_liquidity.csv", index=False)

    plot_iv_bid_mid_ask_smile(iv_analysis, FIGURES_DIR / "iv_bid_mid_ask_smile.png")
    plot_iv_uncertainty_heatmap(iv_analysis, FIGURES_DIR / "iv_uncertainty_heatmap.png")
    plot_iv_uncertainty_by_expiry(iv_analysis, FIGURES_DIR / "iv_uncertainty_by_expiry.png")
    plot_iv_uncertainty_by_moneyness(iv_analysis, FIGURES_DIR / "iv_uncertainty_by_moneyness.png")

    median_relative_range = iv_analysis["IV_relative_range"].median()
    print(f"[4/10] IV uncertainty analyzed: median IV_relative_range = {median_relative_range:.2%}")
    return iv_analysis


def stage_surface(iv_analysis: pd.DataFrame) -> None:
    """Build raw and cleaned volatility surfaces and reliability diagnostics."""
    from src.surface import (
        build_surface_grid,
        clean_vs_unclean_surface_comparison,
        prepare_surface_dataset,
        smile_residuals,
        surface_reliability_diagnostics,
    )
    from src.plotting import (
        plot_clean_vs_unclean_surface,
        plot_iv_bid_mid_ask_smile,
        plot_iv_mid_smiles,
        plot_surface_residuals,
        plot_volatility_surface_reliability,
    )

    surface_data = prepare_surface_dataset(iv_analysis)

    build_surface_grid(surface_data, retained_only=False).to_csv(PROCESSED_DATA_DIR / "raw_surface_grid.csv", index=False)
    build_surface_grid(surface_data, retained_only=True).to_csv(PROCESSED_DATA_DIR / "clean_surface_grid.csv", index=False)

    clean_vs_unclean_surface_comparison(surface_data).to_csv(
        PROCESSED_DATA_DIR / "clean_vs_unclean_surface_comparison.csv", index=False
    )

    diagnostics = surface_reliability_diagnostics(surface_data)
    diagnostics.to_csv(PROCESSED_DATA_DIR / "surface_diagnostics.csv", index=False)

    smile_residuals(surface_data).to_csv(PROCESSED_DATA_DIR / "surface_residuals.csv", index=False)

    plot_iv_mid_smiles(surface_data, FIGURES_DIR / "iv_mid_smiles_by_expiry.png")
    plot_iv_bid_mid_ask_smile(surface_data, FIGURES_DIR / "iv_bid_mid_ask_smile.png")
    plot_clean_vs_unclean_surface(surface_data, FIGURES_DIR / "clean_vs_unclean_surface.png")
    plot_volatility_surface_reliability(surface_data, FIGURES_DIR / "volatility_surface_reliability.png")
    plot_surface_residuals(surface_data, FIGURES_DIR / "surface_residuals.png")

    mean_reliability = diagnostics["reliability_score"].mean()
    print(f"[5/10] Surface diagnostics built: mean reliability score = {mean_reliability:.2f}")


def stage_greeks(iv_analysis: pd.DataFrame, db_path: Path, snapshot_id: int) -> pd.DataFrame:
    """Calculate Greeks and Greek uncertainty from bid, mid, and ask IV."""
    from src.greek_uncertainty import (
        greek_uncertainty_summary,
        insert_greek_results_to_database,
        plot_all_greek_uncertainty_heatmaps,
        prepare_greek_uncertainty_dataset,
    )

    greek_results, greek_wide = prepare_greek_uncertainty_dataset(
        iv_analysis,
        risk_free_rate=RISK_FREE_RATE,
        retained_only=True,
    )

    greek_results.to_csv(PROCESSED_DATA_DIR / "greek_results.csv", index=False)
    greek_wide.to_csv(PROCESSED_DATA_DIR / "greek_uncertainty_results.csv", index=False)
    greek_uncertainty_summary(greek_wide).to_csv(PROCESSED_DATA_DIR / "greek_uncertainty_summary.csv", index=False)

    plot_all_greek_uncertainty_heatmaps(greek_wide, output_dir=FIGURES_DIR)

    insert_greek_results_to_database(db_path, greek_results, greek_wide, snapshot_id)

    print(f"[6/10] Greeks calculated for {greek_wide['contractSymbol'].nunique()} contracts "
          f"across bid, mid, and ask IV")
    return greek_wide


def stage_short_expiry_risk(greek_wide: pd.DataFrame) -> None:
    """Summarize Gamma, Theta, Vega, and IV uncertainty by days to expiry."""
    from src.short_expiry_risk import (
        build_short_expiry_dashboard_outputs,
        prepare_short_expiry_dataset,
        short_expiry_risk_score,
        short_expiry_risk_summary,
    )

    short_expiry_data = prepare_short_expiry_dataset(greek_wide, max_days=60, retained_only=True)
    short_expiry_data = short_expiry_risk_score(short_expiry_data)

    short_expiry_risk_summary(short_expiry_data).to_csv(PROCESSED_DATA_DIR / "short_expiry_risk_summary.csv", index=False)
    short_expiry_data.to_csv(PROCESSED_DATA_DIR / "short_expiry_risk_dataset.csv", index=False)

    build_short_expiry_dashboard_outputs(short_expiry_data, output_dir=FIGURES_DIR)

    print(f"[7/10] Short-expiry risk dashboard built for {len(short_expiry_data)} contracts under 60 DTE")


def stage_price_paths() -> pd.DataFrame:
    """Simulate geometric Brownian motion price paths for the hedging study."""
    from src.simulation import build_simulation_figures, save_simulation_outputs, simulate_gbm_paths

    paths = simulate_gbm_paths(
        starting_price=100.0,
        drift=0.06,
        volatility=0.25,
        time_horizon=30 / 365.25,
        steps=30,
        num_paths=2_000,
        random_seed=42,
    )

    save_simulation_outputs(paths, output_dir=PROCESSED_DATA_DIR, file_prefix="gbm")
    build_simulation_figures(paths, output_dir=FIGURES_DIR)

    print(f"[8/10] Simulated {paths.shape[1] - 2} GBM price paths over {paths.shape[0] - 1} steps")
    return paths


def stage_delta_hedging() -> tuple[pd.DataFrame, "HedgeContract"]:
    """Run a discrete delta-hedging simulation for one at-the-money call."""
    from src.hedging import HedgeContract, build_hedging_figures, hedging_error_summary, save_hedging_outputs, simulate_delta_hedge_many_paths
    from src.simulation import simulate_gbm_paths

    risk_free_rate = RISK_FREE_RATE
    maturity_years = 30 / 365.25

    paths = simulate_gbm_paths(
        starting_price=100.0,
        drift=risk_free_rate,
        volatility=0.25,
        time_horizon=maturity_years,
        steps=30,
        num_paths=5_000,
        random_seed=42,
    )

    contract = HedgeContract(
        option_type="call",
        strike=100.0,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        volatility=0.25,
        position=1,
    )

    hedge_results, _ = simulate_delta_hedge_many_paths(
        paths=paths,
        contract=contract,
        transaction_cost_bps=5.0,
        hedge_mode="fixed",
        rebalance_interval=1,
        store_path_details=False,
    )

    summary = hedging_error_summary(hedge_results)
    save_hedging_outputs(hedge_results, summary, output_dir=PROCESSED_DATA_DIR)
    build_hedging_figures(hedge_results, output_dir=FIGURES_DIR)

    mean_error = summary.loc[summary["metric"] == "mean_hedging_error", "value"].iloc[0]
    print(f"[9/10] Delta-hedging simulation: {len(hedge_results)} paths, "
          f"mean hedging error = {mean_error:.4f}")
    return hedge_results, contract


def stage_scenarios(contract) -> None:
    """Compare hedge frequencies and transaction-cost assumptions."""
    from src.scenario_analysis import build_scenario_figures, run_scenario_grid, save_scenario_outputs, summarize_scenarios
    from src.simulation import simulate_gbm_paths

    paths = simulate_gbm_paths(
        starting_price=100.0,
        drift=contract.risk_free_rate,
        volatility=contract.volatility,
        time_horizon=contract.maturity_years,
        steps=30,
        num_paths=3_000,
        random_seed=42,
    )

    scenario_results = run_scenario_grid(
        paths=paths,
        contract=contract,
        transaction_cost_bps_values=[0, 1, 5, 10],
        include_event_trigger=True,
        event_delta_threshold=0.10,
    )

    scenario_summary = summarize_scenarios(scenario_results)
    save_scenario_outputs(scenario_results, scenario_summary, output_dir=PROCESSED_DATA_DIR)
    build_scenario_figures(scenario_summary, output_dir=FIGURES_DIR)

    print(f"[10/10] Scenario grid evaluated: {scenario_summary['scenario_name'].nunique()} scenarios")


def main() -> None:
    ensure_project_directories()

    cleaned = stage_clean_quotes()
    db_path, snapshot_id = stage_build_database()
    iv_wide = stage_implied_volatility(cleaned, db_path, snapshot_id)
    iv_analysis = stage_iv_uncertainty(iv_wide)
    stage_surface(iv_analysis)
    greek_wide = stage_greeks(iv_analysis, db_path, snapshot_id)
    stage_short_expiry_risk(greek_wide)
    stage_price_paths()
    _, contract = stage_delta_hedging()
    stage_scenarios(contract)

    print("\nPipeline complete. Processed tables are in data/processed/, "
          f"the database is at {db_path}, "
          f"and figures are in {FIGURES_DIR}/.")


if __name__ == "__main__":
    main()
