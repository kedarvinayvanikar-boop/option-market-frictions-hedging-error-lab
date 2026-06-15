"""
SQLite utilities for the option market frictions lab.

The database stores raw option snapshots, cleaned quotes, model outputs, and
hedging simulation results in a reproducible structure.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_TABLES = [
    "snapshots",
    "option_quotes_raw",
    "option_quotes_clean",
    "quote_quality_summary",
    "iv_results",
    "iv_uncertainty_results",
    "greek_results",
    "greek_uncertainty_results",
    "surface_diagnostics",
    "hedge_runs",
    "hedge_results",
    "scenario_results",
]


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def execute_sql_file(connection: sqlite3.Connection, sql_path: str | Path) -> None:
    """Execute a SQL script file against an open connection."""
    sql_path = Path(sql_path)

    with sql_path.open("r", encoding="utf-8") as file:
        connection.executescript(file.read())

    connection.commit()


def initialize_database(
    db_path: str | Path = "data/database/options_frictions_lab.db",
    schema_path: str | Path = "sql/schema.sql",
) -> Path:
    """Create the SQLite database and project tables."""
    db_path = Path(db_path)
    schema_path = Path(schema_path)

    with get_connection(db_path) as connection:
        execute_sql_file(connection, schema_path)

    return db_path


def run_query(
    db_path: str | Path,
    query: str,
    params: tuple | dict | None = None,
) -> pd.DataFrame:
    """Run a SELECT query and return the result as a DataFrame."""
    with get_connection(db_path) as connection:
        return pd.read_sql_query(query, connection, params=params)


def table_counts(db_path: str | Path) -> pd.DataFrame:
    """Return row counts for the main project tables."""
    rows = []

    with get_connection(db_path) as connection:
        for table in PROJECT_TABLES:
            count = connection.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
            rows.append({"table_name": table, "row_count": count})

    return pd.DataFrame(rows)


def create_snapshot(
    connection: sqlite3.Connection,
    ticker: str,
    snapshot_time_utc: str,
    source: str,
    raw_file_path: str | None = None,
    notes: str | None = None,
) -> int:
    """Insert a snapshot record and return its identifier."""
    connection.execute(
        """
        INSERT OR IGNORE INTO snapshots (
            ticker,
            snapshot_time_utc,
            source,
            raw_file_path,
            notes
        )
        VALUES (?, ?, ?, ?, ?);
        """,
        (ticker.upper(), snapshot_time_utc, source, raw_file_path, notes),
    )

    snapshot_id = connection.execute(
        """
        SELECT snapshot_id
        FROM snapshots
        WHERE ticker = ?
          AND snapshot_time_utc = ?
          AND source = ?;
        """,
        (ticker.upper(), snapshot_time_utc, source),
    ).fetchone()[0]

    return int(snapshot_id)


def _clean_int(value) -> int | None:
    """Convert numeric values to nullable integers."""
    if pd.isna(value):
        return None
    return int(value)


def _clean_float(value) -> float | None:
    """Convert numeric values to nullable floats."""
    if pd.isna(value):
        return None
    return float(value)


def _clean_text(value) -> str | None:
    """Convert values to nullable strings."""
    if pd.isna(value):
        return None
    return str(value)


def _clean_bool_int(value) -> int | None:
    """Convert boolean-like values to nullable 0/1 integers."""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        return int(value.strip().lower() in {"true", "1", "yes"})
    return int(bool(value))


def insert_raw_option_quotes(
    connection: sqlite3.Connection,
    raw_quotes: pd.DataFrame,
    snapshot_id: int,
) -> int:
    """Insert raw option quotes for a snapshot."""
    if raw_quotes.empty:
        return 0

    rows = []

    for _, row in raw_quotes.iterrows():
        rows.append(
            (
                snapshot_id,
                _clean_text(row.get("contractSymbol")),
                _clean_text(row.get("ticker")),
                _clean_text(row.get("expiration")),
                _clean_text(row.get("option_type")),
                _clean_text(row.get("lastTradeDate")),
                _clean_float(row.get("strike")),
                _clean_float(row.get("lastPrice")),
                _clean_float(row.get("bid")),
                _clean_float(row.get("ask")),
                _clean_float(row.get("change")),
                _clean_float(row.get("percentChange")),
                _clean_int(row.get("volume")),
                _clean_int(row.get("openInterest")),
                _clean_float(row.get("impliedVolatility")),
                _clean_bool_int(row.get("inTheMoney")),
                _clean_text(row.get("contractSize")),
                _clean_text(row.get("currency")),
                _clean_text(row.get("source")),
                _clean_text(row.get("snapshot_time_utc")),
            )
        )

    connection.executemany(
        """
        INSERT OR REPLACE INTO option_quotes_raw (
            snapshot_id,
            contract_symbol,
            ticker,
            expiration,
            option_type,
            last_trade_datetime_utc,
            strike,
            last_price,
            bid,
            ask,
            change_value,
            percent_change,
            volume,
            open_interest,
            vendor_implied_volatility,
            in_the_money,
            contract_size,
            currency,
            source,
            snapshot_time_utc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )

    connection.commit()
    return len(rows)


def _raw_quote_id_map(connection: sqlite3.Connection, snapshot_id: int) -> dict[str, int]:
    """Map contract symbols to raw quote identifiers for one snapshot."""
    rows = connection.execute(
        """
        SELECT contract_symbol, raw_quote_id
        FROM option_quotes_raw
        WHERE snapshot_id = ?;
        """,
        (snapshot_id,),
    ).fetchall()

    return {contract_symbol: raw_quote_id for contract_symbol, raw_quote_id in rows}


def insert_clean_option_quotes(
    connection: sqlite3.Connection,
    clean_quotes: pd.DataFrame,
    snapshot_id: int,
) -> int:
    """Insert cleaned option quotes for a snapshot."""
    if clean_quotes.empty:
        return 0

    raw_id_by_contract = _raw_quote_id_map(connection, snapshot_id)
    rows = []

    for _, row in clean_quotes.iterrows():
        contract_symbol = _clean_text(row.get("contractSymbol"))
        rows.append(
            (
                raw_id_by_contract.get(contract_symbol),
                snapshot_id,
                contract_symbol,
                _clean_text(row.get("ticker")),
                _clean_text(row.get("expiration")),
                _clean_text(row.get("option_type")),
                _clean_float(row.get("strike")),
                _clean_float(row.get("bid")),
                _clean_float(row.get("ask")),
                _clean_float(row.get("mid_price")),
                _clean_float(row.get("bid_ask_spread")),
                _clean_float(row.get("spread_pct")),
                _clean_float(row.get("lastPrice")),
                _clean_int(row.get("volume")),
                _clean_int(row.get("openInterest")),
                _clean_float(row.get("impliedVolatility")),
                _clean_float(row.get("underlying_price")),
                _clean_float(row.get("days_to_expiry")),
                _clean_float(row.get("time_to_maturity")),
                _clean_float(row.get("moneyness")),
                _clean_float(row.get("log_moneyness")),
                _clean_bool_int(row.get("is_excluded")),
                _clean_text(row.get("exclusion_reason")),
                _clean_bool_int(row.get("flag_missing_bid_ask")) or 0,
                _clean_bool_int(row.get("flag_negative_bid_ask")) or 0,
                _clean_bool_int(row.get("flag_crossed_market")) or 0,
                _clean_bool_int(row.get("flag_zero_bid")) or 0,
                _clean_bool_int(row.get("flag_zero_ask")) or 0,
                _clean_bool_int(row.get("flag_invalid_mid")) or 0,
                _clean_bool_int(row.get("flag_wide_spread")) or 0,
                _clean_bool_int(row.get("flag_missing_strike")) or 0,
                _clean_bool_int(row.get("flag_nonpositive_strike")) or 0,
                _clean_bool_int(row.get("flag_missing_expiration")) or 0,
                _clean_bool_int(row.get("flag_expired_contract")) or 0,
                _clean_bool_int(row.get("flag_low_liquidity")) or 0,
            )
        )

    connection.executemany(
        """
        INSERT OR REPLACE INTO option_quotes_clean (
            raw_quote_id,
            snapshot_id,
            contract_symbol,
            ticker,
            expiration,
            option_type,
            strike,
            bid,
            ask,
            mid_price,
            bid_ask_spread,
            spread_pct,
            last_price,
            volume,
            open_interest,
            vendor_implied_volatility,
            underlying_price,
            days_to_expiry,
            time_to_maturity,
            moneyness,
            log_moneyness,
            is_excluded,
            exclusion_reason,
            flag_missing_bid_ask,
            flag_negative_bid_ask,
            flag_crossed_market,
            flag_zero_bid,
            flag_zero_ask,
            flag_invalid_mid,
            flag_wide_spread,
            flag_missing_strike,
            flag_nonpositive_strike,
            flag_missing_expiration,
            flag_expired_contract,
            flag_low_liquidity
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )

    connection.commit()
    return len(rows)


def replace_quote_quality_summary(
    connection: sqlite3.Connection,
    clean_quotes: pd.DataFrame,
    snapshot_id: int,
) -> int:
    """Replace quote-quality summary rows for one snapshot."""
    if "exclusion_reason" not in clean_quotes.columns:
        raise ValueError("clean_quotes must contain exclusion_reason.")

    summary = (
        clean_quotes["exclusion_reason"]
        .value_counts(dropna=False)
        .rename_axis("exclusion_reason")
        .reset_index(name="contract_count")
    )

    summary["share_of_contracts"] = summary["contract_count"] / len(clean_quotes)

    connection.execute(
        "DELETE FROM quote_quality_summary WHERE snapshot_id = ?;",
        (snapshot_id,),
    )

    rows = [
        (
            snapshot_id,
            str(row["exclusion_reason"]),
            int(row["contract_count"]),
            float(row["share_of_contracts"]),
        )
        for _, row in summary.iterrows()
    ]

    connection.executemany(
        """
        INSERT INTO quote_quality_summary (
            snapshot_id,
            exclusion_reason,
            contract_count,
            share_of_contracts
        )
        VALUES (?, ?, ?, ?);
        """,
        rows,
    )

    connection.commit()
    return len(rows)


def clean_quote_id_map(connection: sqlite3.Connection, snapshot_id: int) -> dict[str, int]:
    """Map contract symbols to clean quote identifiers for one snapshot."""
    rows = connection.execute(
        """
        SELECT contract_symbol, clean_quote_id
        FROM option_quotes_clean
        WHERE snapshot_id = ?;
        """,
        (snapshot_id,),
    ).fetchall()

    return {contract_symbol: clean_quote_id for contract_symbol, clean_quote_id in rows}


def insert_iv_results_to_database(
    db_path: str | Path,
    iv_results: pd.DataFrame,
    iv_wide: pd.DataFrame,
    snapshot_id: int,
) -> dict[str, int]:
    """Insert per-quote IV solves and bid/mid/ask IV uncertainty into the database."""
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with get_connection(db_path) as connection:
        quote_map = clean_quote_id_map(connection, snapshot_id)

        iv_rows = []
        for _, row in iv_results.iterrows():
            clean_quote_id = quote_map.get(row["contractSymbol"])
            if clean_quote_id is None:
                continue
            iv_rows.append(
                (
                    clean_quote_id,
                    snapshot_id,
                    row["price_source"],
                    _clean_float(row["input_price"]),
                    _clean_float(row["implied_volatility"]),
                    row["solver_status"],
                    _clean_int(row["solver_iterations"]),
                    _clean_float(row["solver_lower_bound"]),
                    _clean_float(row["solver_upper_bound"]),
                    _clean_float(row["pricing_error"]),
                )
            )

        connection.executemany(
            """
            INSERT OR REPLACE INTO iv_results (
                clean_quote_id,
                snapshot_id,
                price_source,
                input_price,
                implied_volatility,
                solver_status,
                solver_iterations,
                solver_lower_bound,
                solver_upper_bound,
                pricing_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            iv_rows,
        )

        status_by_contract = iv_results.pivot_table(
            index="contractSymbol",
            columns="price_source",
            values="solver_status",
            aggfunc="first",
        )

        uncertainty_rows = []
        for _, row in iv_wide.iterrows():
            clean_quote_id = quote_map.get(row["contractSymbol"])
            if clean_quote_id is None:
                continue

            statuses = (
                status_by_contract.loc[row["contractSymbol"]]
                if row["contractSymbol"] in status_by_contract.index
                else {}
            )

            uncertainty_rows.append(
                (
                    clean_quote_id,
                    snapshot_id,
                    _clean_float(row.get("IV_bid")),
                    _clean_float(row.get("IV_mid")),
                    _clean_float(row.get("IV_ask")),
                    _clean_float(row.get("IV_range")),
                    _clean_float(row.get("IV_relative_range")),
                    statuses.get("bid"),
                    statuses.get("mid"),
                    statuses.get("ask"),
                )
            )

        connection.executemany(
            """
            INSERT OR REPLACE INTO iv_uncertainty_results (
                clean_quote_id,
                snapshot_id,
                iv_bid,
                iv_mid,
                iv_ask,
                iv_range,
                iv_relative_range,
                bid_solver_status,
                mid_solver_status,
                ask_solver_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            uncertainty_rows,
        )

        connection.commit()

    return {
        "iv_results_inserted": len(iv_rows),
        "iv_uncertainty_rows_inserted": len(uncertainty_rows),
    }


def load_option_csv(path: str | Path) -> pd.DataFrame:
    """Load an option CSV file."""
    return pd.read_csv(path)


def populate_database_from_csv(
    db_path: str | Path,
    schema_path: str | Path,
    raw_csv_path: str | Path,
    clean_csv_path: str | Path,
    ticker: str,
    snapshot_time_utc: str,
    source: str = "csv",
) -> dict[str, int]:
    """Create the database and insert raw and cleaned option-chain data."""
    initialize_database(db_path=db_path, schema_path=schema_path)

    raw_quotes = load_option_csv(raw_csv_path)
    clean_quotes = load_option_csv(clean_csv_path)

    with get_connection(db_path) as connection:
        snapshot_id = create_snapshot(
            connection=connection,
            ticker=ticker,
            snapshot_time_utc=snapshot_time_utc,
            source=source,
            raw_file_path=str(raw_csv_path),
        )

        raw_count = insert_raw_option_quotes(connection, raw_quotes, snapshot_id)
        clean_count = insert_clean_option_quotes(connection, clean_quotes, snapshot_id)
        summary_count = replace_quote_quality_summary(connection, clean_quotes, snapshot_id)

    return {
        "snapshot_id": snapshot_id,
        "raw_quote_count": raw_count,
        "clean_quote_count": clean_count,
        "quote_quality_summary_count": summary_count,
    }
