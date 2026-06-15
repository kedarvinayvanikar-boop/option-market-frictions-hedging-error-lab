-- Snapshot overview
SELECT
    snapshot_id,
    ticker,
    snapshot_time_utc,
    source,
    raw_file_path,
    created_at_utc
FROM snapshots
ORDER BY snapshot_id DESC;

-- Quote retention by snapshot
SELECT
    s.ticker,
    s.snapshot_time_utc,
    COUNT(c.clean_quote_id) AS total_contracts,
    SUM(CASE WHEN c.is_excluded = 0 THEN 1 ELSE 0 END) AS retained_contracts,
    SUM(CASE WHEN c.is_excluded = 1 THEN 1 ELSE 0 END) AS excluded_contracts,
    ROUND(1.0 * SUM(CASE WHEN c.is_excluded = 1 THEN 1 ELSE 0 END) / COUNT(c.clean_quote_id), 4) AS excluded_share
FROM option_quotes_clean c
JOIN snapshots s
    ON c.snapshot_id = s.snapshot_id
GROUP BY
    s.ticker,
    s.snapshot_time_utc
ORDER BY
    s.snapshot_time_utc DESC;

-- Median spread by expiry
SELECT
    expiration,
    option_type,
    COUNT(*) AS retained_contracts,
    AVG(spread_pct) AS avg_spread_pct,
    MIN(spread_pct) AS min_spread_pct,
    MAX(spread_pct) AS max_spread_pct
FROM option_quotes_clean
WHERE is_excluded = 0
GROUP BY
    expiration,
    option_type
ORDER BY
    expiration,
    option_type;

-- Most common exclusion reasons
SELECT
    exclusion_reason,
    SUM(contract_count) AS contract_count
FROM quote_quality_summary
WHERE exclusion_reason <> 'retained'
GROUP BY exclusion_reason
ORDER BY contract_count DESC;

-- IV uncertainty by expiry
SELECT
    c.expiration,
    c.option_type,
    COUNT(u.iv_uncertainty_id) AS contracts_with_iv,
    AVG(u.iv_range) AS avg_iv_range,
    MAX(u.iv_range) AS max_iv_range
FROM iv_uncertainty_results u
JOIN option_quotes_clean c
    ON u.clean_quote_id = c.clean_quote_id
GROUP BY
    c.expiration,
    c.option_type
ORDER BY
    c.expiration,
    c.option_type;

-- Greek uncertainty by expiry
SELECT
    c.expiration,
    c.option_type,
    COUNT(g.greek_uncertainty_id) AS contracts_with_greeks,
    AVG(g.delta_range) AS avg_delta_range,
    AVG(g.gamma_range) AS avg_gamma_range,
    AVG(g.vega_range) AS avg_vega_range,
    AVG(g.theta_range) AS avg_theta_range
FROM greek_uncertainty_results g
JOIN option_quotes_clean c
    ON g.clean_quote_id = c.clean_quote_id
GROUP BY
    c.expiration,
    c.option_type
ORDER BY
    c.expiration,
    c.option_type;

-- Hedge scenario summary
SELECT
    scenario_name,
    hedge_frequency,
    transaction_cost_bps,
    path_count,
    mean_hedging_error,
    std_hedging_error,
    mean_abs_hedging_error,
    p05_hedging_error,
    p50_hedging_error,
    p95_hedging_error,
    mean_transaction_cost
FROM scenario_results
ORDER BY
    scenario_name,
    transaction_cost_bps,
    hedge_frequency;
