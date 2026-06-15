import pytest

from src.black_scholes import call_price
from src.greeks import (
    calculate_greeks,
    delta,
    gamma,
    theta,
    theta_per_day,
    vega,
    vega_per_vol_point,
)


def test_call_delta_between_zero_and_one():
    value = delta(100.0, 100.0, 0.5, 0.04, 0.25, "call")
    assert 0.0 < value < 1.0


def test_put_delta_between_negative_one_and_zero():
    value = delta(100.0, 100.0, 0.5, 0.04, 0.25, "put")
    assert -1.0 < value < 0.0


def test_call_put_delta_parity():
    call_delta = delta(100.0, 100.0, 0.5, 0.04, 0.25, "call")
    put_delta = delta(100.0, 100.0, 0.5, 0.04, 0.25, "put")
    assert call_delta - put_delta == pytest.approx(1.0)


def test_gamma_is_same_for_call_and_put():
    call_greeks = calculate_greeks(100.0, 100.0, 0.5, 0.04, 0.25, "call")
    put_greeks = calculate_greeks(100.0, 100.0, 0.5, 0.04, 0.25, "put")
    assert call_greeks.gamma == pytest.approx(put_greeks.gamma)


def test_gamma_and_vega_are_positive():
    assert gamma(100.0, 100.0, 0.5, 0.04, 0.25) > 0.0
    assert vega(100.0, 100.0, 0.5, 0.04, 0.25) > 0.0


def test_delta_approximates_small_stock_price_change_for_call():
    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.04
    sigma = 0.25
    bump = 0.01

    finite_difference = (
        call_price(S + bump, K, T, r, sigma)
        - call_price(S - bump, K, T, r, sigma)
    ) / (2 * bump)

    analytic_delta = delta(S, K, T, r, sigma, "call")
    assert analytic_delta == pytest.approx(finite_difference, abs=1e-4)


def test_gamma_approximates_delta_change():
    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.04
    sigma = 0.25
    bump = 0.01

    finite_difference = (
        delta(S + bump, K, T, r, sigma, "call")
        - delta(S - bump, K, T, r, sigma, "call")
    ) / (2 * bump)

    analytic_gamma = gamma(S, K, T, r, sigma)
    assert analytic_gamma == pytest.approx(finite_difference, abs=1e-4)


def test_vega_approximates_volatility_change_for_call():
    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.04
    sigma = 0.25
    bump = 0.0001

    finite_difference = (
        call_price(S, K, T, r, sigma + bump)
        - call_price(S, K, T, r, sigma - bump)
    ) / (2 * bump)

    analytic_vega = vega(S, K, T, r, sigma)
    assert analytic_vega == pytest.approx(finite_difference, abs=1e-3)


def test_theta_day_conversion():
    annual_theta = theta(100.0, 100.0, 0.5, 0.04, 0.25, "call")
    assert theta_per_day(annual_theta) == pytest.approx(annual_theta / 365.0)


def test_vega_per_vol_point_conversion():
    vega_value = vega(100.0, 100.0, 0.5, 0.04, 0.25)
    assert vega_per_vol_point(vega_value) == pytest.approx(vega_value / 100.0)


def test_greeks_reject_expired_options():
    with pytest.raises(ValueError):
        calculate_greeks(100.0, 100.0, 0.0, 0.04, 0.25, "call")


def test_greeks_reject_zero_volatility():
    with pytest.raises(ValueError):
        calculate_greeks(100.0, 100.0, 0.5, 0.04, 0.0, "put")
