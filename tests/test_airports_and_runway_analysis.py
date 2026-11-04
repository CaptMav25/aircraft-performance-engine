import pytest

from aircraft import C172, CL3500
from airports import CYYZ, KICT, Runway, runway_pair, wind_components
from runway_analysis import analyze_runway, factored_headwind, isa_dev_from_oat
from units import ft_to_m


def test_wind_straight_down_the_runway():
    hw_kt, xw_kt = wind_components(50, 10, 50)
    assert hw_kt == pytest.approx(10)
    assert xw_kt == pytest.approx(0, abs=1e-9)


def test_wind_from_the_right_at_90_degrees():
    hw_kt, xw_kt = wind_components(140, 10, 50)
    assert hw_kt == pytest.approx(0, abs=1e-9)
    assert xw_kt == pytest.approx(10)


def test_wind_factors():
    assert factored_headwind(10) == 5
    assert factored_headwind(-4) == -6


def test_isa_deviation_from_oat():
    assert isa_dev_from_oat(0, 15) == pytest.approx(0)
    assert isa_dev_from_oat(0, 35) == pytest.approx(20)


def test_runway_pair_flips_slope_and_applies_displaced_threshold():
    rwy_a, rwy_b = runway_pair("09", 90, "27", 270, 10_000, disp_1_ft=1_000, slope_1_pct=0.5)
    assert rwy_a.lda_m == pytest.approx(ft_to_m(9_000))
    assert rwy_b.lda_m == pytest.approx(ft_to_m(10_000))
    assert rwy_b.slope_pct == -rwy_a.slope_pct


def test_unknown_runway_raises():
    with pytest.raises(KeyError):
        CYYZ.runway("99")


def test_report_example_passes():
    result = analyze_runway(CL3500, KICT, KICT.runway("01L"), oat_c=30,
                            wind_dir_deg=20, wind_kt=10)
    assert result["hw_perf_kt"] == pytest.approx(5)
    assert result["takeoff_ok"] and result["landing_ok"]


def test_short_runway_fails():
    short = Runway("SHORT", 0, ft_to_m(3_000), ft_to_m(3_000), ft_to_m(3_000), ft_to_m(3_000))
    result = analyze_runway(CL3500, KICT, short)
    assert not result["takeoff_ok"]
    assert not result["landing_ok"]


def test_single_engine_checks_tod_and_ground_roll():
    result = analyze_runway(C172, CYYZ, CYYZ.runway("05"))
    assert [check[0] for check in result["takeoff_checks"]] == ["TOD", "Ground roll"]


def test_strong_tailwind_warns():
    result = analyze_runway(C172, CYYZ, CYYZ.runway("05"), wind_dir_deg=227, wind_kt=15)
    assert result["warnings"]
