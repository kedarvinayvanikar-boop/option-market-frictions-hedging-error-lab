#include <math.h>

#include "normal_math.h"

static const double INV_SQRT_TWO_PI = 0.39894228040143267794;

double normal_pdf(double x)
{
    return INV_SQRT_TWO_PI * exp(-0.5 * x * x);
}

double normal_cdf(double x)
{
    return 0.5 * (1.0 + erf(x / sqrt(2.0)));
}
