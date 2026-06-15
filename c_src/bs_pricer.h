#ifndef BS_PRICER_H
#define BS_PRICER_H

double bs_d1(double S, double K, double T, double r, double sigma);
double bs_d2(double S, double K, double T, double r, double sigma);
double bs_call_price(double S, double K, double T, double r, double sigma);
double bs_put_price(double S, double K, double T, double r, double sigma);
double bs_option_price(double S, double K, double T, double r, double sigma, int option_type);

#endif
