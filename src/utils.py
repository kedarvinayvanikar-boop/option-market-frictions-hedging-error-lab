"""
Small utility functions used across the project.

More specialized finance logic should live in its own module rather than being
packed into this file.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


def project_path(*parts: str) -> Path:
    """
    Build a path relative to the project root.
    """
    from src.config import PROJECT_ROOT

    return PROJECT_ROOT.joinpath(*parts)


def save_dataframe(df: pd.DataFrame, path: str | Path, index: bool = False) -> Path:
    """
    Save a DataFrame to CSV and create the parent folder if needed.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=index)
    return output_path


def load_dataframe(path: str | Path) -> pd.DataFrame:
    """
    Load a CSV file into a DataFrame with a clear error if the file is missing.
    """
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    return pd.read_csv(input_path)


def clean_column_names(columns: Iterable[str]) -> list[str]:
    """
    Convert column names into a consistent snake_case style.

    This is useful when raw data has inconsistent names such as
    'Bid Price', 'askPrice', or 'Open Interest'.
    """
    cleaned = []

    for column in columns:
        name = str(column).strip()
        name = name.replace("-", "_").replace(" ", "_")
        name = "".join(char if char.isalnum() or char == "_" else "" for char in name)
        name = "_".join(part for part in name.lower().split("_") if part)
        cleaned.append(name)

    return cleaned


def timestamp_label() -> str:
    """
    Return a compact timestamp label for output files.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")
