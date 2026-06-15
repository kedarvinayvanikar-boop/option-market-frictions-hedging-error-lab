import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from src.black_scholes import call_price, normal_cdf, normal_pdf, put_price
from src.c_bindings import (
    BlackScholesCLibrary,
    MonteCarloCLibrary,
    add_doubles_c,
    add_doubles_python,
    safe_c_implied_vol_bisection,
    safe_c_simulate_gbm_paths,
)
from src.greeks import calculate_greeks, delta, gamma, theta, vega
from src.implied_vol import solve_implied_volatility
from src.simulation import simulate_gbm_paths


def _bs_library_name() -> str:
    system_name = platform.system().lower()
    if system_name == "darwin":
        return "libbs_pricer.dylib"
    if system_name == "windows":
        return "bs_pricer.dll"
    return "libbs_pricer.so"


def _mc_library_name() -> str:
    system_name = platform.system().lower()
    if system_name == "darwin":
        return "libmonte_carlo.dylib"
    if system_name == "windows":
        return "monte_carlo.dll"
    return "libmonte_carlo.so"


def _compile_library(tmp_path: Path, source_files: list[Path], output_name: str) -> Path:
    compiler = shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        pytest.skip("C compiler not available.")

    output_path = tmp_path / output_name
    system_name = platform.system().lower()

    if system_name == "darwin":
        command = [compiler, "-O3", "-fPIC", "-dynamiclib", *map(str, source_files), "-o", str(output_path)]
    elif system_name == "windows":
        command = [compiler, "-O3", "-shared", *map(str, source_files), "-o", str(output_path)]
    else:
        command = [compiler, "-O3", "-fPIC", "-shared", *map(str, source_files), "-o", str(output_path), "-lm"]

    subprocess.run(command, check=True)
    return output_path


@pytest.fixture(scope="session")
def c_library(tmp_path_factory):
    project_root = Path(__file__).resolve().parents[1]
    source_files = [
        project_root / "c_src" / "normal_math.c",
        project_root / "c_src" / "bs_pricer.c",
        project_root / "c_src" / "iv_solver.c",
        project_root / "c_src" / "greeks_kernel.c",
    ]
    library_path = _compile_library(tmp_path_factory.mktemp("bs_lib"), source_files, _bs_library_name())
    return BlackScholesCLibrary(library_path)


@pytest.fixture(scope="session")
def mc_library(tmp_path_factory):
    project_root = Path(__file__).resolve().parents[1]
    source_files = [project_root / "c_src" / "monte_carlo.c"]
    library_path = _compile_library(tmp_path_factory.mktemp("mc_lib"), source_files, _mc_library_name())
    return MonteCarloCLibrary(library_path)


def test_c_normal_functions_match_python(c_library):
    for x in [-2.0, -0.5, 0.0, 0.5, 2.0]:
        assert c_library.normal_pdf(x) == pytest.approx(normal_pdf(x), abs=1e-12)
        assert c_library.normal_cdf(x) == pytest.approx(normal_cdf(x), abs=1e-12)


def test_c_prices_match_python(c_library):
    cases = [
        (100.0, 100.0, 0.5, 0.04, 0.25),
        (105.0, 100.0, 1.0, 0.03, 0.20),
        (95.0, 100.0, 30 / 365, 0.04, 0.35),
    ]

    for S, K, T, r, sigma in cases:
        assert c_library.call_price(S, K, T, r, sigma) == pytest.approx(
            call_price(S, K, T, r, sigma),
            abs=1e-10,
        )
        assert c_library.put_price(S, K, T, r, sigma) == pytest.approx(
            put_price(S, K, T, r, sigma),
            abs=1e-10,
        )


def test_c_iv_solver_recovers_volatility(c_library):
    S, K, T, r, sigma = 100.0, 100.0, 0.5, 0.04, 0.25

    market_price = call_price(S, K, T, r, sigma)
    result = c_library.implied_vol_bisection(market_price, S, K, T, r, "call")

    assert result.solver_status == "success"
    assert result.implied_volatility == pytest.approx(sigma, abs=1e-6)


def test_c_iv_matches_python_iv(c_library):
    cases = [
        ("call", 100.0, 100.0, 0.5, 0.04, 0.20),
        ("put", 100.0, 100.0, 0.5, 0.04, 0.30),
        ("call", 110.0, 100.0, 1.0, 0.03, 0.22),
        ("put", 95.0, 100.0, 45 / 365, 0.04, 0.35),
    ]

    for option_type, S, K, T, r, sigma in cases:
        market_price = call_price(S, K, T, r, sigma) if option_type == "call" else put_price(S, K, T, r, sigma)

        c_result = c_library.implied_vol_bisection(market_price, S, K, T, r, option_type)
        py_result = solve_implied_volatility(market_price, S, K, T, r, option_type)

        assert c_result.solver_status == "success"
        assert py_result.solver_status == "success"
        assert c_result.implied_volatility == pytest.approx(py_result.implied_volatility, abs=1e-7)


def test_c_iv_failure_flag_for_nonpositive_price(c_library):
    result = c_library.implied_vol_bisection(0.0, 100.0, 100.0, 0.5, 0.04, "call")

    assert result.solver_status == "failed"
    assert result.failure_reason == "nonpositive option price"


def test_safe_c_iv_falls_back_when_library_missing():
    S, K, T, r, sigma = 100.0, 100.0, 0.5, 0.04, 0.25

    market_price = call_price(S, K, T, r, sigma)
    result = safe_c_implied_vol_bisection(
        market_price,
        S,
        K,
        T,
        r,
        "call",
        library_path="missing_library_file.so",
    )

    assert result.used_fallback is True
    assert result.solver_status == "success"
    assert result.implied_volatility == pytest.approx(sigma, abs=1e-6)


def test_c_delta_matches_python(c_library):
    cases = [
        ("call", 100.0, 100.0, 0.5, 0.04, 0.25),
        ("put", 100.0, 100.0, 0.5, 0.04, 0.25),
        ("call", 110.0, 100.0, 1.0, 0.03, 0.22),
        ("put", 95.0, 100.0, 45 / 365, 0.04, 0.35),
    ]

    for option_type, S, K, T, r, sigma in cases:
        assert c_library.delta(S, K, T, r, sigma, option_type) == pytest.approx(
            delta(S, K, T, r, sigma, option_type),
            abs=1e-10,
        )


def test_c_gamma_matches_python(c_library):
    cases = [
        (100.0, 100.0, 0.5, 0.04, 0.25),
        (110.0, 100.0, 1.0, 0.03, 0.22),
        (95.0, 100.0, 45 / 365, 0.04, 0.35),
    ]

    for S, K, T, r, sigma in cases:
        assert c_library.gamma(S, K, T, r, sigma) == pytest.approx(
            gamma(S, K, T, r, sigma),
            abs=1e-10,
        )


def test_c_vega_and_theta_match_python(c_library):
    cases = [
        ("call", 100.0, 100.0, 0.5, 0.04, 0.25),
        ("put", 100.0, 100.0, 0.5, 0.04, 0.25),
        ("call", 110.0, 100.0, 1.0, 0.03, 0.22),
        ("put", 95.0, 100.0, 45 / 365, 0.04, 0.35),
    ]

    for option_type, S, K, T, r, sigma in cases:
        assert c_library.vega(S, K, T, r, sigma) == pytest.approx(vega(S, K, T, r, sigma), abs=1e-10)
        assert c_library.theta(S, K, T, r, sigma, option_type) == pytest.approx(
            theta(S, K, T, r, sigma, option_type),
            abs=1e-10,
        )


def test_c_greeks_struct_matches_python(c_library):
    option_type, S, K, T, r, sigma = "call", 100.0, 100.0, 0.5, 0.04, 0.25

    c_values = c_library.greeks(S, K, T, r, sigma, option_type)
    py_values = calculate_greeks(S, K, T, r, sigma, option_type)

    assert c_values.status == "success"
    assert c_values.delta == pytest.approx(py_values.delta, abs=1e-10)
    assert c_values.gamma == pytest.approx(py_values.gamma, abs=1e-10)
    assert c_values.vega == pytest.approx(py_values.vega, abs=1e-10)
    assert c_values.theta == pytest.approx(py_values.theta, abs=1e-10)
    assert c_values.rho == pytest.approx(py_values.rho, abs=1e-10)


def test_c_greeks_reject_invalid_inputs(c_library):
    result = c_library.greeks(100.0, 100.0, 0.0, 0.04, 0.25, "call")

    assert result.status == "failed"
    assert result.failure_reason == "invalid input"


def test_c_monte_carlo_distribution_matches_python(mc_library):
    params = dict(
        starting_price=100.0,
        drift=0.04,
        volatility=0.25,
        time_horizon=0.5,
        steps=50,
        num_paths=2000,
    )

    c_result = mc_library.simulate_gbm_paths(random_seed=42, **params)
    python_paths = simulate_gbm_paths(random_seed=123, **params)

    assert c_result.status == "success"

    path_columns = [c for c in c_result.paths.columns if c.startswith("path_")]
    c_final = c_result.paths[path_columns].iloc[-1]
    py_final = python_paths[path_columns].iloc[-1]

    # Different random number generators mean paths will not match exactly,
    # so the comparison is between distribution means rather than individual draws.
    assert c_final.mean() == pytest.approx(py_final.mean(), rel=0.05)


def test_safe_c_simulate_gbm_paths_falls_back_when_library_missing():
    result = safe_c_simulate_gbm_paths(
        starting_price=100.0,
        drift=0.04,
        volatility=0.25,
        time_horizon=0.5,
        steps=10,
        num_paths=50,
        random_seed=42,
        library_path="missing_library_file.so",
    )

    assert result.used_fallback is True
    assert result.status == "success"
    assert not result.paths.empty


def test_add_doubles_c_matches_python():
    try:
        c_result = add_doubles_c(2.5, 4.25)
    except FileNotFoundError:
        pytest.skip("compiled/libexample_add.so not built; see c_src/build_instructions.md")

    assert c_result == add_doubles_python(2.5, 4.25)
