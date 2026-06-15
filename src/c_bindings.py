"""
ctypes bindings for C numerical kernels.

The C library provides Black-Scholes pricing, implied-volatility, Greek, and
Monte Carlo simulation functions. Python remains responsible for validation,
data handling, and fallback behavior when a shared library is unavailable.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import math
import platform
from pathlib import Path
import timeit

import numpy as np
import pandas as pd

from src.config import shared_library_path
from src.implied_vol import solve_implied_volatility
from src.simulation import simulate_gbm_paths as python_simulate_gbm_paths


class CLibraryNotFoundError(FileNotFoundError):
    """Raised when an expected compiled C shared library is missing."""


def load_example_add_library(library_path: str | Path | None = None) -> ctypes.CDLL:
    """Load the compiled example_add shared library."""
    path = Path(library_path) if library_path is not None else shared_library_path()

    if not path.exists():
        raise CLibraryNotFoundError(
            f"Shared library not found at {path}. "
            "Compile c_src/example_add.c first. See c_src/build_instructions.md."
        )

    library = ctypes.CDLL(str(path))

    library.add_doubles.argtypes = [ctypes.c_double, ctypes.c_double]
    library.add_doubles.restype = ctypes.c_double

    return library


def add_doubles_c(a: float, b: float, library_path: str | Path | None = None) -> float:
    """Add two numbers using the compiled C function."""
    library = load_example_add_library(library_path)
    return float(library.add_doubles(float(a), float(b)))


def add_doubles_python(a: float, b: float) -> float:
    """Pure Python version used as a validation benchmark."""
    return float(a + b)


def validate_example_add(a: float = 2.5, b: float = 4.25) -> dict[str, float | bool]:
    """Compare the C result against the pure Python result."""
    c_result = add_doubles_c(a, b)
    python_result = add_doubles_python(a, b)

    return {
        "a": float(a),
        "b": float(b),
        "c_result": c_result,
        "python_result": python_result,
        "matches": abs(c_result - python_result) < 1e-12,
    }



IV_STATUS_MESSAGES = {
    0: None,
    1: "invalid input",
    2: "nonpositive option price",
    3: "expired option has no implied volatility",
    4: "price below no-arbitrage lower bound",
    5: "price above no-arbitrage upper bound",
    6: "root not bracketed",
    7: "maximum iterations reached",
}

GREEKS_STATUS_MESSAGES = {
    0: None,
    1: "invalid input",
    2: "invalid option type",
}


class CIVResult(ctypes.Structure):
    """ctypes representation of the C IVResult struct."""

    _fields_ = [
        ("implied_volatility", ctypes.c_double),
        ("status_code", ctypes.c_int),
        ("iterations", ctypes.c_int),
        ("pricing_error", ctypes.c_double),
        ("lower_bound", ctypes.c_double),
        ("upper_bound", ctypes.c_double),
        ("input_price", ctypes.c_double),
    ]


class CGreeksResult(ctypes.Structure):
    """ctypes representation of the C GreeksResult struct."""

    _fields_ = [
        ("delta", ctypes.c_double),
        ("gamma", ctypes.c_double),
        ("vega", ctypes.c_double),
        ("theta", ctypes.c_double),
        ("rho", ctypes.c_double),
        ("status_code", ctypes.c_int),
    ]


@dataclass(frozen=True)
class CImpliedVolResult:
    """Python representation of one C implied-volatility result."""

    implied_volatility: float | None
    solver_status: str
    failure_reason: str | None
    status_code: int
    iterations: int
    pricing_error: float | None
    lower_bound: float
    upper_bound: float
    input_price: float
    used_fallback: bool = False


@dataclass(frozen=True)
class CGreeks:
    """Python representation of one C Greeks result."""

    delta: float | None
    gamma: float | None
    vega: float | None
    theta: float | None
    rho: float | None
    status: str
    failure_reason: str | None
    status_code: int


class BlackScholesCLibrary:
    """Load and call the C Black-Scholes numerical library."""

    def __init__(self, library_path: str | Path | None = None) -> None:
        self.library_path = Path(library_path) if library_path is not None else self._default_library_path()
        self.lib = ctypes.CDLL(str(self.library_path))
        self._configure_signatures()

    @staticmethod
    def candidate_library_paths() -> list[Path]:
        """Return likely shared-library locations for the current platform."""
        project_root = Path(__file__).resolve().parents[1]
        compiled_dir = project_root / "compiled"

        system_name = platform.system().lower()
        if system_name == "darwin":
            names = ["libbs_pricer.dylib", "libbs_pricer.so"]
        elif system_name == "windows":
            names = ["bs_pricer.dll", "libbs_pricer.dll"]
        else:
            names = ["libbs_pricer.so"]

        return [compiled_dir / name for name in names]

    @classmethod
    def _default_library_path(cls) -> Path:
        for path in cls.candidate_library_paths():
            if path.exists():
                return path

        candidates = ", ".join(str(path) for path in cls.candidate_library_paths())
        raise FileNotFoundError(f"C library not found. Compile it first. Checked: {candidates}")

    def _configure_signatures(self) -> None:
        double_args = [ctypes.c_double] * 5

        self.lib.normal_pdf.argtypes = [ctypes.c_double]
        self.lib.normal_pdf.restype = ctypes.c_double

        self.lib.normal_cdf.argtypes = [ctypes.c_double]
        self.lib.normal_cdf.restype = ctypes.c_double

        self.lib.bs_d1.argtypes = double_args
        self.lib.bs_d1.restype = ctypes.c_double

        self.lib.bs_d2.argtypes = double_args
        self.lib.bs_d2.restype = ctypes.c_double

        self.lib.bs_call_price.argtypes = double_args
        self.lib.bs_call_price.restype = ctypes.c_double

        self.lib.bs_put_price.argtypes = double_args
        self.lib.bs_put_price.restype = ctypes.c_double

        self.lib.bs_option_price.argtypes = double_args + [ctypes.c_int]
        self.lib.bs_option_price.restype = ctypes.c_double

        self.lib.bs_implied_vol_bisection.argtypes = [
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_int,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_int,
        ]
        self.lib.bs_implied_vol_bisection.restype = CIVResult

        self.lib.bs_delta.argtypes = double_args + [ctypes.c_int]
        self.lib.bs_delta.restype = ctypes.c_double

        self.lib.bs_gamma.argtypes = double_args
        self.lib.bs_gamma.restype = ctypes.c_double

        self.lib.bs_vega.argtypes = double_args
        self.lib.bs_vega.restype = ctypes.c_double

        self.lib.bs_theta.argtypes = double_args + [ctypes.c_int]
        self.lib.bs_theta.restype = ctypes.c_double

        self.lib.bs_rho.argtypes = double_args + [ctypes.c_int]
        self.lib.bs_rho.restype = ctypes.c_double

        self.lib.bs_greeks.argtypes = double_args + [ctypes.c_int]
        self.lib.bs_greeks.restype = CGreeksResult

    @staticmethod
    def _option_type_code(option_type: str) -> int:
        option_type = option_type.lower()

        if option_type == "call":
            return 1
        if option_type == "put":
            return -1

        raise ValueError("option_type must be 'call' or 'put'.")

    @staticmethod
    def _validate_numeric_result(value: float) -> float:
        if math.isnan(value):
            raise ValueError("The C function returned NaN for the supplied inputs.")
        return value

    @staticmethod
    def _convert_iv_result(result: CIVResult, used_fallback: bool = False) -> CImpliedVolResult:
        success = result.status_code == 0
        return CImpliedVolResult(
            implied_volatility=float(result.implied_volatility) if success else None,
            solver_status="success" if success else "failed",
            failure_reason=IV_STATUS_MESSAGES.get(result.status_code, "unknown failure"),
            status_code=int(result.status_code),
            iterations=int(result.iterations),
            pricing_error=float(result.pricing_error) if math.isfinite(result.pricing_error) else None,
            lower_bound=float(result.lower_bound),
            upper_bound=float(result.upper_bound),
            input_price=float(result.input_price),
            used_fallback=used_fallback,
        )

    @staticmethod
    def _convert_greeks_result(result: CGreeksResult) -> CGreeks:
        success = result.status_code == 0

        return CGreeks(
            delta=float(result.delta) if success else None,
            gamma=float(result.gamma) if success else None,
            vega=float(result.vega) if success else None,
            theta=float(result.theta) if success else None,
            rho=float(result.rho) if success else None,
            status="success" if success else "failed",
            failure_reason=GREEKS_STATUS_MESSAGES.get(result.status_code, "unknown failure"),
            status_code=int(result.status_code),
        )

    def normal_pdf(self, x: float) -> float:
        """Return the standard normal density from C."""
        return self.lib.normal_pdf(float(x))

    def normal_cdf(self, x: float) -> float:
        """Return the standard normal cumulative probability from C."""
        return self.lib.normal_cdf(float(x))

    def call_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Return a European call price from C."""
        value = self.lib.bs_call_price(float(S), float(K), float(T), float(r), float(sigma))
        return self._validate_numeric_result(value)

    def put_price(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Return a European put price from C."""
        value = self.lib.bs_put_price(float(S), float(K), float(T), float(r), float(sigma))
        return self._validate_numeric_result(value)

    def implied_vol_bisection(
        self,
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str,
        lower_bound: float = 1e-6,
        upper_bound: float = 5.0,
        tolerance: float = 1e-8,
        max_iterations: int = 100,
    ) -> CImpliedVolResult:
        """Return implied volatility from the C bisection solver."""
        result = self.lib.bs_implied_vol_bisection(
            float(market_price),
            float(S),
            float(K),
            float(T),
            float(r),
            self._option_type_code(option_type),
            float(lower_bound),
            float(upper_bound),
            float(tolerance),
            int(max_iterations),
        )
        return self._convert_iv_result(result)

    def delta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Return Black-Scholes delta from C."""
        value = self.lib.bs_delta(float(S), float(K), float(T), float(r), float(sigma), self._option_type_code(option_type))
        return self._validate_numeric_result(value)

    def gamma(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Return Black-Scholes gamma from C."""
        value = self.lib.bs_gamma(float(S), float(K), float(T), float(r), float(sigma))
        return self._validate_numeric_result(value)

    def vega(self, S: float, K: float, T: float, r: float, sigma: float) -> float:
        """Return Black-Scholes vega from C."""
        value = self.lib.bs_vega(float(S), float(K), float(T), float(r), float(sigma))
        return self._validate_numeric_result(value)

    def theta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Return Black-Scholes theta from C."""
        value = self.lib.bs_theta(float(S), float(K), float(T), float(r), float(sigma), self._option_type_code(option_type))
        return self._validate_numeric_result(value)

    def rho(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Return Black-Scholes rho from C."""
        value = self.lib.bs_rho(float(S), float(K), float(T), float(r), float(sigma), self._option_type_code(option_type))
        return self._validate_numeric_result(value)

    def greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> CGreeks:
        """Return all Black-Scholes Greeks from C."""
        result = self.lib.bs_greeks(
            float(S),
            float(K),
            float(T),
            float(r),
            float(sigma),
            self._option_type_code(option_type),
        )
        return self._convert_greeks_result(result)


def load_black_scholes_c(library_path: str | Path | None = None) -> BlackScholesCLibrary:
    """Load the C library."""
    return BlackScholesCLibrary(library_path)


def safe_c_implied_vol_bisection(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str,
    library_path: str | Path | None = None,
    lower_bound: float = 1e-6,
    upper_bound: float = 5.0,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
) -> CImpliedVolResult:
    """
    Solve IV with C when available, otherwise fall back to the Python solver.

    If the C shared library is unavailable or the C solve fails, the Python
    bisection solver is used as the fallback.
    """
    try:
        c_library = load_black_scholes_c(library_path)
        c_result = c_library.implied_vol_bisection(
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

        if c_result.solver_status == "success":
            return c_result
    except (FileNotFoundError, OSError, ValueError):
        pass

    python_result = solve_implied_volatility(
        market_price=market_price,
        S=S,
        K=K,
        T=T,
        r=r,
        option_type=option_type,
        method="bisection",
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        tolerance=tolerance,
        max_iterations=max_iterations,
    )

    return CImpliedVolResult(
        implied_volatility=python_result.implied_volatility,
        solver_status=python_result.solver_status,
        failure_reason=python_result.failure_reason,
        status_code=0 if python_result.solver_status == "success" else -1,
        iterations=python_result.iterations,
        pricing_error=python_result.pricing_error,
        lower_bound=python_result.lower_bound,
        upper_bound=python_result.upper_bound,
        input_price=python_result.input_price,
        used_fallback=True,
    )


MC_STATUS_MESSAGES = {
    0: None,
    1: "invalid input",
    2: "null output buffer",
}



@dataclass(frozen=True)
class CSimulationResult:
    """Container for a C simulation result."""
    paths: pd.DataFrame
    status_code: int
    status: str
    failure_reason: str | None
    used_fallback: bool


class MonteCarloCLibrary:
    """Load and call the C Monte Carlo library."""

    def __init__(self, library_path: str | Path | None = None) -> None:
        self.library_path = Path(library_path) if library_path is not None else self._default_library_path()
        self.lib = ctypes.CDLL(str(self.library_path))
        self._configure_signatures()

    @staticmethod
    def candidate_library_paths() -> list[Path]:
        """Return likely shared-library locations for the current platform."""
        project_root = Path(__file__).resolve().parents[1]
        compiled_dir = project_root / "compiled"

        system_name = platform.system().lower()
        if system_name == "darwin":
            names = ["libmonte_carlo.dylib", "libmonte_carlo.so"]
        elif system_name == "windows":
            names = ["monte_carlo.dll", "libmonte_carlo.dll"]
        else:
            names = ["libmonte_carlo.so"]

        return [compiled_dir / name for name in names]

    @classmethod
    def _default_library_path(cls) -> Path:
        for path in cls.candidate_library_paths():
            if path.exists():
                return path

        candidates = ", ".join(str(path) for path in cls.candidate_library_paths())
        raise FileNotFoundError(f"C Monte Carlo library not found. Checked: {candidates}")

    def _configure_signatures(self) -> None:
        self.lib.simulate_gbm_paths.argtypes = [
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_double),
        ]
        self.lib.simulate_gbm_paths.restype = ctypes.c_int

    @staticmethod
    def _paths_to_dataframe(
        prices: np.ndarray,
        time_horizon: float,
        steps: int,
        num_paths: int,
    ) -> pd.DataFrame:
        """Convert a row-major C output array to the project path format."""
        time_grid = np.linspace(0.0, time_horizon, steps + 1)

        path_columns = [f"path_{path_id:04d}" for path_id in range(num_paths)]
        paths = pd.DataFrame(prices, columns=path_columns)
        paths.insert(0, "time_years", time_grid)
        paths.insert(1, "step", np.arange(steps + 1))

        return paths

    def simulate_gbm_paths(
        self,
        starting_price: float,
        drift: float,
        volatility: float,
        time_horizon: float,
        steps: int,
        num_paths: int,
        random_seed: int = 42,
    ) -> CSimulationResult:
        """Simulate GBM paths using the C kernel."""
        output = np.empty((steps + 1, num_paths), dtype=np.float64, order="C")

        status_code = self.lib.simulate_gbm_paths(
            float(starting_price),
            float(drift),
            float(volatility),
            float(time_horizon),
            int(steps),
            int(num_paths),
            ctypes.c_uint64(int(random_seed)),
            output.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        )

        if status_code != 0:
            return CSimulationResult(
                paths=pd.DataFrame(),
                status_code=int(status_code),
                status="failed",
                failure_reason=MC_STATUS_MESSAGES.get(int(status_code), "unknown failure"),
                used_fallback=False,
            )

        paths = self._paths_to_dataframe(
            output,
            time_horizon=time_horizon,
            steps=steps,
            num_paths=num_paths,
        )

        return CSimulationResult(
            paths=paths,
            status_code=0,
            status="success",
            failure_reason=None,
            used_fallback=False,
        )


def load_monte_carlo_c(library_path: str | Path | None = None) -> MonteCarloCLibrary:
    """Load the C Monte Carlo library."""
    return MonteCarloCLibrary(library_path)


def safe_c_simulate_gbm_paths(
    starting_price: float,
    drift: float,
    volatility: float,
    time_horizon: float,
    steps: int,
    num_paths: int,
    random_seed: int = 42,
    library_path: str | Path | None = None,
) -> CSimulationResult:
    """Use the C simulator when available, otherwise fall back to Python."""
    try:
        c_library = load_monte_carlo_c(library_path)
        result = c_library.simulate_gbm_paths(
            starting_price=starting_price,
            drift=drift,
            volatility=volatility,
            time_horizon=time_horizon,
            steps=steps,
            num_paths=num_paths,
            random_seed=random_seed,
        )

        if result.status == "success":
            return result
    except (FileNotFoundError, OSError, ValueError):
        pass

    paths = python_simulate_gbm_paths(
        starting_price=starting_price,
        drift=drift,
        volatility=volatility,
        time_horizon=time_horizon,
        steps=steps,
        num_paths=num_paths,
        random_seed=random_seed,
    )

    return CSimulationResult(
        paths=paths,
        status_code=0,
        status="success",
        failure_reason=None,
        used_fallback=True,
    )


def final_price_statistics(paths: pd.DataFrame) -> pd.Series:
    """Return summary statistics for final simulated prices."""
    path_columns = [column for column in paths.columns if column.startswith("path_")]
    final_prices = paths[path_columns].iloc[-1]

    return pd.Series(
        {
            "mean_final_price": final_prices.mean(),
            "median_final_price": final_prices.median(),
            "std_final_price": final_prices.std(),
            "min_final_price": final_prices.min(),
            "max_final_price": final_prices.max(),
            "p05_final_price": final_prices.quantile(0.05),
            "p95_final_price": final_prices.quantile(0.95),
        }
    )


def compare_python_and_c_statistics(
    python_paths: pd.DataFrame,
    c_paths: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare Python and C path distributions.

    Exact path-by-path matching is not expected because NumPy and the C kernel
    use different random number generators. The fair comparison is distribution
    behavior under the same model inputs.
    """
    python_stats = final_price_statistics(python_paths).rename("python")
    c_stats = final_price_statistics(c_paths).rename("c")

    comparison = pd.concat([python_stats, c_stats], axis=1)
    comparison["c_minus_python"] = comparison["c"] - comparison["python"]
    comparison["abs_difference"] = comparison["c_minus_python"].abs()

    return comparison.reset_index(names="metric")


def benchmark_python_vs_c(
    c_library: MonteCarloCLibrary,
    starting_price: float,
    drift: float,
    volatility: float,
    time_horizon: float,
    steps: int,
    num_paths: int,
    random_seed: int = 42,
    number: int = 5,
) -> pd.DataFrame:
    """
    Benchmark Python/NumPy simulation against the C kernel.

    Compilation is excluded. Both implementations write full path arrays.
    """
    python_time = timeit.timeit(
        lambda: python_simulate_gbm_paths(
            starting_price,
            drift,
            volatility,
            time_horizon,
            steps,
            num_paths,
            random_seed,
        ),
        number=number,
    )

    c_time = timeit.timeit(
        lambda: c_library.simulate_gbm_paths(
            starting_price,
            drift,
            volatility,
            time_horizon,
            steps,
            num_paths,
            random_seed,
        ),
        number=number,
    )

    return pd.DataFrame(
        {
            "implementation": ["Python NumPy", "C through ctypes"],
            "runs": [number, number],
            "steps": [steps, steps],
            "num_paths": [num_paths, num_paths],
            "total_seconds": [python_time, c_time],
            "seconds_per_run": [python_time / number, c_time / number],
        }
    )
