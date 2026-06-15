-- Table inventory
SELECT
    name AS table_name
FROM sqlite_master
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name;

-- Row counts for the main project tables
SELECT 'snapshots' AS table_name, COUNT(*) AS row_count FROM snapshots
UNION ALL SELECT 'option_quotes_raw', COUNT(*) FROM option_quotes_raw
UNION ALL SELECT 'option_quotes_clean', COUNT(*) FROM option_quotes_clean
UNION ALL SELECT 'quote_quality_summary', COUNT(*) FROM quote_quality_summary
UNION ALL SELECT 'iv_results', COUNT(*) FROM iv_results
UNION ALL SELECT 'iv_uncertainty_results', COUNT(*) FROM iv_uncertainty_results
UNION ALL SELECT 'greek_results', COUNT(*) FROM greek_results
UNION ALL SELECT 'greek_uncertainty_results', COUNT(*) FROM greek_uncertainty_results
UNION ALL SELECT 'surface_diagnostics', COUNT(*) FROM surface_diagnostics
UNION ALL SELECT 'hedge_runs', COUNT(*) FROM hedge_runs
UNION ALL SELECT 'hedge_results', COUNT(*) FROM hedge_results
UNION ALL SELECT 'scenario_results', COUNT(*) FROM scenario_results;

-- Raw quote counts by snapshot
SELECT
    s.snapshot_id,
    s.ticker,
    s.snapshot_time_utc,
    COUNT(r.raw_quote_id) AS raw_quote_count
FROM snapshots s
LEFT JOIN option_quotes_raw r
    ON s.snapshot_id = r.snapshot_id
GROUP BY
    s.snapshot_id,
    s.ticker,
    s.snapshot_time_utc
ORDER BY
    s.snapshot_id;

-- Clean quote counts by snapshot
SELECT
    s.snapshot_id,
    s.ticker,
    s.snapshot_time_utc,
    COUNT(c.clean_quote_id) AS clean_quote_count,
    SUM(CASE WHEN c.is_excluded = 0 THEN 1 ELSE 0 END) AS retained_quote_count,
    SUM(CASE WHEN c.is_excluded = 1 THEN 1 ELSE 0 END) AS excluded_quote_count
FROM snapshots s
LEFT JOIN option_quotes_clean c
    ON s.snapshot_id = c.snapshot_id
GROUP BY
    s.snapshot_id,
    s.ticker,
    s.snapshot_time_utc
ORDER BY
    s.snapshot_id;

-- Exclusion reason summary
SELECT
    s.ticker,
    s.snapshot_time_utc,
    q.exclusion_reason,
    q.contract_count,
    ROUND(q.share_of_contracts, 4) AS share_of_contracts
FROM quote_quality_summary q
JOIN snapshots s
    ON q.snapshot_id = s.snapshot_id
ORDER BY
    q.contract_count DESC;

-- Quotes with invalid spread logic
SELECT
    clean_quote_id,
    contract_symbol,
    bid,
    ask,
    mid_price,
    bid_ask_spread,
    spread_pct
FROM option_quotes_clean
WHERE ask < bid
   OR mid_price <= 0
   OR bid_ask_spread < 0;

-- Expired or missing maturity records
SELECT
    clean_quote_id,
    contract_symbol,
    expiration,
    days_to_expiry,
    time_to_maturity
FROM option_quotes_clean
WHERE time_to_maturity IS NULL
   OR time_to_maturity <= 0;

-- Duplicate cleaned contracts within a snapshot
SELECT
    snapshot_id,
    contract_symbol,
    COUNT(*) AS duplicate_count
FROM option_quotes_clean
GROUP BY
    snapshot_id,
    contract_symbol
HAVING COUNT(*) > 1;

-- Orphan IV records
SELECT
    iv.iv_result_id,
    iv.clean_quote_id
FROM iv_results iv
LEFT JOIN option_quotes_clean c
    ON iv.clean_quote_id = c.clean_quote_id
WHERE c.clean_quote_id IS NULL;
