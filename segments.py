"""Building blocks shared by takeoff, landing and BFL: the Conditions for the
day, the accelerating ground roll, the climb to the screen height, and the
braking roll. The equations of motion are written once, here.

Basis:
Anderson, Aircraft Performance and Design, Ch. 6 (ground roll)
Ojha (runway slope term); Raymer Ch. 17 (transition arc)

Author: M. Barsoum
"""

import math
from dataclasses import dataclass

from scipy.integrate import solve_ivp

from atmosphere import isa, G0_MPS2
from aircraft import Aircraft
from exceptions import InsufficientThrustError, ClimbPerformanceError
from units import ft_to_m, kt_to_mps

T_MAX_S = 300.0
MAX_STEP_S = 0.5             # 0.1 s gives the same distances to within 0.1 ft, 5x slower
STOPPED_MPS = 0.1            # the solver never reaches exactly zero
WET_MU_BRAKE_FACTOR = 0.5    # simplified from [AIRBUS-GTG]
RWY_CONDITIONS = ("dry", "wet")
TRANSITION_LOAD_FACTOR = 1.2   # [RAYMER] Ch. 17
V_TR_FACTOR = 1.15             # [RAYMER] Ch. 17


@dataclass
class Conditions:
    """Everything about the day that the equations of motion need."""
    elev_m: float            # pressure altitude
    isa_dev_c: float
    mass_kg: float
    weight_n: float
    rho_kg_m3: float
    hw_mps: float            # negative = tailwind
    slope_rad: float         # in the direction of travel, + = uphill
    mu_brake: float          # already reduced if the runway is wet
    rwy_condition: str


def make_conditions(acft: Aircraft, mass_kg, elev_m=0.0, isa_dev_c=0.0, hw_kt=0.0,
                    slope_pct=0.0, rwy_condition="dry"):
    """Convert runway inputs to the SI quantities used by each flight segment."""
    if rwy_condition not in RWY_CONDITIONS:
        raise ValueError(f"rwy_condition must be one of {RWY_CONDITIONS}")

    _, _, rho_kg_m3 = isa(elev_m, isa_dev_c)
    if rwy_condition == "wet":
        mu_brake = acft.mu_brake * WET_MU_BRAKE_FACTOR
    else:
        mu_brake = acft.mu_brake * 1.0

    return Conditions(
        elev_m=elev_m, isa_dev_c=isa_dev_c,
        mass_kg=mass_kg, weight_n=mass_kg * G0_MPS2,
        rho_kg_m3=rho_kg_m3, hw_mps=kt_to_mps(hw_kt),
        slope_rad=math.atan(slope_pct / 100),
        mu_brake=mu_brake, rwy_condition=rwy_condition,
    )


def _gravity_along_runway(cond: Conditions):
    return cond.weight_n * math.sin(cond.slope_rad)


def accelerate(acft: Aircraft, cond: Conditions, tas_target_mps, gs_start_mps=0.0,
               dist_start_m=0.0, engines_operating=None):
    """Integrate ground distance and GS until the target TAS is reached.

    Returns (dist_end_m, time_s, solution). If the target is already met,
    no integration is needed and solution is None.
    Force balance: [ANDERSON-APD] Ch. 6; runway slope: [OJHA].
    """
    if gs_start_mps + cond.hw_mps >= tas_target_mps:
        return dist_start_m, 0.0, None

    def reached_target(t_s, y):
        return (y[1] + cond.hw_mps) - tas_target_mps

    reached_target.terminal = True
    reached_target.direction = 1

    def equations_of_motion(t_s, y):
        dist_m, gs_mps = y
        tas_mps = gs_mps + cond.hw_mps
        lift_n = acft.lift(tas_mps, cond.rho_kg_m3, acft.cl_gnd)
        drag_n = acft.drag(tas_mps, cond.rho_kg_m3, acft.cl_gnd)
        thrust_n = acft.thrust(tas_mps, cond.elev_m, cond.isa_dev_c, engines_operating)
        friction_n = acft.mu_roll * max(cond.weight_n - lift_n, 0.0)
        accel_mps2 = (
            thrust_n - drag_n - friction_n - _gravity_along_runway(cond)
        ) / cond.mass_kg

        # Brake release must not produce backward motion from rest.
        if gs_mps <= 0:
            if accel_mps2 < 0:
                accel_mps2 = 0.0
        return [gs_mps, accel_mps2]

    solution = solve_ivp(
        equations_of_motion,
        t_span=[0, T_MAX_S],
        y0=[dist_start_m, gs_start_mps],
        events=reached_target,
        max_step=MAX_STEP_S,
    )
    if solution.t_events[0].size:
        return solution.y_events[0][0][0], solution.t_events[0][0], solution

    tas_reached_mps = solution.y[1].max() + cond.hw_mps
    raise InsufficientThrustError(acft.name, tas_reached_mps, tas_target_mps)


def climb_to_screen(acft: Aircraft, cond: Conditions, vs1_mps, screen_height_ft,
                    engines_operating=None):
    """
    Liftoff to the screen height with Raymer's transition arc [RAYMER] Ch. 17:
    find the climb angle at V2, fly a pull-up arc until the path reaches that
    angle, then climb straight if the screen height is still above.
    Returns (air_dist_m, climb_grad_pct).
    """
    v2_mps = 1.2 * vs1_mps
    q_climb_pa = 0.5 * cond.rho_kg_m3 * v2_mps**2
    cl_climb = cond.weight_n / (q_climb_pa * acft.s_ref_m2)
    drag_climb_n = acft.drag(v2_mps, cond.rho_kg_m3, cl_climb)
    thrust_climb_n = acft.thrust(v2_mps, cond.elev_m, cond.isa_dev_c, engines_operating)
    sin_gamma = (thrust_climb_n - drag_climb_n) / cond.weight_n
    if sin_gamma <= 0:
        raise ClimbPerformanceError(acft.name, 100 * math.tan(math.asin(max(sin_gamma, -0.99))))
    gamma_rad = math.asin(min(sin_gamma, 0.99))

    v_tr_mps = V_TR_FACTOR * vs1_mps
    radius_m = v_tr_mps**2 / (G0_MPS2 * (TRANSITION_LOAD_FACTOR - 1))
    h_transition_m = radius_m * (1 - math.cos(gamma_rad))
    screen_height_m = ft_to_m(screen_height_ft)

    if h_transition_m >= screen_height_m:                     # cleared during the arc
        air_dist_m = math.sqrt(radius_m**2 - (radius_m - screen_height_m)**2)
    else:
        s_transition_m = radius_m * math.sin(gamma_rad)
        s_climb_m = (screen_height_m - h_transition_m) / math.tan(gamma_rad)
        air_dist_m = s_transition_m + s_climb_m

    # The arc and climb were computed in the air mass; the headwind shortens
    # the distance over the ground.
    air_dist_m *= (v_tr_mps - cond.hw_mps) / v_tr_mps
    return air_dist_m, 100 * math.tan(gamma_rad)


def decelerate(acft: Aircraft, cond: Conditions, gs_start_mps, dist_start_m=0.0,
               cl=None, use_reverse=False):
    """Integrate the braking roll with zero idle thrust.

    The aircraft supplies braking CL unless cl is given explicitly.
    Returns (dist_end_m, time_s, solution) at the stopping event.
    """
    cl_braking = cl
    if cl is None:
        cl_braking = acft.cl_braking()

    def stopped(t_s, y):
        return y[1] - STOPPED_MPS

    stopped.terminal = True
    stopped.direction = -1

    def equations_of_motion(t_s, y):
        dist_m, gs_mps = y
        tas_mps = gs_mps + cond.hw_mps
        lift_n = acft.lift(tas_mps, cond.rho_kg_m3, cl_braking)
        drag_n = acft.drag(tas_mps, cond.rho_kg_m3, cl_braking)
        brake_n = cond.mu_brake * max(cond.weight_n - lift_n, 0.0)
        rev_n = acft.reverse_thrust(tas_mps, use_reverse)
        accel_mps2 = -(
            drag_n + brake_n + rev_n + _gravity_along_runway(cond)
        ) / cond.mass_kg
        return [gs_mps, accel_mps2]

    solution = solve_ivp(
        equations_of_motion,
        t_span=[0, T_MAX_S],
        y0=[dist_start_m, gs_start_mps],
        events=stopped,
        max_step=MAX_STEP_S,
    )
    return solution.y_events[0][0][0], solution.t_events[0][0], solution
