PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    snapshot_time_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    raw_file_path TEXT,
    notes TEXT,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker, snapshot_time_utc, source)
);

CREATE TABLE IF NOT EXISTS option_quotes_raw (
    raw_quote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    contract_symbol TEXT NOT NULL,
    ticker TEXT NOT NULL,
    expiration TEXT NOT NULL,
    option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
    last_trade_datetime_utc TEXT,
    strike REAL NOT NULL,
    last_price REAL,
    bid REAL,
    ask REAL,
    change_value REAL,
    percent_change REAL,
    volume INTEGER,
    open_interest INTEGER,
    vendor_implied_volatility REAL,
    in_the_money INTEGER,
    contract_size TEXT,
    currency TEXT,
    source TEXT,
    snapshot_time_utc TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    UNIQUE (snapshot_id, contract_symbol)
);

CREATE TABLE IF NOT EXISTS option_quotes_clean (
    clean_quote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_quote_id INTEGER,
    snapshot_id INTEGER NOT NULL,
    contract_symbol TEXT NOT NULL,
    ticker TEXT NOT NULL,
    expiration TEXT NOT NULL,
    option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
    strike REAL NOT NULL,
    bid REAL,
    ask REAL,
    mid_price REAL,
    bid_ask_spread REAL,
    spread_pct REAL,
    last_price REAL,
    volume INTEGER,
    open_interest INTEGER,
    vendor_implied_volatility REAL,
    underlying_price REAL,
    days_to_expiry REAL,
    time_to_maturity REAL,
    moneyness REAL,
    log_moneyness REAL,
    is_excluded INTEGER NOT NULL CHECK (is_excluded IN (0, 1)),
    exclusion_reason TEXT NOT NULL,
    flag_missing_bid_ask INTEGER NOT NULL DEFAULT 0 CHECK (flag_missing_bid_ask IN (0, 1)),
    flag_negative_bid_ask INTEGER NOT NULL DEFAULT 0 CHECK (flag_negative_bid_ask IN (0, 1)),
    flag_crossed_market INTEGER NOT NULL DEFAULT 0 CHECK (flag_crossed_market IN (0, 1)),
    flag_zero_bid INTEGER NOT NULL DEFAULT 0 CHECK (flag_zero_bid IN (0, 1)),
    flag_zero_ask INTEGER NOT NULL DEFAULT 0 CHECK (flag_zero_ask IN (0, 1)),
    flag_invalid_mid INTEGER NOT NULL DEFAULT 0 CHECK (flag_invalid_mid IN (0, 1)),
    flag_wide_spread INTEGER NOT NULL DEFAULT 0 CHECK (flag_wide_spread IN (0, 1)),
    flag_missing_strike INTEGER NOT NULL DEFAULT 0 CHECK (flag_missing_strike IN (0, 1)),
    flag_nonpositive_strike INTEGER NOT NULL DEFAULT 0 CHECK (flag_nonpositive_strike IN (0, 1)),
    flag_missing_expiration INTEGER NOT NULL DEFAULT 0 CHECK (flag_missing_expiration IN (0, 1)),
    flag_expired_contract INTEGER NOT NULL DEFAULT 0 CHECK (flag_expired_contract IN (0, 1)),
    flag_low_liquidity INTEGER NOT NULL DEFAULT 0 CHECK (flag_low_liquidity IN (0, 1)),
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_quote_id) REFERENCES option_quotes_raw(raw_quote_id) ON DELETE SET NULL,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    UNIQUE (snapshot_id, contract_symbol)
);

CREATE TABLE IF NOT EXISTS quote_quality_summary (
    quote_quality_summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    exclusion_reason TEXT NOT NULL,
    contract_count INTEGER NOT NULL,
    share_of_contracts REAL NOT NULL,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    UNIQUE (snapshot_id, exclusion_reason)
);

CREATE TABLE IF NOT EXISTS iv_results (
    iv_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    clean_quote_id INTEGER NOT NULL,
    snapshot_id INTEGER NOT NULL,
    price_source TEXT NOT NULL CHECK (price_source IN ('bid', 'mid', 'ask')),
    input_price REAL NOT NULL,
    implied_volatility REAL,
    solver_status TEXT NOT NULL,
    solver_iterations INTEGER,
    solver_lower_bound REAL,
    solver_upper_bound REAL,
    pricing_error REAL,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clean_quote_id) REFERENCES option_quotes_clean(clean_quote_id) ON DELETE CASCADE,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    UNIQUE (clean_quote_id, price_source)
);

CREATE TABLE IF NOT EXISTS iv_uncertainty_results (
    iv_uncertainty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    clean_quote_id INTEGER NOT NULL,
    snapshot_id INTEGER NOT NULL,
    iv_bid REAL,
    iv_mid REAL,
    iv_ask REAL,
    iv_range REAL,
    iv_relative_range REAL,
    bid_solver_status TEXT,
    mid_solver_status TEXT,
    ask_solver_status TEXT,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clean_quote_id) REFERENCES option_quotes_clean(clean_quote_id) ON DELETE CASCADE,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    UNIQUE (clean_quote_id)
);

CREATE TABLE IF NOT EXISTS greek_results (
    greek_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    clean_quote_id INTEGER NOT NULL,
    snapshot_id INTEGER NOT NULL,
    price_source TEXT NOT NULL CHECK (price_source IN ('bid', 'mid', 'ask')),
    implied_volatility REAL NOT NULL,
    delta REAL,
    gamma REAL,
    vega REAL,
    theta REAL,
    rho REAL,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clean_quote_id) REFERENCES option_quotes_clean(clean_quote_id) ON DELETE CASCADE,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    UNIQUE (clean_quote_id, price_source)
);

CREATE TABLE IF NOT EXISTS greek_uncertainty_results (
    greek_uncertainty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    clean_quote_id INTEGER NOT NULL,
    snapshot_id INTEGER NOT NULL,
    delta_bid REAL,
    delta_mid REAL,
    delta_ask REAL,
    delta_range REAL,
    gamma_bid REAL,
    gamma_mid REAL,
    gamma_ask REAL,
    gamma_range REAL,
    vega_bid REAL,
    vega_mid REAL,
    vega_ask REAL,
    vega_range REAL,
    theta_bid REAL,
    theta_mid REAL,
    theta_ask REAL,
    theta_range REAL,
    rho_bid REAL,
    rho_mid REAL,
    rho_ask REAL,
    rho_range REAL,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (clean_quote_id) REFERENCES option_quotes_clean(clean_quote_id) ON DELETE CASCADE,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
    UNIQUE (clean_quote_id)
);

CREATE TABLE IF NOT EXISTS surface_diagnostics (
    surface_diagnostic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL,
    expiration TEXT NOT NULL,
    option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
    moneyness_bucket TEXT,
    quote_count INTEGER NOT NULL,
    retained_count INTEGER NOT NULL,
    median_spread_pct REAL,
    median_iv_mid REAL,
    median_iv_range REAL,
    solver_failure_rate REAL,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hedge_runs (
    hedge_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name TEXT NOT NULL,
    snapshot_id INTEGER,
    ticker TEXT NOT NULL,
    option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
    strike REAL NOT NULL,
    initial_stock_price REAL NOT NULL,
    risk_free_rate REAL NOT NULL,
    implied_volatility REAL NOT NULL,
    time_to_maturity REAL NOT NULL,
    hedge_frequency TEXT NOT NULL,
    transaction_cost_bps REAL NOT NULL DEFAULT 0,
    path_count INTEGER NOT NULL,
    random_seed INTEGER,
    run_time_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS hedge_results (
    hedge_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hedge_run_id INTEGER NOT NULL,
    path_id INTEGER NOT NULL,
    terminal_stock_price REAL NOT NULL,
    option_payoff REAL NOT NULL,
    hedge_pnl REAL NOT NULL,
    transaction_cost REAL NOT NULL,
    hedging_error REAL NOT NULL,
    rebalance_count INTEGER NOT NULL,
    FOREIGN KEY (hedge_run_id) REFERENCES hedge_runs(hedge_run_id) ON DELETE CASCADE,
    UNIQUE (hedge_run_id, path_id)
);

CREATE TABLE IF NOT EXISTS scenario_results (
    scenario_result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_name TEXT NOT NULL,
    hedge_run_id INTEGER,
    snapshot_id INTEGER,
    hedge_frequency TEXT,
    transaction_cost_bps REAL,
    path_count INTEGER,
    mean_hedging_error REAL,
    std_hedging_error REAL,
    mean_abs_hedging_error REAL,
    p05_hedging_error REAL,
    p50_hedging_error REAL,
    p95_hedging_error REAL,
    mean_transaction_cost REAL,
    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hedge_run_id) REFERENCES hedge_runs(hedge_run_id) ON DELETE SET NULL,
    FOREIGN KEY (snapshot_id) REFERENCES snapshots(snapshot_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_snapshot ON option_quotes_raw(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_raw_contract ON option_quotes_raw(contract_symbol);
CREATE INDEX IF NOT EXISTS idx_clean_snapshot ON option_quotes_clean(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_clean_expiry_type ON option_quotes_clean(expiration, option_type);
CREATE INDEX IF NOT EXISTS idx_clean_moneyness ON option_quotes_clean(log_moneyness);
CREATE INDEX IF NOT EXISTS idx_clean_excluded ON option_quotes_clean(is_excluded);
CREATE INDEX IF NOT EXISTS idx_iv_clean_quote ON iv_results(clean_quote_id);
CREATE INDEX IF NOT EXISTS idx_iv_snapshot ON iv_results(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_greek_clean_quote ON greek_results(clean_quote_id);
CREATE INDEX IF NOT EXISTS idx_greek_snapshot ON greek_results(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_hedge_run ON hedge_results(hedge_run_id);
