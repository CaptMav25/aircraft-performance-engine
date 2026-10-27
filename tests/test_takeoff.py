import pytest

from aircraft import C172, SR22T, CL3500
from exceptions import InsufficientThrustError
from takeoff import takeoff
from units import m_to_ft


def tod_ft(acft, **conditions):
    return m_to_ft(takeoff(acft, **conditions)["tod_m"])


def test_sr22t_matches_published_ground_roll():
    # sls_thrust_n was calibrated to AOPA's 1,517 ft ground roll.
    assert m_to_ft(takeoff(SR22T)["ground_roll_m"]) == pytest.approx(1517, rel=0.01)


def test_sr22t_distance_over_50_ft_independent_check():
    # Not tuned. AOPA publishes 2,080 ft.
    assert tod_ft(SR22T) == pytest.approx(2080, rel=0.05)


def test_c172_regression():
    # Values in the README validation table. A change here means the model changed.
    result = takeoff(C172)
    assert m_to_ft(result["ground_roll_m"]) == pytest.approx(881, abs=2)
    assert m_to_ft(result["tod_m"]) == pytest.approx(1332, abs=2)


def test_speed_order():
    result = takeoff(CL3500)
    assert result["vs1_mps"] < result["vr_mps"] < result["v2_mps"]


def test_jet_uses_35_ft_screen_and_prop_50_ft():
    assert takeoff(CL3500)["screen_height_ft"] == 35
    assert takeoff(C172)["screen_height_ft"] == 50


@pytest.mark.parametrize("acft", [C172, CL3500])
def test_headwind_shortens_and_tailwind_lengthens(acft):
    calm = tod_ft(acft)
    assert tod_ft(acft, hw_kt=10) < calm < tod_ft(acft, hw_kt=-5)


@pytest.mark.parametrize("acft", [C172, CL3500])
def test_uphill_heavy_hot_and_high_all_lengthen(acft):
    calm = tod_ft(acft)
    assert tod_ft(acft, slope_pct=1.0) > calm
    assert tod_ft(acft, isa_dev_c=30) > calm
    assert tod_ft(acft, elev_m=1500) > calm
    assert tod_ft(acft, mass_kg=0.8 * acft.mtow_kg) < calm


def test_wet_runway_does_not_change_all_engines_takeoff():
    assert tod_ft(CL3500, rwy_condition="wet") == pytest.approx(tod_ft(CL3500))


def test_underpowered_aircraft_raises():
    with pytest.raises(InsufficientThrustError):
        takeoff(C172, mass_kg=3 * C172.mtow_kg)
