"""
Module:   bfl
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Balanced field length and certified takeoff field length for multi-engine
    aircraft. For each trial V1, an engine fails and the model computes both
    outcomes: continue the takeoff on the remaining engines (accelerate-go) or
    reject it and brake to a stop (accelerate-stop). The V1 where the two are
    equal gives the BFL, and TOFL = max(BFL, 1.15 x all-engines TOD).

Basis:
    Torenbeek; Mair & Birdsall; Airbus, Getting to Grips with Aircraft Performance
    14 CFR 25.107, 25.109, 25.111, 25.113; CAR 525
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

from aircraft import Aircraft
from segments import make_conditions, accelerate, climb_to_screen, decelerate
from takeoff import takeoff, takeoff_speeds, rotation_distance, ask
from units import ft_to_m, m_to_ft, mps_to_kt, lb_to_kg, kg_to_lb
from plot_style import (use_style, style_axes, add_metres_axis, stack_tables, align_layout,
                        figure_title, footnote, title_case, BLUE, ORANGE, INK, INK_3, LIMIT_RED)

STOP_DELAY_S = 2.0         # pilot recognition and reaction allowance, [14CFR25] §25.109
AEO_TOD_FACTOR = 1.15      # [14CFR25] §25.113
V1_MIN_FRACTION = 0.5      # stands in for VMCG, which the model does not compute


def accelerate_go(acft: Aircraft, cond, v1_mps):
    """Engine fails at V1, takeoff continues. Returns (distance to 35 ft, OEI gradient %)."""
    vs1_mps, vr_mps, _ = takeoff_speeds(acft, cond)
    oei = acft.n_engines - 1

    dist_v1_m, _, _ = accelerate(acft, cond, v1_mps)
    dist_vr_m, _, _ = accelerate(acft, cond, vr_mps, gs_start_mps=v1_mps - cond.hw_mps,
                                 dist_start_m=dist_v1_m, engines_operating=oei)
    dist_lof_m = dist_vr_m + rotation_distance(acft, cond, vr_mps)
    air_dist_m, climb_grad_pct = climb_to_screen(acft, cond, vs1_mps,
                                                 acft.TAKEOFF_SCREEN_HEIGHT_FT,
                                                 engines_operating=oei)
    return dist_lof_m + air_dist_m, climb_grad_pct


def accelerate_stop(acft: Aircraft, cond, v1_mps):
    """Engine fails at V1, takeoff rejected. Returns the distance to a full stop [m]."""
    dist_v1_m, _, _ = accelerate(acft, cond, v1_mps)
    gs_v1_mps = v1_mps - cond.hw_mps
    dist_brake_start_m = dist_v1_m + gs_v1_mps * STOP_DELAY_S
    # Reverse thrust is not credited on a dry runway, [14CFR25] §25.109.
    dist_stop_m, _, _ = decelerate(acft, cond, gs_v1_mps, dist_brake_start_m,
                                   use_reverse=False)
    return dist_stop_m


def balanced_field(acft: Aircraft, elev_m=0.0, isa_dev_c=0.0, mass_kg=None, hw_kt=0.0,
                   slope_pct=0.0, rwy_condition="dry", n_curve_points=25):
    """
    Balanced field length and takeoff field length. Same inputs as takeoff().
    Also returns the go and stop curves so plot_bfl() can draw them.
    """
    if acft.n_engines < 2:
        raise ValueError(f"{acft.name} has one engine: balanced field length doesn't apply.")

    mass_kg = acft.mtow_kg if mass_kg is None else mass_kg
    cond = make_conditions(acft, mass_kg, elev_m, isa_dev_c, hw_kt, slope_pct, rwy_condition)
    vs1_mps, vr_mps, v2_mps = takeoff_speeds(acft, cond)

    def go_minus_stop(v1_mps):
        return accelerate_go(acft, cond, v1_mps)[0] - accelerate_stop(acft, cond, v1_mps)

    # Going gets shorter and stopping gets longer as V1 rises, so go - stop
    # changes sign once. Brent's method finds that crossing without needing a
    # derivative, which would be expensive here (each call runs the ODE solver).
    v1_low_mps = max(V1_MIN_FRACTION * vr_mps, cond.hw_mps + 1.0)
    v1_high_mps = vr_mps                             # V1 may not exceed VR, §25.107
    diff_low_m = go_minus_stop(v1_low_mps)
    diff_high_m = go_minus_stop(v1_high_mps)

    if diff_low_m > 0 and diff_high_m < 0:
        v1_mps = brentq(go_minus_stop, v1_low_mps, v1_high_mps, xtol=0.01)
        balance_note = "balanced"
    elif diff_high_m >= 0:
        v1_mps = v1_high_mps
        balance_note = "unbalanced: V1 limited to VR (go-limited)"
    else:
        v1_mps = v1_low_mps
        balance_note = "unbalanced: V1 at search minimum (stop-limited)"

    todg_oei_m, oei_climb_grad_pct = accelerate_go(acft, cond, v1_mps)
    asd_m = accelerate_stop(acft, cond, v1_mps)
    bfl_m = max(todg_oei_m, asd_m)

    aeo = takeoff(acft, elev_m, isa_dev_c, mass_kg, hw_kt, slope_pct, rwy_condition)
    tod_aeo_factored_m = AEO_TOD_FACTOR * aeo["tod_m"]
    tofl_m = max(bfl_m, tod_aeo_factored_m)
    tofl_limit = "OEI (balanced field)" if bfl_m >= tod_aeo_factored_m else "AEO × 1.15"

    v1_curve_mps = np.linspace(v1_low_mps, v1_high_mps, n_curve_points)
    go_curve_m = np.array([accelerate_go(acft, cond, v)[0] for v in v1_curve_mps])
    stop_curve_m = np.array([accelerate_stop(acft, cond, v) for v in v1_curve_mps])

    return {
        "acft_name": acft.name,
        "mass_kg": mass_kg,
        "elev_m": elev_m,
        "isa_dev_c": isa_dev_c,
        "hw_kt": hw_kt,
        "slope_pct": slope_pct,
        "rwy_condition": rwy_condition,
        "vs1_mps": vs1_mps,
        "v1_mps": v1_mps,
        "vr_mps": vr_mps,
        "v2_mps": v2_mps,
        "balance_note": balance_note,
        "todg_oei_m": todg_oei_m,
        "asd_m": asd_m,
        "bfl_m": bfl_m,
        "oei_climb_grad_pct": oei_climb_grad_pct,
        "tod_aeo_m": aeo["tod_m"],
        "tod_aeo_factored_m": tod_aeo_factored_m,
        "tofl_m": tofl_m,
        "tofl_limit": tofl_limit,
        "v1_curve_mps": v1_curve_mps,
        "go_curve_m": go_curve_m,
        "stop_curve_m": stop_curve_m,
    }


def print_bfl(result):
    print(f"\n=== Balanced field length: {result['acft_name']} ({result['mass_kg']:,.0f} kg) ===")
    print(f"  V1 (decision)          : {mps_to_kt(result['v1_mps']):7.1f} KTAS  ({result['balance_note']})")
    print(f"  VR (rotation)          : {mps_to_kt(result['vr_mps']):7.1f} KTAS")
    print(f"  V2 (climb)             : {mps_to_kt(result['v2_mps']):7.1f} KTAS")
    print(f"  Accelerate-go (OEI)    : {m_to_ft(result['todg_oei_m']):7.0f} ft")
    print(f"  Accelerate-stop        : {m_to_ft(result['asd_m']):7.0f} ft")
    print(f"  BFL                    : {m_to_ft(result['bfl_m']):7.0f} ft  ({result['bfl_m']:.0f} m)")
    print(f"  OEI climb gradient @V2 : {result['oei_climb_grad_pct']:7.1f} %  (gear down, to 35 ft)")
    print(f"  AEO TOD × 1.15         : {m_to_ft(result['tod_aeo_factored_m']):7.0f} ft  "
          f"(AEO TOD {m_to_ft(result['tod_aeo_m']):,.0f} ft)")
    print(f"  TOFL (takeoff field)   : {m_to_ft(result['tofl_m']):7.0f} ft  ({result['tofl_m']:.0f} m)"
          f"  (limited by {result['tofl_limit']})")


def conditions_rows(result):
    elev_txt = "Sea Level" if result["elev_m"] < 1 else f"{m_to_ft(result['elev_m']):,.0f} ft"
    isa_txt = "0 °C" if abs(result["isa_dev_c"]) < 0.5 else f"{result['isa_dev_c']:+.0f} °C"
    if abs(result["hw_kt"]) < 0.5:
        wind_txt = "Calm"
    elif result["hw_kt"] > 0:
        wind_txt = f"{result['hw_kt']:.0f} kt Head"
    else:
        wind_txt = f"{-result['hw_kt']:.0f} kt Tail"
    return [
        ("Takeoff Weight", f"{kg_to_lb(result['mass_kg']):,.0f} lb"),
        ("Field Elevation", elev_txt),
        ("Standard Atmosphere (ISA) Deviation", isa_txt),
        ("Wind Component (Factored)" if result.get("wind_factored") else "Wind Component", wind_txt),
        ("Runway Surface", result["rwy_condition"].title()),
        ("Runway Slope", f"{result['slope_pct']:+.2f} %"),
    ]


def plot_bfl(result, filename=None, runway=None, extra_conditions=None):
    """
    Go and stop distance against V1, with a conditions and results sidebar.
    Pass a Runway to draw its TODA / ASDA limit lines.
    """
    use_style()
    v1_kt = mps_to_kt(result["v1_curve_mps"])
    go_ft = m_to_ft(result["go_curve_m"])
    stop_ft = m_to_ft(result["stop_curve_m"])
    v1_bal_kt = mps_to_kt(result["v1_mps"])
    vr_kt = mps_to_kt(result["vr_mps"])
    bfl_ft = m_to_ft(result["bfl_m"])
    aeo_ft = m_to_ft(result["tod_aeo_factored_m"])
    tofl_ft = m_to_ft(result["tofl_m"])
    aeo_limits = tofl_ft > bfl_ft + 0.5

    fig = plt.figure(figsize=(13, 7.2))
    grid = fig.add_gridspec(1, 2, width_ratios=[2.6, 1], left=0.075, right=0.975,
                            top=0.88, bottom=0.13, wspace=0.16)
    ax = fig.add_subplot(grid[0, 0])
    ax_side = fig.add_subplot(grid[0, 1])
    title_text = figure_title(fig, f"{result['acft_name']} – Balanced Field Length (BFL)")

    # Curves, labelled directly
    ax.plot(v1_kt, go_ft, color=BLUE, lw=2.4, zorder=3)
    ax.plot(v1_kt, stop_ft, color=ORANGE, lw=2.4, zorder=3)
    i_go = len(v1_kt) // 5
    ax.annotate(title_case("accelerate-go"), (v1_kt[i_go], go_ft[i_go]), xytext=(0, 30),
                textcoords="offset points", fontsize=10, fontweight="bold", color=BLUE)
    ax.annotate("Engine fails at V1, takeoff continues to 35 ft",
                (v1_kt[i_go], go_ft[i_go]), xytext=(0, 16), textcoords="offset points",
                fontsize=8, color=BLUE)
    i_stop = len(v1_kt) * 2 // 5
    ax.annotate(title_case("accelerate-stop"), (v1_kt[i_stop], stop_ft[i_stop]), xytext=(10, -16),
                textcoords="offset points", fontsize=10, fontweight="bold", color=ORANGE, va="top")
    ax.annotate("Engine fails at V1, takeoff rejected", (v1_kt[i_stop], stop_ft[i_stop]),
                xytext=(10, -31), textcoords="offset points", fontsize=8, color=ORANGE, va="top")

    # All Engines Operating (AEO) × 1.15 reference
    ax.axhline(aeo_ft, color=INK if aeo_limits else INK_3, lw=1, ls=(0, (6, 4)), zorder=2)
    aeo_label = "All Engines Operating (AEO) × 1.15"
    if aeo_limits:
        aeo_label += f"  =  Takeoff Field Length (TOFL) {tofl_ft:,.0f} ft"
    ax.text(v1_kt[0], aeo_ft, " " + aeo_label, color=INK if aeo_limits else INK_3, fontsize=8,
            va="bottom", fontweight="bold" if aeo_limits else "normal")

    # Runway limit (optional)
    limits_ft = [go_ft.max(), stop_ft.max(), aeo_ft]
    if runway is not None:
        if abs(runway.toda_m - runway.asda_m) < 1:
            limits = [("Runway Available (TODA = ASDA)", runway.toda_m)]
        else:
            limits = [("Takeoff Distance Available (TODA)", runway.toda_m),
                      ("Accelerate-Stop Distance Available (ASDA)", runway.asda_m)]
        for name, dist_m in limits:
            ax.axhline(m_to_ft(dist_m), color=LIMIT_RED, lw=1.1, ls=(0, (2, 2)), zorder=2)
            ax.text(v1_kt[0], m_to_ft(dist_m), f" {name}  {m_to_ft(dist_m):,.0f} ft",
                    color=LIMIT_RED, fontsize=8, va="bottom", fontweight="bold")
            limits_ft.append(m_to_ft(dist_m))

    # Balanced point, V1 and VR
    y_top = max(limits_ft) * 1.10
    y_bottom = min(go_ft.min(), stop_ft.min()) * 0.80
    ax.set_ylim(y_bottom, y_top)
    ax.axvline(v1_bal_kt, color=INK, lw=0.9, ls=(0, (4, 3)), zorder=1)
    ax.axvline(vr_kt, color=INK_3, lw=0.9, ls=":", zorder=1)
    ax.plot([v1_bal_kt], [bfl_ft], "o", ms=8, color=INK, mec="white", mew=2, zorder=5)
    ax.annotate(f"BFL {bfl_ft:,.0f} ft", (v1_bal_kt, bfl_ft), xytext=(-10, 0),
                textcoords="offset points", ha="right", va="center", fontsize=9,
                color=INK, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.9))
    ax.text(v1_bal_kt, y_top, f" V1 {v1_bal_kt:.0f}", ha="left", va="top", fontsize=8.5,
            color=INK, fontweight="bold")
    ax.text(vr_kt, y_top, f" VR {vr_kt:.0f}", ha="left", va="top", fontsize=8.5, color=INK_3)

    style_axes(ax, xlabel="decision speed V1 – knots true airspeed (KTAS)",
               ylabel="distance (ft)")
    ax.set_xlim(v1_kt[0] - 2, vr_kt + 6)
    add_metres_axis(ax)

    foot = footnote(fig, "All speeds are true airspeed. "
                    "TOFL = max(BFL, 1.15 × AEO takeoff distance), CAR 525 / 14 CFR 25.113.")
    align_layout(fig, [ax], ax_side, title_text, foot)

    # Sidebar: Conditions, then Results (drawn after alignment)
    wide = [0.74, 0.26]
    stack_tables(ax_side, [
        dict(heading="Conditions", rows=list(extra_conditions or []) + conditions_rows(result)),
        dict(heading="Takeoff Speeds (KTAS)", col_widths=wide, rows=[
            ("Decision Speed (V1)", f"{v1_bal_kt:.0f}"),
            ("Rotation Speed (VR)", f"{vr_kt:.0f}"),
            ("Takeoff Safety Speed (V2)", f"{mps_to_kt(result['v2_mps']):.0f}"),
        ]),
        dict(heading="Distances", col_widths=wide, rows=[
            ("Balanced Field Length (BFL)", f"{bfl_ft:,.0f} ft"),
            ("All Engines Operating (AEO) × 1.15", f"{aeo_ft:,.0f} ft"),
            ("Takeoff Field Length (TOFL)", f"{tofl_ft:,.0f} ft"),
            ("TOFL Limited By", "AEO × 1.15" if aeo_limits else "BFL"),
            ("One Engine Inoperative (OEI) Gradient", f"{result['oei_climb_grad_pct']:.1f} %"),
        ]),
    ])

    if filename is None:
        filename = f"bfl_{result['acft_name'].replace(' ', '_')}.png"
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    return filename


def run_bfl_interactive(acft: Aircraft):
    if acft.n_engines < 2:
        print(f"\n  {acft.name} has one engine: balanced field length doesn't apply.")
        return None
    print(f"\n--- Balanced field conditions for {acft.name} ---")
    elev_ft = ask("Field elevation [ft]", 0)
    isa_dev_c = ask("ISA deviation [°C]", 0)
    mass_lb = ask("Takeoff weight [lb]", round(kg_to_lb(acft.mtow_kg)))
    hw_kt = ask("Headwind [kt] (negative = tailwind)", 0)
    slope_pct = ask("Runway slope [%] (+ = uphill)", 0)
    wet = input("  Runway wet? (y/n, default n): ").strip().lower() == "y"

    result = balanced_field(acft, elev_m=ft_to_m(elev_ft), isa_dev_c=isa_dev_c,
                            mass_kg=lb_to_kg(mass_lb), hw_kt=hw_kt, slope_pct=slope_pct,
                            rwy_condition="wet" if wet else "dry")
    print_bfl(result)
    print(f"  Saved plot: {plot_bfl(result)}")
    return result
