import json

import pytest

import profiles
from aircraft import BUILT_IN, PropAircraft, C172


@pytest.fixture
def profile_file(tmp_path, monkeypatch):
    path = tmp_path / "aircraft_profiles.json"
    monkeypatch.setattr(profiles, "PROFILE_FILE", str(path))
    return path


def test_save_and_load_round_trip(profile_file):
    profiles.load_profiles()
    custom = PropAircraft("Test Single", 1000, 15, 0.03, 0.04, 1.5, 2.0, 0.4, 0.04, 0.4, 2000,
                          max_power_w=100_000, eta_prop=0.7)
    profiles.profiles[custom.name] = custom
    profiles.save_profiles()

    profiles.load_profiles()
    assert profiles.profiles["Test Single"] == custom


def test_built_ins_are_never_written(profile_file):
    profiles.load_profiles()
    profiles.save_profiles()
    assert json.loads(profile_file.read_text()) == {}


def test_built_ins_come_from_the_code_even_if_the_file_has_them(profile_file):
    profile_file.write_text(json.dumps({C172.name: {"engine_type": "prop", "name": C172.name}}))
    profiles.load_profiles()
    assert profiles.profiles[C172.name] is C172


def test_damaged_file_falls_back_to_built_ins(profile_file):
    profile_file.write_text("{ not json")
    loaded = profiles.load_profiles()
    assert set(loaded) == set(BUILT_IN)
