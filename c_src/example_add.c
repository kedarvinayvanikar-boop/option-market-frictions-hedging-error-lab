/*
    example_add.c

    A minimal C function used to confirm that Python can call compiled C code.

    The rest of the project uses the same idea for numerical kernels such as
    normal distribution helpers, Black-Scholes pricing, implied-volatility
    solving, Greeks, and simulation loops.
*/

double add_doubles(double a, double b) {
    return a + b;
}
