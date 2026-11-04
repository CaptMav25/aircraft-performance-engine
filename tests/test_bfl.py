import pytest

from aircraft import C172, CL3500
from bfl import accelerate_go, accelerate_stop, balanced_field
from segments import make_conditions
from units import m_to_ft


@pytest.fixture(scope="module")
def cl3500_sea_level():
    return balanced_field(CL3500, n_curve_points=5)


def test_cl3500_matches_published_tofl(cl3500_sea_level):
    # cl_max_to was calibrated to Bombardier's 4,835 ft.
    assert m_to_ft(cl3500_sea_level["tofl_m"]) == pytest.approx(4835, rel=0.01)


def test_go_and_stop_are_equal_at_balanced_v1(cl3500_sea_level):
    result = cl3500_sea_level
    assert result["balance_note"] == "balanced"
    assert result["todg_oei_m"] == pytest.approx(result["asd_m"], abs=1.0)


def test_v1_does_not_exceed_vr(cl3500_sea_level):
    assert cl3500_sea_level["v1_mps"] <= cl3500_sea_level["vr_mps"]


def test_tofl_is_the_larger_of_bfl_and_factored_aeo(cl3500_sea_level):
    result = cl3500_sea_level
    assert result["tofl_m"] == max(result["bfl_m"], 1.15 * result["tod_aeo_m"])


def test_go_falls_and_stop_rises_with_v1():
    cond = make_conditions(CL3500, CL3500.mtow_kg)
    slow, fast = 50.0, 65.0
    assert accelerate_go(CL3500, cond, fast)[0] < accelerate_go(CL3500, cond, slow)[0]
    assert accelerate_stop(CL3500, cond, fast) > accelerate_stop(CL3500, cond, slow)


def test_single_engine_has_no_balanced_field():
    with pytest.raises(ValueError):
        balanced_field(C172)


def test_hot_day_above_flat_rating_lengthens_tofl(cl3500_sea_level):
    hot = balanced_field(CL3500, isa_dev_c=30, n_curve_points=2)
    assert hot["tofl_m"] > cl3500_sea_level["tofl_m"]
