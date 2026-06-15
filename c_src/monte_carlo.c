#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>

#include "monte_carlo.h"

/*
Simple xorshift64* random number generator.

This is good enough for a learning project and reproducible Monte Carlo
experiments, but it is not a production-grade risk RNG.
*/
static uint64_t xorshift64star(uint64_t *state)
{
    uint64_t x = *state;

    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;

    *state = x;

    return x * 2685821657736338717ULL;
}

static double uniform_01(uint64_t *state)
{
    /*
    Convert the upper 53 bits to a double in [0, 1). The shift and divisor
    match the precision of a double's mantissa.
    */
    uint64_t random_bits = xorshift64star(state) >> 11;
    double u = (double)random_bits * (1.0 / 9007199254740992.0);

    if (u <= 0.0) {
        return DBL_MIN;
    }

    if (u >= 1.0) {
        return 1.0 - DBL_EPSILON;
    }

    return u;
}

static double standard_normal(uint64_t *state)
{
    /*
    Box-Muller transform.

    Two uniforms can generate two normals, but this function keeps the code
    simple by returning one normal draw per call.
    */
    double u1 = uniform_01(state);
    double u2 = uniform_01(state);

    return sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);
}

static int invalid_inputs(
    double starting_price,
    double drift,
    double volatility,
    double time_horizon,
    int steps,
    int num_paths
)
{
    if (!isfinite(starting_price) || !isfinite(drift) ||
        !isfinite(volatility) || !isfinite(time_horizon)) {
        return 1;
    }

    if (starting_price <= 0.0 || volatility < 0.0 ||
        time_horizon <= 0.0 || steps <= 0 || num_paths <= 0) {
        return 1;
    }

    return 0;
}

int simulate_gbm_paths(
    double starting_price,
    double drift,
    double volatility,
    double time_horizon,
    int steps,
    int num_paths,
    uint64_t seed,
    double *output_prices
)
{
    if (output_prices == NULL) {
        return MC_NULL_OUTPUT;
    }

    if (invalid_inputs(starting_price, drift, volatility, time_horizon, steps, num_paths)) {
        return MC_INVALID_INPUT;
    }

    uint64_t state = seed;

    if (state == 0ULL) {
        state = 88172645463393265ULL;
    }

    double dt = time_horizon / (double)steps;
    double drift_step = (drift - 0.5 * volatility * volatility) * dt;
    double diffusion_scale = volatility * sqrt(dt);

    for (int path_id = 0; path_id < num_paths; path_id++) {
        output_prices[path_id] = starting_price;
    }

    for (int step = 1; step <= steps; step++) {
        int previous_offset = (step - 1) * num_paths;
        int current_offset = step * num_paths;

        for (int path_id = 0; path_id < num_paths; path_id++) {
            double previous_price = output_prices[previous_offset + path_id];
            double z = standard_normal(&state);
            double log_return = drift_step + diffusion_scale * z;
            output_prices[current_offset + path_id] = previous_price * exp(log_return);
        }
    }

    return MC_SUCCESS;
}
