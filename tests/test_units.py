import pytest

from units import (ft_to_m, m_to_ft, ft2_to_m2, m2_to_ft2, kt_to_mps, mps_to_kt, lb_to_kg,
                   kg_to_lb, lbf_to_n, n_to_lbf, hp_to_w, w_to_hp, c_to_k, k_to_c)

PAIRS = [
    (ft_to_m, m_to_ft, 5000.0),
    (ft2_to_m2, m2_to_ft2, 174.0),
    (kt_to_mps, mps_to_kt, 60.0),
    (lb_to_kg, kg_to_lb, 2550.0),
    (lbf_to_n, n_to_lbf, 630.0),
    (hp_to_w, w_to_hp, 180.0),
    (c_to_k, k_to_c, 15.0),
]


@pytest.mark.parametrize("to_si, from_si, value", PAIRS)
def test_round_trip(to_si, from_si, value):
    assert from_si(to_si(value)) == pytest.approx(value)


def test_known_values():
    assert ft_to_m(1) == 0.3048
    assert kt_to_mps(1) == pytest.approx(1852 / 3600)
    assert lb_to_kg(1) == 0.45359237
    assert c_to_k(15) == pytest.approx(288.15)
