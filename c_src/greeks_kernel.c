#include <math.h>

#include "greeks_kernel.h"
#include "bs_pricer.h"
#include "normal_math.h"

#define GREEKS_SUCCESS 0
#define GREEKS_INVALID_INPUT 1
#define GREEKS_INVALID_OPTION_TYPE 2

static int invalid_greek_inputs(double S, double K, double T, double sigma)
{
    return S <= 0.0 || K <= 0.0 || T <= 0.0 || sigma <= 0.0 ||
           !isfinite(S) || !isfinite(K) || !isfinite(T) || !isfinite(sigma);
}

static GreeksResult make_greeks_result(
    double delta,
    double gamma,
    double vega,
    double theta,
    double rho,
    int status_code
)
{
    GreeksResult result;

    result.delta = delta;
    result.gamma = gamma;
    result.vega = vega;
    result.theta = theta;
    result.rho = rho;
    result.status_code = status_code;

    return result;
}

double bs_delta(double S, double K, double T, double r, double sigma, int option_type)
{
    if (invalid_greek_inputs(S, K, T, sigma)) {
        return NAN;
    }

    double d_1 = bs_d1(S, K, T, r, sigma);

    if (option_type == 1) {
        return normal_cdf(d_1);
    }

    if (option_type == -1) {
        return normal_cdf(d_1) - 1.0;
    }

    return NAN;
}

double bs_gamma(double S, double K, double T, double r, double sigma)
{
    if (invalid_greek_inputs(S, K, T, sigma)) {
        return NAN;
    }

    double d_1 = bs_d1(S, K, T, r, sigma);

    return normal_pdf(d_1) / (S * sigma * sqrt(T));
}

double bs_vega(double S, double K, double T, double r, double sigma)
{
    if (invalid_greek_inputs(S, K, T, sigma)) {
        return NAN;
    }

    double d_1 = bs_d1(S, K, T, r, sigma);

    return S * normal_pdf(d_1) * sqrt(T);
}

double bs_theta(double S, double K, double T, double r, double sigma, int option_type)
{
    if (invalid_greek_inputs(S, K, T, sigma)) {
        return NAN;
    }

    double d_1 = bs_d1(S, K, T, r, sigma);
    double d_2 = bs_d2(S, K, T, r, sigma);
    double time_decay = -(S * normal_pdf(d_1) * sigma) / (2.0 * sqrt(T));

    if (option_type == 1) {
        return time_decay - r * K * exp(-r * T) * normal_cdf(d_2);
    }

    if (option_type == -1) {
        return time_decay + r * K * exp(-r * T) * normal_cdf(-d_2);
    }

    return NAN;
}

double bs_rho(double S, double K, double T, double r, double sigma, int option_type)
{
    if (invalid_greek_inputs(S, K, T, sigma)) {
        return NAN;
    }

    double d_2 = bs_d2(S, K, T, r, sigma);

    if (option_type == 1) {
        return K * T * exp(-r * T) * normal_cdf(d_2);
    }

    if (option_type == -1) {
        return -K * T * exp(-r * T) * normal_cdf(-d_2);
    }

    return NAN;
}

GreeksResult bs_greeks(double S, double K, double T, double r, double sigma, int option_type)
{
    if (invalid_greek_inputs(S, K, T, sigma)) {
        return make_greeks_result(NAN, NAN, NAN, NAN, NAN, GREEKS_INVALID_INPUT);
    }

    if (option_type != 1 && option_type != -1) {
        return make_greeks_result(NAN, NAN, NAN, NAN, NAN, GREEKS_INVALID_OPTION_TYPE);
    }

    return make_greeks_result(
        bs_delta(S, K, T, r, sigma, option_type),
        bs_gamma(S, K, T, r, sigma),
        bs_vega(S, K, T, r, sigma),
        bs_theta(S, K, T, r, sigma, option_type),
        bs_rho(S, K, T, r, sigma, option_type),
        GREEKS_SUCCESS
    );
}
