import pytest

from aircraft import C172, CL3500
from landing import landing
from units import m_to_ft


def test_c172_regression():
    result = landing(C172)
    assert m_to_ft(result["ground_roll_m"]) == pytest.approx(533, abs=2)
    assert m_to_ft(result["ld_m"]) == pytest.approx(1487, abs=2)


def test_cl3500_regression():
    assert m_to_ft(landing(CL3500, use_reverse=False)["ld_m"]) == pytest.approx(2692, abs=3)


def test_jet_ldr_is_ld_over_0_6():
    result = landing(CL3500)
    assert result["ldr_m"] == pytest.approx(result["ld_m"] / 0.6)


def test_prop_has_no_ldr_rule():
    assert landing(C172)["ldr_m"] is None


def test_every_landing_starts_at_50_ft():
    assert landing(C172)["screen_height_ft"] == 50
    assert landing(CL3500)["screen_height_ft"] == 50


def test_reverse_thrust_shortens_the_roll():
    assert landing(CL3500, use_reverse=True)["ld_m"] < landing(CL3500, use_reverse=False)["ld_m"]


def test_wet_runway_lengthens_the_roll():
    assert landing(CL3500, rwy_condition="wet")["ld_m"] > landing(CL3500)["ld_m"]


def test_bad_runway_condition_is_rejected():
    with pytest.raises(ValueError):
        landing(C172, rwy_condition="icy")
