import pytest

from atmosphere import isa, sigma, speed_of_sound
from exceptions import AtmosphereRangeError, PerformanceError


def test_sea_level_standard_day():
    temp_k, press_pa, rho_kg_m3 = isa(0)
    assert temp_k == pytest.approx(288.15)
    assert press_pa == pytest.approx(101325)
    assert rho_kg_m3 == pytest.approx(1.225, abs=1e-3)
    assert sigma(0) == pytest.approx(1.0, abs=1e-3)


def test_tropopause_temperature():
    assert isa(11000)[0] == pytest.approx(216.65)


def test_hot_day_changes_density_not_pressure():
    standard = isa(1000)
    hot = isa(1000, isa_dev_c=20)
    assert hot[1] == standard[1]
    assert hot[0] == pytest.approx(standard[0] + 20)
    assert hot[2] < standard[2]


def test_speed_of_sound_sea_level():
    assert speed_of_sound(0) == pytest.approx(340.3, abs=0.1)


@pytest.mark.parametrize("alt_m", [-1, 11001])
def test_altitude_outside_model_raises(alt_m):
    with pytest.raises(AtmosphereRangeError):
        isa(alt_m)


def test_range_error_is_caught_as_either_parent():
    with pytest.raises(PerformanceError):
        isa(20000)
    with pytest.raises(ValueError):
        isa(20000)
