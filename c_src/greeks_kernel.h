#ifndef GREEKS_KERNEL_H
#define GREEKS_KERNEL_H

typedef struct {
    double delta;
    double gamma;
    double vega;
    double theta;
    double rho;
    int status_code;
} GreeksResult;

double bs_delta(double S, double K, double T, double r, double sigma, int option_type);
double bs_gamma(double S, double K, double T, double r, double sigma);
double bs_vega(double S, double K, double T, double r, double sigma);
double bs_theta(double S, double K, double T, double r, double sigma, int option_type);
double bs_rho(double S, double K, double T, double r, double sigma, int option_type);

GreeksResult bs_greeks(double S, double K, double T, double r, double sigma, int option_type);

#endif
