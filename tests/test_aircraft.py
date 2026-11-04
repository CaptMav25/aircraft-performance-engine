import pytest

from aircraft import Aircraft, PropAircraft, JetAircraft, C172, SR22T, CL3500
from units import ft_to_m, kt_to_mps


def test_base_class_has_no_thrust_model():
    generic = Aircraft("Generic", 1000, 15, 0.03, 0.04, 1.5, 2.0, 0.4, 0.04, 0.4, 2000)
    with pytest.raises(NotImplementedError):
        generic.thrust(30)


def test_mlw_defaults_to_mtow():
    acft = PropAircraft("Test", 1000, 15, 0.03, 0.04, 1.5, 2.0, 0.4, 0.04, 0.4, 2000,
                        max_power_w=100_000, eta_prop=0.7)
    assert acft.mlw_kg == acft.mtow_kg


def test_prop_needs_power_and_efficiency():
    with pytest.raises(ValueError):
        PropAircraft("Test", 1000, 15, 0.03, 0.04, 1.5, 2.0, 0.4, 0.04, 0.4, 2000)


def test_jet_is_at_least_a_twin():
    jet = JetAircraft("Test", 20000, 50, 0.03, 0.04, 1.5, 2.0, 0.3, 0.02, 0.4, 60000, n_engines=1)
    assert jet.n_engines == 2


def test_prop_thrust_is_capped_at_static_thrust():
    # rel tolerance: sigma(0) is 1.00001 because RHO_SL is rounded to 1.225.
    assert C172.thrust(0) == pytest.approx(C172.sls_thrust_n, rel=1e-4)


def test_jet_static_thrust_flat_rated_to_isa_plus_15():
    # At speed, a hot day lowers the Mach number and so slightly raises thrust,
    # so the flat rating is checked at static thrust.
    assert CL3500.thrust(0, isa_dev_c=15) == pytest.approx(CL3500.thrust(0, isa_dev_c=0))
    assert CL3500.thrust(0, isa_dev_c=30) < CL3500.thrust(0, isa_dev_c=15)


def test_one_engine_out_halves_twin_thrust():
    v = kt_to_mps(100)
    assert CL3500.thrust(v, engines_operating=1) == pytest.approx(CL3500.thrust(v) / 2)


def test_turbo_holds_power_below_critical_altitude():
    v = kt_to_mps(100)
    assert SR22T.thrust(v, alt_m=ft_to_m(10_000)) == pytest.approx(SR22T.thrust(v, alt_m=0))
    assert C172.thrust(v, alt_m=ft_to_m(10_000)) < C172.thrust(v, alt_m=0)


def test_spoilers_dump_lift_on_jets_only():
    assert CL3500.cl_braking() == 0.0
    assert C172.cl_braking() == C172.cl_gnd


def test_no_reverse_thrust_below_cutoff():
    assert CL3500.reverse_thrust(kt_to_mps(50)) == 0.0
    assert CL3500.reverse_thrust(kt_to_mps(100)) > 0.0
    assert CL3500.reverse_thrust(kt_to_mps(100), use_reverse=False) == 0.0
