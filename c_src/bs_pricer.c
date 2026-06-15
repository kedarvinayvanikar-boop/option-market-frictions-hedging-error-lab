#include <math.h>

#include "bs_pricer.h"
#include "normal_math.h"

static int invalid_inputs(double S, double K, double T, double sigma)
{
    return S <= 0.0 || K <= 0.0 || T < 0.0 || sigma < 0.0;
}

double bs_d1(double S, double K, double T, double r, double sigma)
{
    if (invalid_inputs(S, K, T, sigma) || T == 0.0 || sigma == 0.0) {
        return NAN;
    }

    return (log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * sqrt(T));
}

double bs_d2(double S, double K, double T, double r, double sigma)
{
    double d_1 = bs_d1(S, K, T, r, sigma);

    if (isnan(d_1)) {
        return NAN;
    }

    return d_1 - sigma * sqrt(T);
}

double bs_call_price(double S, double K, double T, double r, double sigma)
{
    if (invalid_inputs(S, K, T, sigma)) {
        return NAN;
    }

    if (T == 0.0) {
        return fmax(S - K, 0.0);
    }

    if (sigma == 0.0) {
        return fmax(S - K * exp(-r * T), 0.0);
    }

    double d_1 = bs_d1(S, K, T, r, sigma);
    double d_2 = d_1 - sigma * sqrt(T);

    return S * normal_cdf(d_1) - K * exp(-r * T) * normal_cdf(d_2);
}

double bs_put_price(double S, double K, double T, double r, double sigma)
{
    if (invalid_inputs(S, K, T, sigma)) {
        return NAN;
    }

    if (T == 0.0) {
        return fmax(K - S, 0.0);
    }

    if (sigma == 0.0) {
        return fmax(K * exp(-r * T) - S, 0.0);
    }

    double d_1 = bs_d1(S, K, T, r, sigma);
    double d_2 = d_1 - sigma * sqrt(T);

    return K * exp(-r * T) * normal_cdf(-d_2) - S * normal_cdf(-d_1);
}

double bs_option_price(double S, double K, double T, double r, double sigma, int option_type)
{
    if (option_type == 1) {
        return bs_call_price(S, K, T, r, sigma);
    }

    if (option_type == -1) {
        return bs_put_price(S, K, T, r, sigma);
    }

    return NAN;
}
