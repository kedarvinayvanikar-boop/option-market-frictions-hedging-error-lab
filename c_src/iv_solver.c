#include <math.h>

#include "iv_solver.h"
#include "bs_pricer.h"

#define IV_SUCCESS 0
#define IV_INVALID_INPUT 1
#define IV_NONPOSITIVE_PRICE 2
#define IV_EXPIRED_OPTION 3
#define IV_PRICE_BELOW_LOWER_BOUND 4
#define IV_PRICE_ABOVE_UPPER_BOUND 5
#define IV_ROOT_NOT_BRACKETED 6
#define IV_MAX_ITERATIONS_REACHED 7

static IVResult make_result(
    double implied_volatility,
    int status_code,
    int iterations,
    double pricing_error,
    double lower_bound,
    double upper_bound,
    double input_price
)
{
    IVResult result;

    result.implied_volatility = implied_volatility;
    result.status_code = status_code;
    result.iterations = iterations;
    result.pricing_error = pricing_error;
    result.lower_bound = lower_bound;
    result.upper_bound = upper_bound;
    result.input_price = input_price;

    return result;
}

static int invalid_solver_inputs(
    double market_price,
    double S,
    double K,
    double T,
    double r,
    int option_type,
    double lower_bound,
    double upper_bound,
    double tolerance,
    int max_iterations
)
{
    if (!isfinite(market_price) || !isfinite(S) || !isfinite(K) || !isfinite(T) ||
        !isfinite(r) || !isfinite(lower_bound) || !isfinite(upper_bound) ||
        !isfinite(tolerance)) {
        return 1;
    }

    if (S <= 0.0 || K <= 0.0 || T < 0.0 || lower_bound <= 0.0 ||
        upper_bound <= lower_bound || tolerance <= 0.0 || max_iterations <= 0) {
        return 1;
    }

    if (option_type != 1 && option_type != -1) {
        return 1;
    }

    return 0;
}

static int bound_failure_code(double market_price, double S, double K, double T, double r, int option_type)
{
    double discounted_strike = K * exp(-r * T);
    double lower_price_bound;
    double upper_price_bound;
    double tolerance = 1e-10;

    if (option_type == 1) {
        lower_price_bound = fmax(S - discounted_strike, 0.0);
        upper_price_bound = S;
    } else {
        lower_price_bound = fmax(discounted_strike - S, 0.0);
        upper_price_bound = discounted_strike;
    }

    if (market_price < lower_price_bound - tolerance) {
        return IV_PRICE_BELOW_LOWER_BOUND;
    }

    if (market_price > upper_price_bound + tolerance) {
        return IV_PRICE_ABOVE_UPPER_BOUND;
    }

    return IV_SUCCESS;
}

IVResult bs_implied_vol_bisection(
    double market_price,
    double S,
    double K,
    double T,
    double r,
    int option_type,
    double lower_bound,
    double upper_bound,
    double tolerance,
    int max_iterations
)
{
    if (invalid_solver_inputs(market_price, S, K, T, r, option_type, lower_bound, upper_bound, tolerance, max_iterations)) {
        return make_result(NAN, IV_INVALID_INPUT, 0, NAN, lower_bound, upper_bound, market_price);
    }

    if (market_price <= 0.0) {
        return make_result(NAN, IV_NONPOSITIVE_PRICE, 0, NAN, lower_bound, upper_bound, market_price);
    }

    if (T == 0.0) {
        return make_result(NAN, IV_EXPIRED_OPTION, 0, NAN, lower_bound, upper_bound, market_price);
    }

    int bound_code = bound_failure_code(market_price, S, K, T, r, option_type);
    if (bound_code != IV_SUCCESS) {
        return make_result(NAN, bound_code, 0, NAN, lower_bound, upper_bound, market_price);
    }

    double low = lower_bound;
    double high = upper_bound;
    double low_error = bs_option_price(S, K, T, r, low, option_type) - market_price;
    double high_error = bs_option_price(S, K, T, r, high, option_type) - market_price;

    if (!isfinite(low_error) || !isfinite(high_error)) {
        return make_result(NAN, IV_INVALID_INPUT, 0, NAN, lower_bound, upper_bound, market_price);
    }

    if (fabs(low_error) <= tolerance) {
        return make_result(low, IV_SUCCESS, 0, low_error, lower_bound, upper_bound, market_price);
    }

    if (fabs(high_error) <= tolerance) {
        return make_result(high, IV_SUCCESS, 0, high_error, lower_bound, upper_bound, market_price);
    }

    if (low_error * high_error > 0.0) {
        return make_result(NAN, IV_ROOT_NOT_BRACKETED, 0, NAN, lower_bound, upper_bound, market_price);
    }

    double mid = NAN;
    double mid_error = NAN;

    for (int iteration = 1; iteration <= max_iterations; iteration++) {
        mid = 0.5 * (low + high);
        mid_error = bs_option_price(S, K, T, r, mid, option_type) - market_price;

        if (!isfinite(mid_error)) {
            return make_result(NAN, IV_INVALID_INPUT, iteration, NAN, lower_bound, upper_bound, market_price);
        }

        if (fabs(mid_error) <= tolerance || 0.5 * (high - low) <= tolerance) {
            return make_result(mid, IV_SUCCESS, iteration, mid_error, lower_bound, upper_bound, market_price);
        }

        if (low_error * mid_error <= 0.0) {
            high = mid;
            high_error = mid_error;
        } else {
            low = mid;
            low_error = mid_error;
        }
    }

    return make_result(mid, IV_MAX_ITERATIONS_REACHED, max_iterations, mid_error, lower_bound, upper_bound, market_price);
}
