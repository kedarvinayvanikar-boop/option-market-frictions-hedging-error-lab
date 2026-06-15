"""
Implied-volatility solvers and batch utilities.

The functions in this module invert Black-Scholes prices into implied
volatility estimates. Solver diagnostics are kept with the output because
failed or unstable solves are part of option quote-quality analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Literal

import pandas as pd

from src.black_scholes import option_price

OptionType = Literal["call", "put"]
PriceSource = Literal["bid", "mid", "ask"]
SolverMethod = Literal["bisection", "brent"]


@dataclass(frozen=True)
class ImpliedVolResult:
    """Container for one implied-volatility solve."""
    implied_volatility: float | None
    solver_status: str
    failure_reason: str | None
    iterations: int
    pricing_error: float | None
    lower_bound: float
    upper_bound: float
    input_price: float


def intrinsic_value(S: float, K: float, option_type: OptionType) -> float:
    """Return option intrinsic value."""
    option_type = option_type.lower()

    if option_type == "call":
        return max(S - K, 0.0)
    if option_type == "put":
        return max(K - S, 0.0)

    raise ValueError("option_type must be 'call' or 'put'.")


def discounted_bound_check(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: OptionType,
) -> str | None:
    """
    Return a basic no-arbitrage failure reason when the price is outside
    simple European option bounds.
    """
    if not all(math.isfinite(x) for x in [market_price, S, K, T, r]):
        return "non-finite input"

    if market_price <= 0:
        return "nonpositive option price"

    if S <= 0 or K <= 0:
        return "nonpositive stock or strike"

    if T < 0:
        return "negative time to maturity"

    option_type = option_type.lower()
    discounted_strike = K * math.exp(-r * max(T, 0.0))

    if option_type == "call":
        lower_bound = max(S - discounted_strike, 0.0)
        upper_bound = S
    elif option_type == "put":
        lower_bound = max(discounted_strike - S, 0.0)
        upper_bound = discounted_strike
    else:
        return "invalid option type"

    tolerance = 1e-10

    if market_price < lower_bound - tolerance:
        return "price below no-arbitrage lower bound"

    if market_price > upper_bound + tolerance:
        return "price above no-arbitrage upper bound"

    return None


def _price_difference(
    sigma: float,
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: OptionType,
) -> float:
    """Return Black-Scholes price minus market price for one volatility."""
    return option_price(S, K, T, r, sigma, option_type) - market_price


def implied_vol_bisection(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: OptionType,
    lower_bound: float = 1e-6,
    upper_bound: float = 5.0,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
) -> ImpliedVolResult:
    """Solve implied volatility with the bisection method."""
    failure_reason = discounted_bound_check(market_price, S, K, T, r, option_type)
    if failure_reason is not None:
        return ImpliedVolResult(
            implied_volatility=None,
            solver_status="failed",
            failure_reason=failure_reason,
            iterations=0,
            pricing_error=None,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    if T == 0:
        return ImpliedVolResult(
            implied_volatility=None,
            solver_status="failed",
            failure_reason="expired option has no implied volatility",
            iterations=0,
            pricing_error=None,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    low = lower_bound
    high = upper_bound

    low_error = _price_difference(low, market_price, S, K, T, r, option_type)
    high_error = _price_difference(high, market_price, S, K, T, r, option_type)

    if abs(low_error) <= tolerance:
        return ImpliedVolResult(
            implied_volatility=low,
            solver_status="success",
            failure_reason=None,
            iterations=0,
            pricing_error=low_error,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    if abs(high_error) <= tolerance:
        return ImpliedVolResult(
            implied_volatility=high,
            solver_status="success",
            failure_reason=None,
            iterations=0,
            pricing_error=high_error,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    if low_error * high_error > 0:
        return ImpliedVolResult(
            implied_volatility=None,
            solver_status="failed",
            failure_reason="root not bracketed",
            iterations=0,
            pricing_error=None,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    mid = math.nan
    mid_error = math.nan

    for iteration in range(1, max_iterations + 1):
        mid = 0.5 * (low + high)
        mid_error = _price_difference(mid, market_price, S, K, T, r, option_type)

        if abs(mid_error) <= tolerance or 0.5 * (high - low) <= tolerance:
            return ImpliedVolResult(
                implied_volatility=mid,
                solver_status="success",
                failure_reason=None,
                iterations=iteration,
                pricing_error=mid_error,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                input_price=market_price,
            )

        if low_error * mid_error <= 0:
            high = mid
            high_error = mid_error
        else:
            low = mid
            low_error = mid_error

    return ImpliedVolResult(
        implied_volatility=mid,
        solver_status="failed",
        failure_reason="maximum iterations reached",
        iterations=max_iterations,
        pricing_error=mid_error,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        input_price=market_price,
    )


def implied_vol_brent(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: OptionType,
    lower_bound: float = 1e-6,
    upper_bound: float = 5.0,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
) -> ImpliedVolResult:
    """Solve implied volatility with Brent's method when scipy is available."""
    try:
        from scipy.optimize import brentq
    except ImportError:
        return implied_vol_bisection(
            market_price=market_price,
            S=S,
            K=K,
            T=T,
            r=r,
            option_type=option_type,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            tolerance=tolerance,
            max_iterations=max_iterations,
        )

    failure_reason = discounted_bound_check(market_price, S, K, T, r, option_type)
    if failure_reason is not None:
        return ImpliedVolResult(
            implied_volatility=None,
            solver_status="failed",
            failure_reason=failure_reason,
            iterations=0,
            pricing_error=None,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    if T == 0:
        return ImpliedVolResult(
            implied_volatility=None,
            solver_status="failed",
            failure_reason="expired option has no implied volatility",
            iterations=0,
            pricing_error=None,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    low_error = _price_difference(lower_bound, market_price, S, K, T, r, option_type)
    high_error = _price_difference(upper_bound, market_price, S, K, T, r, option_type)

    if low_error * high_error > 0:
        return ImpliedVolResult(
            implied_volatility=None,
            solver_status="failed",
            failure_reason="root not bracketed",
            iterations=0,
            pricing_error=None,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    try:
        root, result = brentq(
            lambda sigma: _price_difference(
                sigma, market_price, S, K, T, r, option_type
            ),
            lower_bound,
            upper_bound,
            xtol=tolerance,
            maxiter=max_iterations,
            full_output=True,
        )
    except ValueError as exc:
        return ImpliedVolResult(
            implied_volatility=None,
            solver_status="failed",
            failure_reason=str(exc),
            iterations=0,
            pricing_error=None,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            input_price=market_price,
        )

    pricing_error = _price_difference(root, market_price, S, K, T, r, option_type)

    return ImpliedVolResult(
        implied_volatility=root,
        solver_status="success" if result.converged else "failed",
        failure_reason=None if result.converged else "brent did not converge",
        iterations=result.iterations,
        pricing_error=pricing_error,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        input_price=market_price,
    )


def solve_implied_volatility(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: OptionType,
    method: SolverMethod = "bisection",
    lower_bound: float = 1e-6,
    upper_bound: float = 5.0,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
) -> ImpliedVolResult:
    """Solve implied volatility from a market option price."""
    if method == "bisection":
        return implied_vol_bisection(
            market_price,
            S,
            K,
            T,
            r,
            option_type,
            lower_bound,
            upper_bound,
            tolerance,
            max_iterations,
        )

    if method == "brent":
        return implied_vol_brent(
            market_price,
            S,
            K,
            T,
            r,
            option_type,
            lower_bound,
            upper_bound,
            tolerance,
            max_iterations,
        )

    raise ValueError("method must be 'bisection' or 'brent'.")


def solve_quote_iv_row(
    row: pd.Series,
    price_source: PriceSource,
    risk_free_rate: float,
    method: SolverMethod = "bisection",
    lower_bound: float = 1e-6,
    upper_bound: float = 5.0,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
) -> dict:
    """Solve IV for one quote row and one price source."""
    price_column = {
        "bid": "bid",
        "mid": "mid_price",
        "ask": "ask",
    }[price_source]

    result = solve_implied_volatility(
        market_price=float(row[price_column]),
        S=float(row["underlying_price"]),
        K=float(row["strike"]),
        T=float(row["time_to_maturity"]),
        r=float(risk_free_rate),
        option_type=str(row["option_type"]),
        method=method,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        tolerance=tolerance,
        max_iterations=max_iterations,
    )

    return {
        "contractSymbol": row.get("contractSymbol", row.get("contract_symbol")),
        "price_source": price_source,
        "input_price": result.input_price,
        "implied_volatility": result.implied_volatility,
        "solver_status": result.solver_status,
        "failure_reason": result.failure_reason,
        "solver_iterations": result.iterations,
        "solver_lower_bound": result.lower_bound,
        "solver_upper_bound": result.upper_bound,
        "pricing_error": result.pricing_error,
    }


def calculate_iv_results(
    clean_quotes: pd.DataFrame,
    risk_free_rate: float,
    method: SolverMethod = "bisection",
    lower_bound: float = 1e-6,
    upper_bound: float = 5.0,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
    retained_only: bool = True,
) -> pd.DataFrame:
    """
    Calculate bid, mid, and ask implied-volatility results in long format.

    Long format stores one row per contract and price source.
    """
    required_columns = {
        "strike",
        "option_type",
        "underlying_price",
        "time_to_maturity",
        "bid",
        "mid_price",
        "ask",
    }
    missing_columns = required_columns.difference(clean_quotes.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    frame = clean_quotes.copy()

    if retained_only and "is_excluded" in frame.columns:
        frame = frame.loc[~frame["is_excluded"]].copy()

    records = []
    for _, row in frame.iterrows():
        for price_source in ["bid", "mid", "ask"]:
            records.append(
                solve_quote_iv_row(
                    row=row,
                    price_source=price_source,
                    risk_free_rate=risk_free_rate,
                    method=method,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                    tolerance=tolerance,
                    max_iterations=max_iterations,
                )
            )

    return pd.DataFrame(records)


def build_iv_wide_table(clean_quotes: pd.DataFrame, iv_results: pd.DataFrame) -> pd.DataFrame:
    """Attach IV bid, mid, and ask columns to the cleaned quote dataset."""
    contract_column = "contractSymbol" if "contractSymbol" in clean_quotes.columns else "contract_symbol"

    iv_wide = iv_results.pivot_table(
        index="contractSymbol",
        columns="price_source",
        values="implied_volatility",
        aggfunc="first",
    ).reset_index()

    iv_wide = iv_wide.rename(
        columns={
            "bid": "IV_bid",
            "mid": "IV_mid",
            "ask": "IV_ask",
        }
    )

    merged = clean_quotes.merge(
        iv_wide,
        left_on=contract_column,
        right_on="contractSymbol",
        how="left",
        suffixes=("", "_iv"),
    )

    if "contractSymbol_iv" in merged.columns:
        merged = merged.drop(columns=["contractSymbol_iv"])

    return merged


def calculate_iv_uncertainty(iv_wide_quotes: pd.DataFrame) -> pd.DataFrame:
    """Calculate implied-volatility range from bid, mid, and ask IV."""
    frame = iv_wide_quotes.copy()

    frame["IV_range"] = frame["IV_ask"] - frame["IV_bid"]
    frame["IV_relative_range"] = frame["IV_range"] / frame["IV_mid"]

    return frame


def solver_success_summary(iv_results: pd.DataFrame) -> pd.DataFrame:
    """Summarize solver success rates by price source."""
    summary = (
        iv_results.groupby("price_source")
        .agg(
            total_solves=("solver_status", "size"),
            successful_solves=("solver_status", lambda x: (x == "success").sum()),
            failed_solves=("solver_status", lambda x: (x != "success").sum()),
        )
        .reset_index()
    )

    summary["success_rate"] = summary["successful_solves"] / summary["total_solves"]

    return summary


def solver_failure_summary(iv_results: pd.DataFrame) -> pd.DataFrame:
    """Return counts by solver failure reason."""
    failures = iv_results.loc[iv_results["solver_status"] != "success"].copy()

    if failures.empty:
        return pd.DataFrame(
            columns=["price_source", "failure_reason", "failure_count"]
        )

    return (
        failures.groupby(["price_source", "failure_reason"], dropna=False)
        .size()
        .reset_index(name="failure_count")
        .sort_values(["failure_count", "price_source"], ascending=[False, True])
    )


def vendor_iv_comparison(iv_wide_quotes: pd.DataFrame) -> pd.DataFrame:
    """Compare calculated mid IV against the vendor implied-volatility field."""
    if "impliedVolatility" not in iv_wide_quotes.columns:
        return pd.DataFrame()

    comparison = iv_wide_quotes.dropna(subset=["IV_mid", "impliedVolatility"]).copy()

    if comparison.empty:
        return pd.DataFrame()

    comparison["vendor_iv"] = comparison["impliedVolatility"]
    comparison["computed_minus_vendor_iv"] = comparison["IV_mid"] - comparison["vendor_iv"]
    comparison["abs_computed_minus_vendor_iv"] = comparison["computed_minus_vendor_iv"].abs()

    columns = [
        column
        for column in [
            "contractSymbol",
            "expiration",
            "option_type",
            "strike",
            "IV_mid",
            "vendor_iv",
            "computed_minus_vendor_iv",
            "abs_computed_minus_vendor_iv",
        ]
        if column in comparison.columns
    ]

    return comparison[columns]


def plot_solver_failure_heatmap(
    clean_quotes: pd.DataFrame,
    iv_results: pd.DataFrame,
    output_path: str,
    moneyness_bins: int = 8,
) -> str:
    """
    Save a heatmap showing solver failure rate by expiry and log-moneyness bin.
    """
    import matplotlib.pyplot as plt

    contract_column = "contractSymbol" if "contractSymbol" in clean_quotes.columns else "contract_symbol"

    quote_fields = clean_quotes[
        [contract_column, "expiration", "log_moneyness"]
    ].rename(columns={contract_column: "contractSymbol"})

    merged = iv_results.merge(quote_fields, on="contractSymbol", how="left")
    merged = merged.dropna(subset=["expiration", "log_moneyness"]).copy()

    if merged.empty:
        raise ValueError("No rows available for solver failure heatmap.")

    merged["log_moneyness_bin"] = pd.cut(
        merged["log_moneyness"],
        bins=moneyness_bins,
    ).astype(str)

    merged["is_failure"] = merged["solver_status"] != "success"

    heatmap = (
        merged.groupby(["expiration", "log_moneyness_bin"], observed=True)["is_failure"]
        .mean()
        .unstack(fill_value=0.0)
    )

    output_path = str(output_path)
    Path = __import__("pathlib").Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10, 5))
    image = plt.imshow(heatmap.values, aspect="auto")
    plt.colorbar(image, label="Solver Failure Rate")
    plt.xticks(range(len(heatmap.columns)), heatmap.columns, rotation=45, ha="right")
    plt.yticks(range(len(heatmap.index)), heatmap.index)
    plt.xlabel("Log-Moneyness Bin")
    plt.ylabel("Expiration")
    plt.title("Implied Volatility Solver Failure Rate")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path
