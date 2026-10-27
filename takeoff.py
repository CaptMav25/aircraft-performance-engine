"""
Module:   takeoff
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    All-engines takeoff distance: ground roll to VR, rotation, then the
    transition arc and climb to the screen height (50 ft props, 35 ft jets).
    Engine-failure cases are in bfl.py.

Basis:
    Raymer Ch. 17; Anderson, Aircraft Performance and Design, Ch. 6
    14 CFR 25.107
"""

from aircraft import Aircraft
from segments import make_conditions, accelerate, climb_to_screen, Conditions
from units import ft_to_m, m_to_ft, mps_to_kt, lb_to_kg, kg_to_lb

# Fixed ratios to the stall speed. A real AFM schedules these per weight and
# flap setting; [RAYMER] Ch. 17 gives these as typical, and 1.2 is the
# [14CFR25] §25.107 minimum for V2.
VR_FACTOR = 1.1
V2_FACTOR = 1.2


def takeoff_speeds(acft: Aircraft, cond):
    vs1_mps = acft.stall_speed(cond.weight_n, cond.rho_kg_m3, acft.cl_max_to)
    return vs1_mps, VR_FACTOR * vs1_mps, V2_FACTOR * vs1_mps


def rotation_distance(acft: Aircraft, cond: Conditions, vr_mps):
    # Speed is taken as constant at VR during the rotation.
    return (vr_mps - cond.hw_mps) * acft.ROTATION_S


def takeoff(acft: Aircraft, elev_m=0.0, isa_dev_c=0.0, mass_kg=None, hw_kt=0.0,
            slope_pct=0.0, rwy_condition="dry"):
    """
    All-engines takeoff distance. mass_kg=None uses MTOW; hw_kt is negative
    for a tailwind; slope_pct is + uphill. A wet runway only changes braking,
    so it has no effect here. Returns a dict of results in SI.
    """
    mass_kg = acft.mtow_kg if mass_kg is None else mass_kg
    cond = make_conditions(acft, mass_kg, elev_m, isa_dev_c, hw_kt, slope_pct, rwy_condition)
    vs1_mps, vr_mps, v2_mps = takeoff_speeds(acft, cond)

    dist_vr_m, time_vr_s, solution = accelerate(acft, cond, vr_mps)
    ground_roll_m = dist_vr_m + rotation_distance(acft, cond, vr_mps)
    ground_roll_s = time_vr_s + acft.ROTATION_S

    screen_height_ft = acft.TAKEOFF_SCREEN_HEIGHT_FT
    air_dist_m, climb_grad_pct = climb_to_screen(acft, cond, vs1_mps, screen_height_ft)

    return {
        "acft_name": acft.name,
        "mass_kg": mass_kg,
        "vs1_mps": vs1_mps,
        "vr_mps": vr_mps,
        "v2_mps": v2_mps,
        "ground_roll_m": ground_roll_m,
        "ground_roll_s": ground_roll_s,
        "climb_grad_pct": climb_grad_pct,
        "screen_height_ft": screen_height_ft,
        "air_dist_m": air_dist_m,
        "tod_m": ground_roll_m + air_dist_m,
        "t_hist_s": solution.t,
        "dist_hist_m": solution.y[0],
        "tas_hist_mps": solution.y[1] + cond.hw_mps,
    }


def print_takeoff(result):
    print(f"\n=== Takeoff (all engines): {result['acft_name']} ({result['mass_kg']:,.0f} kg) ===")
    print(f"  VS1 (stall, TO flaps): {mps_to_kt(result['vs1_mps']):7.1f} KTAS")
    print(f"  VR (rotation)        : {mps_to_kt(result['vr_mps']):7.1f} KTAS")
    print(f"  V2 (climb)           : {mps_to_kt(result['v2_mps']):7.1f} KTAS")
    print(f"  Ground roll (to lift): {m_to_ft(result['ground_roll_m']):7.0f} ft  "
          f"({result['ground_roll_m']:.0f} m, {result['ground_roll_s']:.1f} s incl. rotation)")
    print(f"  Climb gradient       : {result['climb_grad_pct']:7.1f} %")
    print(f"  Air distance         : {m_to_ft(result['air_dist_m']):7.0f} ft  "
          f"(to {result['screen_height_ft']:.0f} ft screen)")
    print(f"  TOD (takeoff dist.)  : {m_to_ft(result['tod_m']):7.0f} ft  ({result['tod_m']:.0f} m)")


def ask(prompt, default):
    """Prompt for a number; Enter keeps the default."""
    while True:
        user_input = input(f"  {prompt} (default {default:g}): ").strip()
        if not user_input:
            return default
        try:
            return float(user_input)
        except ValueError:
            print("    Please enter a number.")


def run_takeoff_interactive(acft: Aircraft):
    print(f"\n--- Takeoff conditions for {acft.name} ---")
    elev_ft = ask("Field elevation [ft]", 0)
    isa_dev_c = ask("ISA deviation [°C]", 0)
    mass_lb = ask("Takeoff weight [lb]", round(kg_to_lb(acft.mtow_kg)))
    hw_kt = ask("Headwind [kt] (negative = tailwind)", 0)
    slope_pct = ask("Runway slope [%] (+ = uphill)", 0)

    result = takeoff(acft, elev_m=ft_to_m(elev_ft), isa_dev_c=isa_dev_c,
                     mass_kg=lb_to_kg(mass_lb), hw_kt=hw_kt, slope_pct=slope_pct)
    print_takeoff(result)
    return result
