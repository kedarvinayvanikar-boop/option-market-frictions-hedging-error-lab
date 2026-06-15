<!--
  Before publishing, replace OWNER/REPO below with your GitHub path
  (e.g. janedoe/option-market-frictions-hedging-error-lab) so the CI badge
  and GitHub Pages link resolve correctly.
-->

# Option Market Frictions & Hedging Error Lab

![Python](https://img.shields.io/badge/python-3.11-blue)
![Tests](https://img.shields.io/badge/tests-54%20passing-brightgreen)
![C](https://img.shields.io/badge/kernels-C%20%2B%20ctypes-lightgrey)
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)

A reproducible risk-measurement lab that quantifies how **bid-ask spreads,
quote liquidity, short expiry, and transaction costs** distort implied
volatility, option Greeks, and discrete delta-hedging performance for SPY
options — built end to end in **Python, SQL, and C**, with an interactive
React dashboard.

> This is an educational project, not a trading strategy. It measures
> *measurement error and hedging error*, and makes no claim about mispriced
> options or future returns.

---

## Key results

**Quote quality.** Of 42 raw SPY contracts across three expiries, 37 (88%)
pass the cleaning filters (zero bid, crossed market, missing bid/ask, spread
> 40% of mid, zero liquidity). Retained spreads run 3-12% of the mid price
and widen toward both wings.

![Quote cleaning summary](figures/data_cleaning_summary.png)

**Implied-volatility uncertainty.** Every contract's IV is solved three
times — from the bid, mid, and ask price — so the gap between the bid and
ask smiles is a direct, model-based measure of IV uncertainty created by the
spread.

![Bid mid ask IV smile](figures/iv_bid_mid_ask_smile.png)

**Greek uncertainty.** The same bid/ask gap propagates into Delta, Gamma,
Vega, and Theta. Gamma uncertainty is largest for the nearest expiry and
away from the money — exactly where short-dated traders need it most.

![Gamma uncertainty heatmap](figures/gamma_uncertainty_heatmap.png)

**Hedging error vs. cost.** A 20-scenario grid (5 hedge frequencies x 4
transaction-cost levels) shows that hedge *frequency* drives risk reduction
far more than the transaction-cost assumption does — daily rebalancing has
the lowest error variance at every cost level, while "no hedge" is an
order of magnitude riskier than any hedged strategy.

![Hedge frequency cost-risk frontier](figures/hedge_frequency_cost_frontier.png)

**All 17 result figures, with captions and interpretation, are in
[`reports/figures_gallery.md`](reports/figures_gallery.md).**

---

## Interactive dashboard

The dashboard turns the processed tables into four explorable views: an
overview with surface reliability and sample simulated paths, a quote-quality
breakdown, an IV-smile/Greeks explorer, and a hedge-scenario explorer where
picking a hedge frequency and transaction-cost level updates the metrics,
histogram, cost-risk frontier, and error heatmap live.

![Dashboard overview](dashboard/screenshots/overview.png)

![Dashboard hedging scenarios](dashboard/screenshots/hedging_scenarios.png)

### Run it

```bash
cd dashboard
npm install
npm run dev       # opens a local dev server, default http://localhost:5173
```

For a static build (e.g. to deploy on GitHub Pages):

```bash
npm run build      # writes dashboard/dist/
npm run preview    # serve the production build locally
```

A GitHub Actions workflow (`.github/workflows/pages.yml`) builds and deploys
`dashboard/dist/` to GitHub Pages automatically on push to `main` — enable
Pages for the repo (Settings -> Pages -> Source: GitHub Actions) and the live
dashboard will be available at `https://OWNER.github.io/REPO/`.

The dashboard's data is a static snapshot embedded in
`dashboard/src/FrictionsLabDashboard.jsx` (the `DATA` constant). To refresh it
after re-running the pipeline:

```bash
python3 build_dashboard_data.py
# then copy the contents of data/processed/dashboard_data.json
# into the DATA constant at the top of FrictionsLabDashboard.jsx
```

---

## Architecture

```mermaid
flowchart TD
    A[Raw SPY option chain CSV] --> B[Cleaning and quote quality]
    B --> C[Implied volatility solver]
    C --> D[IV uncertainty]
    D --> E[Volatility surface]
    D --> F[Greeks and Greek uncertainty]
    F --> G[Short-expiry risk]

    H[GBM simulation] --> I[Delta-hedging simulation]
    I --> J[Scenario grid]

    B --> O[(SQLite database)]
    C --> O
    F --> O

    E --> P[figures/*.png]
    F --> P
    G --> P
    J --> P

    E --> Q[React dashboard]
    F --> Q
    G --> Q
    J --> Q

    R[C kernels: Black-Scholes,\nIV solver, Greeks,\nMonte Carlo paths]
    R -. ctypes, optional .-> C
    R -. ctypes, optional .-> F
    R -. ctypes, optional .-> H
```

- **Python** (`src/`) owns data loading, cleaning, statistics, and
  orchestration — everything in `main.py`.
- **SQL** (`sql/`) defines the relational schema for snapshots, raw and
  cleaned quotes, IV results, and Greek results, with validation and
  reporting queries that run against the populated SQLite database.
- **C** (`c_src/`) provides faster Black-Scholes pricing, IV bisection,
  Greeks, and Monte Carlo path generation via `ctypes`. If a shared library
  isn't compiled, the affected functions fall back to the pure Python
  implementation automatically (`used_fallback=True`).
- **Dashboard** (`dashboard/`) is a Vite + React app that visualizes the
  pipeline's processed tables.

---

## Repository structure

```
.
├── main.py                    Single entry point: runs the full pipeline
├── build_dashboard_data.py    Aggregates results into dashboard_data.json
├── requirements.txt
│
├── src/                       Python modules (cleaning, IV, Greeks, surfaces,
│                               hedging, scenarios, database, plotting, ...)
├── c_src/                      C kernels + build_instructions.md
├── compiled/                   Shared libraries built from c_src/ (gitignored)
│
├── sql/                         schema.sql, validation_queries.sql, report_queries.sql
├── data/
│   ├── raw/                    Frozen option-chain snapshot + price history
│   ├── processed/              Every output table (CSV) + dashboard_data.json
│   └── database/               options_frictions_lab.db (SQLite)
│
├── notebooks/                  01-19, one notebook per analysis step
├── tests/                       pytest suite for src/ and the C bindings
├── figures/                     30 result figures (PNG)
├── reports/
│   └── figures_gallery.md      all 17 key figures with captions
│
├── dashboard/                   Vite + React interactive dashboard
│   ├── src/FrictionsLabDashboard.jsx
│   └── screenshots/
│
└── .github/workflows/           CI (tests) and GitHub Pages deployment
```

---

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Compile the C kernels

```bash
mkdir -p compiled
gcc -shared -fPIC c_src/example_add.c -o compiled/libexample_add.so
gcc -O3 -fPIC -shared c_src/normal_math.c c_src/bs_pricer.c c_src/iv_solver.c c_src/greeks_kernel.c -o compiled/libbs_pricer.so -lm
gcc -O3 -fPIC -shared c_src/monte_carlo.c -o compiled/libmonte_carlo.so -lm
```

See `c_src/build_instructions.md` for macOS and Windows commands, and for
the fallback behavior if a library isn't compiled.

### Run the full pipeline

```bash
python3 main.py
```

This regenerates every table in `data/processed/`, rebuilds
`data/database/options_frictions_lab.db`, and rewrites all 30 figures in
`figures/` — about a minute end to end. The ten stages are: clean quotes,
build the database, solve IV (bid/mid/ask), compute IV uncertainty, build
volatility surfaces, compute Greeks and Greek uncertainty, build the
short-expiry risk dashboard tables, simulate GBM price paths, run a discrete
delta-hedging simulation, and evaluate the hedge-frequency/transaction-cost
scenario grid.

### Run the tests

```bash
pytest
```

54 tests cover the Python modules and the C bindings (with graceful
fallback/skip if a shared library isn't compiled).

### Notebooks

`notebooks/01_...` through `notebooks/19_...` walk through the same steps as
`main.py`, one concept at a time, with explanatory markdown and inline plots.
Run them in numeric order from the project root.

---

## Limitations

- The option-chain snapshot is a single frozen point in time (2026-06-14),
  not a live feed.
- Black-Scholes assumes European exercise and constant volatility; many
  real equity options are American-style and exhibit volatility smiles.
- The hedging and scenario simulations use a separate synthetic
  at-the-money call (S = K = 100) under GBM rather than the live SPY chain,
  so that the "true" volatility used for hedging is known by construction.
- `surface_diagnostics`, `hedge_runs`, `hedge_results`, and
  `scenario_results` are defined in `sql/schema.sql` for a fully relational
  design but are currently produced as CSV outputs rather than loaded into
  the database.
