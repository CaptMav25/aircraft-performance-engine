"""
Module:   sensitivity
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Sweeps elevation, temperature, weight and wind one at a time and plots the
    effect on takeoff distance (TOFL for twins, TOD for singles) and landing
    distance in a 2 x 2 figure with a summary table.
"""

import numpy as np
import matplotlib.pyplot as plt

from plot_style import (use_style, style_axes, add_metres_axis, stack_tables, align_layout,
                        figure_title, BLUE as TO_COLOR, ORANGE as LD_COLOR, INK_3)

from aircraft import Aircraft
from takeoff import takeoff
from landing import landing
from bfl import balanced_field
from units import ft_to_m, m_to_ft, kg_to_lb

# Each sweep moves one input; the rest stay at sea level, ISA, max weight, calm.
SWEEPS = {
    "elev_ft": np.linspace(0, 8000, 17),
    "isa_dev_c": np.linspace(-20, 30, 11),
    "weight_pct": np.linspace(70, 100, 13),
    "hw_kt": np.linspace(-10, 20, 16),
}

PANELS = {
    "elev_ft":    ("Field Elevation", "Pressure Altitude (ft)"),
    "isa_dev_c":  ("Temperature", "International Standard Atmosphere (ISA) Deviation (°C)"),
    "weight_pct": ("Weight", "Weight (% of MTOW for Takeoff, % of MLW for Landing)"),
    "hw_kt":      ("Wind", "Headwind Component (kt)"),
}


def takeoff_metric_m(acft: Aircraft, **conditions):
    # A twin is limited by TOFL (engine failure case); a single has only TOD.
    if acft.n_engines >= 2:
        return balanced_field(acft, n_curve_points=2, **conditions)["tofl_m"]
    return takeoff(acft, **conditions)["tod_m"]


def landing_metric_m(acft: Aircraft, **conditions):
    return landing(acft, use_reverse=False, **conditions)["ld_m"]


def takeoff_label(acft: Aircraft):
    return "TOFL" if acft.n_engines >= 2 else "TOD"


def run_sweeps(acft: Aircraft):
    results = {}
    sweeps = {
        "elev_ft":    lambda x: {"elev_m": ft_to_m(x)},
        "isa_dev_c":  lambda x: {"isa_dev_c": x},
        "weight_pct": None,          # % of MTOW for takeoff but % of MLW for landing
        "hw_kt":      lambda x: {"hw_kt": x},
    }
    for key, to_conditions in sweeps.items():
        x_values = SWEEPS[key]
        if key == "weight_pct":
            to_m = [takeoff_metric_m(acft, mass_kg=acft.mtow_kg * pct / 100) for pct in x_values]
            ld_m = [landing_metric_m(acft, mass_kg=acft.mlw_kg * pct / 100) for pct in x_values]
        else:
            to_m = [takeoff_metric_m(acft, **to_conditions(x)) for x in x_values]
            ld_m = [landing_metric_m(acft, **to_conditions(x)) for x in x_values]
        results[key] = (x_values, m_to_ft(np.array(to_m)), m_to_ft(np.array(ld_m)))
    return results


def plot_sensitivity(acft: Aircraft, results, filename=None):
    use_style()
    is_multi = acft.n_engines >= 2
    to_abbr = takeoff_label(acft)
    to_name = "Takeoff Field Length (TOFL)" if is_multi else "Takeoff Distance (TOD)"
    base_x = {"elev_ft": 0, "isa_dev_c": 0, "weight_pct": 100, "hw_kt": 0}

    fig = plt.figure(figsize=(15, 9.4))
    outer = fig.add_gridspec(1, 2, width_ratios=[3.2, 1], left=0.075, right=0.975,
                             top=0.88, bottom=0.10, wspace=0.12)
    charts = outer[0, 0].subgridspec(2, 2, hspace=0.42, wspace=0.30)
    axes = [fig.add_subplot(charts[i, j]) for i in range(2) for j in range(2)]
    ax_side = fig.add_subplot(outer[0, 1])
    title_text = figure_title(fig, f"{acft.name} – Takeoff & Landing Sensitivity")

    for ax, key in zip(axes, PANELS):
        x_values, to_ft, ld_ft = results[key]
        title, xlabel = PANELS[key]
        x0 = base_x[key]
        i0 = int(np.argmin(np.abs(x_values - x0)))

        if key == "hw_kt":
            ax.axvspan(x_values[0], 0, color="#f3e3dc", alpha=0.6, lw=0, zorder=0)
            ax.text(x_values[0], 1.0, " Tailwind", transform=ax.get_xaxis_transform(),
                    va="top", fontsize=7.5, color=INK_3)
        if key == "isa_dev_c" and is_multi and hasattr(acft, "flat_rating_isa_c"):
            ax.axvline(acft.flat_rating_isa_c, color=INK_3, lw=0.9, ls=":")
            ax.text(acft.flat_rating_isa_c, 1.0, f" Flat Rating ISA +{acft.flat_rating_isa_c:.0f}",
                    transform=ax.get_xaxis_transform(), va="top", fontsize=7.5, color=INK_3)

        ax.axvline(x0, color=INK_3, lw=0.8, ls=(0, (4, 3)), zorder=1)
        y_all = np.concatenate([to_ft, ld_ft])
        pad = 0.12 * (y_all.max() - y_all.min())
        min_gap = 0.16 * (y_all.max() - y_all.min() + 2 * pad)

        for y_values, color in ((to_ft, TO_COLOR), (ld_ft, LD_COLOR)):
            ax.plot(x_values, y_values, color=color, lw=2.2, zorder=3)
            ax.plot([x_values[i0]], [y_values[i0]], "o", ms=6, color=color,
                    mec="white", mew=1.5, zorder=4)

        # Push the two end labels apart if they would overlap.
        for i_end, ha, dx in ((0, "right", -6), (-1, "left", 6)):
            if abs(x_values[i_end] - x0) < 1e-9:
                continue
            y_to, y_ld = to_ft[i_end], ld_ft[i_end]
            label_y = {"to": y_to, "ld": y_ld}
            if abs(y_to - y_ld) < min_gap:
                mid = (y_to + y_ld) / 2
                upper, lower = ("to", "ld") if y_to >= y_ld else ("ld", "to")
                label_y[upper] = mid + min_gap / 2
                label_y[lower] = mid - min_gap / 2
            for name, y_values, color in (("to", to_ft, TO_COLOR), ("ld", ld_ft, LD_COLOR)):
                pct = 100 * (y_values[i_end] / y_values[i0] - 1)
                x_text = x_values[i_end] + np.sign(dx) * 0.015 * (x_values[-1] - x_values[0])
                ax.text(x_text, label_y[name], f"{y_values[i_end]:,.0f} ft\n{pct:+.0f}%",
                        ha=ha, va="center", fontsize=7.5, color=color, linespacing=1.2)

        style_axes(ax, title=title, xlabel=xlabel, ylabel="distance (ft)")
        span = x_values[-1] - x_values[0]
        ax.set_xlim(x_values[0] - 0.16 * span, x_values[-1] + 0.16 * span)
        ax.set_ylim(y_all.min() - pad, y_all.max() + pad)
        add_metres_axis(ax, label="m")

    align_layout(fig, axes, ax_side, title_text)

    # The sidebar is drawn after align_layout so the tables line up with the plots.
    base_to_ft = m_to_ft(takeoff_metric_m(acft))
    base_ld_ft = m_to_ft(landing_metric_m(acft))
    change_rows = [
        ("Elevation 0 to 8,000 ft", "elev_ft", -1),
        ("Hot Day, ISA +30 °C", "isa_dev_c", -1),
        ("Weight 100% to 70%", "weight_pct", 0),
        ("20 kt Headwind", "hw_kt", -1),
        ("10 kt Tailwind", "hw_kt", 0),
    ]
    summary = []
    for text, key, idx in change_rows:
        _, to_ft, ld_ft = results[key]
        summary.append((text, f"{100 * (to_ft[idx] / base_to_ft - 1):+.0f}%",
                        f"{100 * (ld_ft[idx] / base_ld_ft - 1):+.0f}%"))
    stack_tables(ax_side, [
        dict(heading="Baseline Conditions", col_widths=[0.62, 0.38], rows=[
            ("Aircraft", acft.name),
            ("Max Takeoff Weight (MTOW)", f"{kg_to_lb(acft.mtow_kg):,.0f} lb"),
            ("Max Landing Weight (MLW)", f"{kg_to_lb(acft.mlw_kg):,.0f} lb"),
            ("Field Elevation", "Sea Level"),
            ("Standard Atmosphere (ISA) Deviation", "0 °C"),
            ("Wind", "Calm"),
            ("Runway", "Dry, Level"),
        ]),
        dict(heading="Legend", col_widths=[0.74, 0.26], swatches=[TO_COLOR, LD_COLOR], rows=[
            (to_name, f"{base_to_ft:,.0f} ft"),
            ("Landing Distance (LD)", f"{base_ld_ft:,.0f} ft"),
        ]),
        dict(heading="Change From Baseline", rows=summary,
             col_headers=["Change", to_abbr, "LD"], col_widths=[0.56, 0.22, 0.22]),
    ])

    if filename is None:
        filename = f"sensitivity_{acft.name.replace(' ', '_')}.png"
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    return filename


def print_summary(acft: Aircraft, results):
    base_to_ft = m_to_ft(takeoff_metric_m(acft))
    base_ld_ft = m_to_ft(landing_metric_m(acft))
    to_name = takeoff_label(acft)
    print(f"\n=== {acft.name}: sensitivity summary ===")
    print(f"  Baseline: {to_name} {base_to_ft:,.0f} ft, LD {base_ld_ft:,.0f} ft\n")
    print(f"  {'Change':<26} {to_name:>10} {'LD':>10}")
    rows = [
        ("Elevation 0 to 8,000 ft", "elev_ft", -1),
        ("Hot day, ISA+30", "isa_dev_c", -1),
        ("Weight 100% to 70%", "weight_pct", 0),
        ("20 kt headwind", "hw_kt", -1),
        ("10 kt tailwind", "hw_kt", 0),
    ]
    for text, key, idx in rows:
        _, to_ft, ld_ft = results[key]
        print(f"  {text:<26} {100 * (to_ft[idx] / base_to_ft - 1):>+9.0f}% "
              f"{100 * (ld_ft[idx] / base_ld_ft - 1):>+9.0f}%")
