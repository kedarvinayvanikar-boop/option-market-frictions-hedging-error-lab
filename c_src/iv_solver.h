#ifndef IV_SOLVER_H
#define IV_SOLVER_H

typedef struct {
    double implied_volatility;
    int status_code;
    int iterations;
    double pricing_error;
    double lower_bound;
    double upper_bound;
    double input_price;
} IVResult;

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
);

#endif
