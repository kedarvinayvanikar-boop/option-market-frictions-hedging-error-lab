#ifndef MONTE_CARLO_H
#define MONTE_CARLO_H

#include <stdint.h>

#define MC_SUCCESS 0
#define MC_INVALID_INPUT 1
#define MC_NULL_OUTPUT 2

int simulate_gbm_paths(
    double starting_price,
    double drift,
    double volatility,
    double time_horizon,
    int steps,
    int num_paths,
    uint64_t seed,
    double *output_prices
);

#endif
