"""
Project configuration.

Centralizing paths and constants here keeps notebooks and scripts cleaner as
the project grows.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = DATA_DIR / "database"

FIGURES_DIR = PROJECT_ROOT / "figures"
REPORTS_DIR = PROJECT_ROOT / "reports"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
SQL_DIR = PROJECT_ROOT / "sql"
C_SRC_DIR = PROJECT_ROOT / "c_src"
COMPILED_DIR = PROJECT_ROOT / "compiled"

TRADING_DAYS_PER_YEAR = 252
DEFAULT_RISK_FREE_RATE = 0.04
DEFAULT_TICKER = "SPY"


def shared_library_name() -> str:
    """Return the platform-specific shared-library name for the example_add demo."""
    import platform

    system = platform.system()

    if system == "Windows":
        return "example_add.dll"
    if system == "Darwin":
        return "libexample_add.dylib"
    return "libexample_add.so"


def shared_library_path() -> Path:
    """Return the full path to the compiled example_add shared library."""
    return COMPILED_DIR / shared_library_name()


def ensure_project_directories() -> None:
    """
    Create the main output folders if they do not already exist.
    """
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        DATABASE_DIR,
        FIGURES_DIR,
        REPORTS_DIR,
        NOTEBOOKS_DIR,
        SQL_DIR,
        COMPILED_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
