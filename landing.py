"""
Module:   landing
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Landing distance from 50 ft: air distance on a 3 degree glideslope, free
    roll after touchdown, then the braking roll. Jets add spoilers, optional
    reverse thrust and the LDR = LD / 0.6 rule.

Basis:
    Anderson, Aircraft Performance and Design, Ch. 6; Raymer Ch. 17
    14 CFR 25.125, 121.195
"""

import math

from aircraft import Aircraft, JetAircraft
from segments import make_conditions, decelerate
from takeoff import ask
from units import ft_to_m, m_to_ft, mps_to_kt, lb_to_kg, kg_to_lb

GLIDESLOPE_DEG = 3.0                       # [AIRBUS-GTG]
VREF_FACTOR = 1.3                          # [RAYMER] Ch. 17
VTD_FACTOR = 1.15                          # the flare bleeds speed from VREF; [RAYMER] Ch. 17


def landing(acft: Aircraft, elev_m=0.0, isa_dev_c=0.0, mass_kg=None, hw_kt=0.0,
            use_reverse=True, slope_pct=0.0, rwy_condition="dry"):
    """
    Landing distance from 50 ft: air distance on the glideslope, a free roll
    before the brakes act, then the braking roll. mass_kg=None uses MLW.
    Returns a dict of results in SI.
    """
    mass_kg = acft.mlw_kg if mass_kg is None else mass_kg
    cond = make_conditions(acft, mass_kg, elev_m, isa_dev_c, hw_kt, slope_pct, rwy_condition)

    vs0_mps = acft.stall_speed(cond.weight_n, cond.rho_kg_m3, acft.cl_max_ldg)
    vref_mps = VREF_FACTOR * vs0_mps
    vtd_mps = VTD_FACTOR * vs0_mps

    screen_height_ft = acft.LANDING_SCREEN_HEIGHT_FT
    air_dist_m = ((ft_to_m(screen_height_ft) / math.tan(math.radians(GLIDESLOPE_DEG)))
                  * (vref_mps - cond.hw_mps) / vref_mps)

    free_roll_s = acft.FREE_ROLL_S
    free_roll_m = (vtd_mps - cond.hw_mps) * free_roll_s

    gs_td_mps = vtd_mps - cond.hw_mps
    braking_roll_m, braking_s, solution = decelerate(acft, cond, gs_td_mps,
                                                     use_reverse=use_reverse)

    ground_roll_m = free_roll_m + braking_roll_m
    ld_m = air_dist_m + ground_roll_m

    return {
        "acft_name": acft.name,
        "mass_kg": mass_kg,
        "engine_type": acft.ENGINE_TYPE,
        "rwy_condition": rwy_condition,
        "rev_used": acft.reverse_thrust(vtd_mps, use_reverse) > 0,
        "vs0_mps": vs0_mps,
        "vref_mps": vref_mps,
        "vtd_mps": vtd_mps,
        "screen_height_ft": screen_height_ft,
        "air_dist_m": air_dist_m,
        "free_roll_m": free_roll_m,
        "braking_roll_m": braking_roll_m,
        "braking_s": braking_s,
        "ground_roll_m": ground_roll_m,
        "ld_m": ld_m,
        "ldr_m": ld_m * acft.LDR_FACTOR if acft.LDR_FACTOR else None,
        "t_hist_s": solution.t,
        "dist_hist_m": solution.y[0],
        "tas_hist_mps": solution.y[1] + cond.hw_mps,
    }


def print_landing(result):
    rev_txt = " + reverse thrust" if result["rev_used"] else ""
    wet_txt = ", WET runway" if result["rwy_condition"] == "wet" else ""
    print(f"\n=== Landing: {result['acft_name']} ({result['mass_kg']:,.0f} kg){rev_txt}{wet_txt} ===")
    print(f"  VS0 (stall, LDG flaps): {mps_to_kt(result['vs0_mps']):7.1f} KTAS")
    print(f"  VREF (approach)       : {mps_to_kt(result['vref_mps']):7.1f} KTAS")
    print(f"  VTD (touchdown)       : {mps_to_kt(result['vtd_mps']):7.1f} KTAS")
    print(f"  Air distance          : {m_to_ft(result['air_dist_m']):7.0f} ft  "
          f"(from {result['screen_height_ft']:.0f} ft screen)")
    print(f"  Free roll             : {m_to_ft(result['free_roll_m']):7.0f} ft")
    print(f"  Braking roll          : {m_to_ft(result['braking_roll_m']):7.0f} ft  "
          f"({result['braking_s']:.1f} s)")
    print(f"  Ground roll           : {m_to_ft(result['ground_roll_m']):7.0f} ft  "
          f"({result['ground_roll_m']:.0f} m)")
    print(f"  LD (landing distance) : {m_to_ft(result['ld_m']):7.0f} ft  ({result['ld_m']:.0f} m)")
    if result["ldr_m"]:
        print(f"  LDR (required, ÷0.6)  : {m_to_ft(result['ldr_m']):7.0f} ft  ({result['ldr_m']:.0f} m)")


def run_landing_interactive(acft: Aircraft):
    print(f"\n--- Landing conditions for {acft.name} ---")
    elev_ft = ask("Field elevation [ft]", 0)
    isa_dev_c = ask("ISA deviation [°C]", 0)
    mass_lb = ask("Landing weight [lb]", round(kg_to_lb(acft.mlw_kg)))
    hw_kt = ask("Headwind [kt] (negative = tailwind)", 0)
    slope_pct = ask("Runway slope [%] (+ = uphill)", 0)
    wet = input("  Runway wet? (y/n, default n): ").strip().lower() == "y"
    use_reverse = True
    if isinstance(acft, JetAircraft) and acft.rev_thrust_ratio > 0:
        use_reverse = input("  Use reverse thrust? (y/n, default y): ").strip().lower() != "n"

    result = landing(acft, elev_m=ft_to_m(elev_ft), isa_dev_c=isa_dev_c,
                     mass_kg=lb_to_kg(mass_lb), hw_kt=hw_kt, use_reverse=use_reverse,
                     slope_pct=slope_pct, rwy_condition="wet" if wet else "dry")
    print_landing(result)
    return result
