"""
Module:   aircraft
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Aircraft base class, PropAircraft and JetAircraft subclasses, and the
    built-in C172S, SR22T and Challenger 3500. Anything that differs by engine
    type (thrust model, screen height, spoilers, reverse thrust, LDR rule) is
    overridden in the subclass, so takeoff and landing code never has to check
    which kind of aircraft it was given.

Basis:
    Anderson, Aircraft Performance and Design, Ch. 6 (drag polar, stall speed)
    Gudmundsson (propeller thrust); Filippone (turbofan lapse, flat rating)
    Data: C172S POH; Bombardier Challenger 3500 factsheet; AOPA (SR22T, CL350)
"""

from dataclasses import dataclass
from typing import ClassVar, Optional
import math

from atmosphere import sigma, speed_of_sound
from units import (ft_to_m, kt_to_mps, kg_to_lb, lb_to_kg, lbf_to_n, m2_to_ft2,
                   ft2_to_m2, n_to_lbf, w_to_hp, hp_to_w)


@dataclass
class Aircraft:
    """
    Everything every aircraft has. Not used directly: create a PropAircraft
    or JetAircraft instead. Subclasses must override thrust().
    """

    # Class variables are fixed by certification category, so they are not
    # saved with each profile.
    ENGINE_TYPE: ClassVar[str] = "generic"
    TAKEOFF_SCREEN_HEIGHT_FT: ClassVar[float] = 50.0
    LANDING_SCREEN_HEIGHT_FT: ClassVar[float] = 50.0
    FREE_ROLL_S: ClassVar[float] = 2.0             # touchdown to full braking
    ROTATION_S: ClassVar[float] = 1.0              # VR to liftoff; Raymer gives ~1 s small, ~3 s large
    LDR_FACTOR: ClassVar[Optional[float]] = None   # None: no operating rule applied

    name: str
    mtow_kg: float
    s_ref_m2: float
    cd0: float
    k_induced: float        # CD = cd0 + k_induced * CL^2
    cl_max_to: float
    cl_max_ldg: float
    cl_gnd: float           # wing CL with the aircraft sitting on its gear
    mu_roll: float          # dry paved runway
    mu_brake: float         # dry paved runway
    sls_thrust_n: float     # all engines
    mlw_kg: float = 0.0     # 0 means MLW = MTOW
    n_engines: int = 1

    def __post_init__(self):
        if not self.mlw_kg:
            self.mlw_kg = self.mtow_kg
        self.n_engines = int(self.n_engines)
        if self.n_engines < 1:
            raise ValueError(f"{self.name}: n_engines must be at least 1")

    def engine_fraction(self, engines_operating=None):
        """Fraction of total thrust available: 1.0 all engines, (n-1)/n one engine out."""
        if engines_operating is None:
            return 1.0
        return max(0, min(engines_operating, self.n_engines)) / self.n_engines

    def stall_speed(self, weight_n, rho_kg_m3, cl_max):
        """Stall speed, TAS [m/s]."""
        return math.sqrt(2 * weight_n / (rho_kg_m3 * self.s_ref_m2 * cl_max))

    def drag(self, tas_mps, rho_kg_m3, cl):
        """Drag [N] from a parabolic drag polar."""
        q_pa = 0.5 * rho_kg_m3 * tas_mps**2
        return q_pa * self.s_ref_m2 * (self.cd0 + self.k_induced * cl**2)

    def lift(self, tas_mps, rho_kg_m3, cl):
        q_pa = 0.5 * rho_kg_m3 * tas_mps**2
        return q_pa * self.s_ref_m2 * cl

    def thrust(self, tas_mps, alt_m=0.0, isa_dev_c=0.0, engines_operating=None):
        """Total thrust [N]. engines_operating=None means all engines."""
        raise NotImplementedError(f"{type(self).__name__} must override thrust()")

    def cl_braking(self):
        return self.cl_gnd

    def reverse_thrust(self, tas_mps, use_reverse=True):
        return 0.0

    def __str__(self):
        return (f"{self.name} ({self.ENGINE_TYPE}, {self.n_engines} eng): "
                f"MTOW {kg_to_lb(self.mtow_kg):,.0f} lb, "
                f"S_ref {m2_to_ft2(self.s_ref_m2):,.0f} ft², "
                f"SLS thrust {n_to_lbf(self.sls_thrust_n):,.0f} lbf")


@dataclass
class PropAircraft(Aircraft):
    """Piston/propeller aircraft. Certified under Part 23: 50 ft screen height."""

    ENGINE_TYPE: ClassVar[str] = "prop"
    TAKEOFF_SCREEN_HEIGHT_FT: ClassVar[float] = 50.0
    FREE_ROLL_S: ClassVar[float] = 2.0

    max_power_w: float = 0.0        # all engines, sea level
    eta_prop: float = 0.0
    critical_alt_m: float = 0.0     # turbocharger critical altitude; 0 = normally aspirated

    def __post_init__(self):
        super().__post_init__()
        if self.max_power_w <= 0 or self.eta_prop <= 0:
            raise ValueError(f"{self.name}: a PropAircraft needs max_power_w and eta_prop > 0")

    def thrust(self, tas_mps, alt_m=0.0, isa_dev_c=0.0, engines_operating=None):
        """
        T = eta P / V, capped at static thrust. T = eta P / V goes to infinity at
        V = 0, so the cap stands in for the real static thrust [GUDMUNDSSON].
        A turbocharger holds rated power up to its critical altitude; a normally
        aspirated engine loses power with density from sea level.
        """
        if self.critical_alt_m > 0:
            sig = 1.0 if alt_m <= self.critical_alt_m else (
                sigma(alt_m, isa_dev_c) / sigma(self.critical_alt_m, isa_dev_c))
        else:
            sig = sigma(alt_m, isa_dev_c)
        power_avail_w = self.max_power_w * sig
        thrust_cap_n = self.sls_thrust_n * sig
        thrust_prop_n = self.eta_prop * power_avail_w / max(tas_mps, 1.0)
        return min(thrust_cap_n, thrust_prop_n) * self.engine_fraction(engines_operating)

    def __str__(self):
        return super().__str__() + f", {w_to_hp(self.max_power_w):,.0f} hp"


@dataclass
class JetAircraft(Aircraft):
    """
    Turbofan transport aircraft certified under Part 25 / CAR 525:
    35 ft takeoff screen height, 50 ft landing screen height.
    Lands with ground spoilers and (optionally) reverse thrust; LDR = LD / 0.6.
    """

    ENGINE_TYPE: ClassVar[str] = "jet"
    TAKEOFF_SCREEN_HEIGHT_FT: ClassVar[float] = 35.0
    FREE_ROLL_S: ClassVar[float] = 3.0
    ROTATION_S: ClassVar[float] = 3.0
    LDR_FACTOR: ClassVar[Optional[float]] = 1 / 0.6    # 14 CFR 121.195: land within 60% of LDA
    REV_CUTOFF_KT: ClassVar[float] = 60.0              # reversers are stowed below about 60 kt

    thrust_lapse: float = 0.9
    rev_thrust_ratio: float = 0.0   # fraction of SLS thrust
    flat_rating_isa_c: float = 15.0

    def __post_init__(self):
        super().__post_init__()
        if self.n_engines < 2:
            self.n_engines = 2          # BFL needs an engine to fail and one to keep going

    def thrust(self, tas_mps, alt_m=0.0, isa_dev_c=0.0, engines_operating=None):
        """
        T = T_SLS * sigma_eff^0.7 * (1 - lapse * M), simplified from [FILIPPONE].
        The engine control holds rated thrust up to ISA + flat_rating_isa_c, so
        only the temperature above that point reduces thrust. Altitude still does.
        """
        excess_c = max(isa_dev_c - self.flat_rating_isa_c, 0.0)
        sig_eff = sigma(alt_m, excess_c)
        mach = tas_mps / speed_of_sound(alt_m, isa_dev_c)          # real temperature, not excess_c
        thrust_n = self.sls_thrust_n * sig_eff**0.7 * (1 - self.thrust_lapse * mach)
        return thrust_n * self.engine_fraction(engines_operating)

    def cl_braking(self):
        # Ground spoilers dump almost all lift on touchdown.
        return 0.0

    def reverse_thrust(self, tas_mps, use_reverse=True):
        # Not credited in certified dry-runway distances, [14CFR25] §25.125.
        if not use_reverse or tas_mps <= kt_to_mps(self.REV_CUTOFF_KT):
            return 0.0
        return self.rev_thrust_ratio * self.sls_thrust_n


# profiles.py saves ENGINE_TYPE as text; this turns it back into a class.
AIRCRAFT_CLASSES = {cls.ENGINE_TYPE: cls for cls in (PropAircraft, JetAircraft)}


C172 = PropAircraft(
    name="Cessna 172S",
    mtow_kg=lb_to_kg(2550),
    s_ref_m2=16.2,
    cd0=0.032,
    k_induced=0.045,
    cl_max_to=1.5,                  # flaps 10°
    cl_max_ldg=2.0,                 # flaps 30°
    cl_gnd=0.4,
    mu_roll=0.04,
    mu_brake=0.40,
    sls_thrust_n=2800.0,
    mlw_kg=lb_to_kg(2550),
    n_engines=1,
    max_power_w=134_000.0,          # 180 hp
    eta_prop=0.65,
)

# Cirrus SR22T, Continental TSIO-550-K turbocharged.
# MTOW, power, VS0 and published distances: AOPA aircraft guide. Wing area: Cirrus
# (144.9 ft²). cl_max_ldg from VS0 = 60 KCAS at MTOW. sls_thrust_n is calibrated to the
# published takeoff ground roll; the distance over 50 ft is then an independent check.
SR22T = PropAircraft(
    name="Cirrus SR22T",
    mtow_kg=lb_to_kg(3600),
    s_ref_m2=ft2_to_m2(144.9),
    cd0=0.027,                      # estimate
    k_induced=0.045,                # estimate
    cl_max_to=1.60,                 # flaps 50%, estimate
    cl_max_ldg=2.04,                # from VS0 = 60 KCAS
    cl_gnd=0.4,
    mu_roll=0.04,
    mu_brake=0.40,
    sls_thrust_n=3_580.0,           # calibrated to the 1,517 ft ground roll
    mlw_kg=lb_to_kg(3600),
    n_engines=1,
    max_power_w=hp_to_w(315),
    eta_prop=0.72,                  # constant-speed prop, estimate
    critical_alt_m=ft_to_m(25_000), # assumed
)


# Bombardier Challenger 3500, 2 x Honeywell HTF7350.
# Weights: Challenger 350/3500 airframe (AOPA, AeroCorner). Thrust and flat rating:
# Bombardier factsheet. Wing area and aero coefficients are ESTIMATES; CL_max_to and
# cd0 are calibrated so the takeoff field length matches Bombardier's 4,835 ft
# (see README, Validation). Landing distance is then an independent check.
CL3500 = JetAircraft(
    name="Challenger 3500",
    mtow_kg=lb_to_kg(40_600),
    s_ref_m2=48.5,                  # estimate
    cd0=0.030,                      # takeoff flaps and gear down, estimate
    k_induced=0.045,                # estimate
    cl_max_to=1.57,                 # calibrated to TOFL 4,835 ft
    cl_max_ldg=2.30,                # estimate
    cl_gnd=0.30,
    mu_roll=0.02,
    mu_brake=0.40,
    sls_thrust_n=2 * lbf_to_n(7_323),
    mlw_kg=lb_to_kg(34_150),
    n_engines=2,
    thrust_lapse=0.90,
    rev_thrust_ratio=0.30,
    flat_rating_isa_c=15.0,
)

BUILT_IN = {C172.name: C172, SR22T.name: SR22T, CL3500.name: CL3500}
