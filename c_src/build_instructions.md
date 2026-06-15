# Building the C Kernels

The project uses two compiled shared libraries plus one minimal example
library. All commands are run from the project root and write into
`compiled/`.

## libexample_add — Python-to-C smoke test

Source: `c_src/example_add.c`

macOS:

```bash
mkdir -p compiled
clang -shared -fPIC c_src/example_add.c -o compiled/libexample_add.dylib
```

Linux:

```bash
mkdir -p compiled
gcc -shared -fPIC c_src/example_add.c -o compiled/libexample_add.so
```

Windows with MinGW:

```powershell
mkdir compiled
gcc -shared c_src/example_add.c -o compiled/example_add.dll
```

## libbs_pricer — normal distribution, Black-Scholes, IV solver, Greeks

Source files: `c_src/normal_math.c`, `c_src/bs_pricer.c`, `c_src/iv_solver.c`,
`c_src/greeks_kernel.c`

macOS:

```bash
mkdir -p compiled
clang -O3 -fPIC -dynamiclib c_src/normal_math.c c_src/bs_pricer.c c_src/iv_solver.c c_src/greeks_kernel.c -o compiled/libbs_pricer.dylib
```

Linux:

```bash
mkdir -p compiled
gcc -O3 -fPIC -shared c_src/normal_math.c c_src/bs_pricer.c c_src/iv_solver.c c_src/greeks_kernel.c -o compiled/libbs_pricer.so -lm
```

Windows with MinGW:

```powershell
mkdir compiled
gcc -O3 -shared c_src/normal_math.c c_src/bs_pricer.c c_src/iv_solver.c c_src/greeks_kernel.c -o compiled/bs_pricer.dll
```

## libmonte_carlo — GBM path simulation

Source: `c_src/monte_carlo.c`

macOS:

```bash
mkdir -p compiled
clang -O3 -fPIC -dynamiclib c_src/monte_carlo.c -o compiled/libmonte_carlo.dylib
```

Linux:

```bash
mkdir -p compiled
gcc -O3 -fPIC -shared c_src/monte_carlo.c -o compiled/libmonte_carlo.so -lm
```

Windows with MinGW:

```powershell
mkdir compiled
gcc -O3 -shared c_src/monte_carlo.c -o compiled/monte_carlo.dll
```

## Fallback behavior

`src/c_bindings.py` loads each shared library from `compiled/`. If a library
is missing, `safe_c_implied_vol_bisection` and `safe_c_simulate_gbm_paths`
fall back to the pure Python implementations in `src/implied_vol.py` and
`src/simulation.py`, and report `used_fallback=True`. The rest of the project
(`BlackScholesCLibrary`, `MonteCarloCLibrary`) requires the corresponding
library to be compiled first.
