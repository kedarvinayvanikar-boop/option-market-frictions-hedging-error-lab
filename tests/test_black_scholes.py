import math

import pytest

from src.black_scholes import (
    call_price,
    d1,
    d2,
    intrinsic_value,
    normal_cdf,
    normal_pdf,
    option_price,
    put_call_parity_gap,
    put_price,
)


def test_normal_cdf_center():
    assert normal_cdf(0.0) == pytest.approx(0.5)


def test_normal_pdf_center():
    assert normal_pdf(0.0) == pytest.approx(1.0 / math.sqrt(2.0 * math.pi))


def test_d2_is_d1_minus_sigma_sqrt_t():
    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.04
    sigma = 0.25

    assert d2(S, K, T, r, sigma) == pytest.approx(
        d1(S, K, T, r, sigma) - sigma * math.sqrt(T)
    )


def test_known_at_the_money_prices_are_reasonable():
    S = 100.0
    K = 100.0
    T = 0.5
    r = 0.04
    sigma = 0.25

    assert call_price(S, K, T, r, sigma) == pytest.approx(8.0080, abs=1e-4)
    assert put_price(S, K, T, r, sigma) == pytest.approx(6.0279, abs=1e-4)


def test_call_price_increases_with_stock_price():
    low_stock_call = call_price(95.0, 100.0, 0.5, 0.04, 0.25)
    high_stock_call = call_price(105.0, 100.0, 0.5, 0.04, 0.25)

    assert high_stock_call > low_stock_call


def test_put_price_decreases_with_stock_price():
    low_stock_put = put_price(95.0, 100.0, 0.5, 0.04, 0.25)
    high_stock_put = put_price(105.0, 100.0, 0.5, 0.04, 0.25)

    assert high_stock_put < low_stock_put


def test_call_price_decreases_when_strike_increases():
    low_strike_call = call_price(100.0, 95.0, 0.5, 0.04, 0.25)
    high_strike_call = call_price(100.0, 105.0, 0.5, 0.04, 0.25)

    assert low_strike_call > high_strike_call


def test_put_price_increases_when_strike_increases():
    low_strike_put = put_price(100.0, 95.0, 0.5, 0.04, 0.25)
    high_strike_put = put_price(100.0, 105.0, 0.5, 0.04, 0.25)

    assert high_strike_put > low_strike_put


def test_call_and_put_prices_increase_with_volatility():
    low_vol_call = call_price(100.0, 100.0, 0.5, 0.04, 0.10)
    high_vol_call = call_price(100.0, 100.0, 0.5, 0.04, 0.40)

    low_vol_put = put_price(100.0, 100.0, 0.5, 0.04, 0.10)
    high_vol_put = put_price(100.0, 100.0, 0.5, 0.04, 0.40)

    assert high_vol_call > low_vol_call
    assert high_vol_put > low_vol_put


def test_time_value_for_at_the_money_options():
    short_call = call_price(100.0, 100.0, 30 / 365, 0.04, 0.25)
    long_call = call_price(100.0, 100.0, 1.0, 0.04, 0.25)

    short_put = put_price(100.0, 100.0, 30 / 365, 0.04, 0.25)
    long_put = put_price(100.0, 100.0, 1.0, 0.04, 0.25)

    assert long_call > short_call
    assert long_put > short_put


def test_put_call_parity_gap_is_near_zero():
    gap = put_call_parity_gap(100.0, 100.0, 0.5, 0.04, 0.25)

    assert gap == pytest.approx(0.0, abs=1e-10)


def test_option_price_dispatcher():
    assert option_price(100.0, 100.0, 0.5, 0.04, 0.25, "call") == pytest.approx(
        call_price(100.0, 100.0, 0.5, 0.04, 0.25)
    )
    assert option_price(100.0, 100.0, 0.5, 0.04, 0.25, "put") == pytest.approx(
        put_price(100.0, 100.0, 0.5, 0.04, 0.25)
    )


def test_intrinsic_value_at_expiry():
    assert intrinsic_value(110.0, 100.0, "call") == 10.0
    assert intrinsic_value(90.0, 100.0, "call") == 0.0
    assert intrinsic_value(90.0, 100.0, "put") == 10.0
    assert intrinsic_value(110.0, 100.0, "put") == 0.0


def test_invalid_inputs_raise_errors():
    with pytest.raises(ValueError):
        call_price(-100.0, 100.0, 0.5, 0.04, 0.25)

    with pytest.raises(ValueError):
        put_price(100.0, 0.0, 0.5, 0.04, 0.25)

    with pytest.raises(ValueError):
        call_price(100.0, 100.0, -0.5, 0.04, 0.25)

    with pytest.raises(ValueError):
        put_price(100.0, 100.0, 0.5, 0.04, -0.25)

    with pytest.raises(ValueError):
        option_price(100.0, 100.0, 0.5, 0.04, 0.25, "straddle")
