"""
Module:   make_examples
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Writes the worked-example sections of the LaTeX report from the model
    itself, so every number in the report matches the code.

Run:
    python3 report/make_examples.py
    then compile report/performance_model.tex with pdflatex (three passes)
"""

import re
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # project folder

from aircraft import CL3500, SR22T, JetAircraft, PropAircraft
from airports import KICT, wind_components
from atmosphere import (isa, sigma, speed_of_sound, TEMP_SL_K, PRESS_SL_PA, RHO_SL_KG_M3,
                        LAPSE_RATE_K_PER_M, R_AIR, G0_MPS2, GAMMA_AIR)
from bfl import balanced_field, accelerate_go, accelerate_stop, plot_bfl, STOP_DELAY_S
from landing import landing, GLIDESLOPE_DEG, VREF_FACTOR, VTD_FACTOR
from runway_analysis import factored_headwind, isa_dev_from_oat
from segments import (make_conditions, TRANSITION_LOAD_FACTOR, V_TR_FACTOR)
from takeoff import takeoff, VR_FACTOR, V2_FACTOR
from units import ft_to_m, m_to_ft, mps_to_kt, kg_to_lb, k_to_c, n_to_lbf, w_to_hp, m2_to_ft2

# ---- Example conditions (the same for both aircraft) ----
AIRPORT = KICT
RUNWAY = KICT.runway("01L")
OAT_C = 30.0
WIND_DIR_DEG = 20.0
WIND_KT = 10.0
RWY_CONDITION = "dry"


# Formatting helpers

def captions_below(tex):
    """Move each table caption under its table (IEEE style)."""
    def move(match):
        body = match.group(0)
        cap = re.search(r"^(\\caption\{.*?\}(?:\\label\{[^}]*\})?)\n", body, re.M)
        if not cap:
            return body
        body = body[:cap.start()] + body[cap.end():]
        return body.replace(r"\end{table}", cap.group(1) + r"\end{table}")
    return re.sub(r"\\begin\{table\}.*?\\end\{table\}", move, tex, flags=re.S)

def N(x, d=0):
    """Number for LaTeX math/text via siunitx."""
    return rf"\num{{{x:.{d}f}}}"


def Q(x, unit, d=0):
    """Quantity with unit via siunitx."""
    return rf"\SI{{{x:.{d}f}}}{{{unit}}}"


def ft(x_m, d=0):
    return Q(m_to_ft(x_m), "ft", d)


def kt(v_mps, d=1):
    return Q(mps_to_kt(v_mps), "kt", d)


# Example generator
def example(acft, label):
    """Return the LaTeX for one worked example."""
    out = []
    w = out.append
    is_jet = isinstance(acft, JetAircraft)
    multi = acft.n_engines >= 2

    # ---------------------------------------------------------------- inputs
    elev_m = AIRPORT.elev_m
    isa_dev_c = isa_dev_from_oat(elev_m, OAT_C)
    hw_kt, xw_kt = wind_components(WIND_DIR_DEG, WIND_KT, RUNWAY.hdg_true_deg)
    hw_perf_kt = factored_headwind(hw_kt)
    slope_pct = RUNWAY.slope_pct
    tow_kg, lw_kg = acft.mtow_kg, acft.mlw_kg

    w(rf"\subsection{{Inputs}}")
    w(rf"Table~\ref{{tab:in-{label}}} lists the aircraft data and the day's conditions. "
      rf"The example uses {AIRPORT.name} ({AIRPORT.icao}) runway {RUNWAY.rwy_id}.")
    rows = [
        ("Maximum takeoff weight (MTOW)", f"{Q(kg_to_lb(tow_kg), 'lb')} = {Q(tow_kg, 'kg', 1)}"),
        ("Maximum landing weight (MLW)", f"{Q(kg_to_lb(lw_kg), 'lb')} = {Q(lw_kg, 'kg', 1)}"),
        ("Reference wing area, $S$", f"{Q(acft.s_ref_m2, 'm^2', 2)} ({Q(m2_to_ft2(acft.s_ref_m2), 'ft^2', 1)})"),
        ("$C_{D_0}$ / $k$", f"{N(acft.cd0, 3)} / {N(acft.k_induced, 3)}"),
        ("$C_{L,\\max}$ takeoff / landing", f"{N(acft.cl_max_to, 2)} / {N(acft.cl_max_ldg, 2)}"),
        ("$C_{L,\\text{gnd}}$", N(acft.cl_gnd, 2)),
        ("$\\mu_\\text{roll}$ / $\\mu_\\text{brake}$", f"{N(acft.mu_roll, 2)} / {N(acft.mu_brake, 2)}"),
        ("Sea-level static thrust, $T_\\text{SLS}$", f"{Q(acft.sls_thrust_n, 'N')} ({Q(n_to_lbf(acft.sls_thrust_n), 'lbf')})"),
        ("Number of engines, $N_e$", str(acft.n_engines)),
    ]
    if is_jet:
        rows += [("Thrust lapse, $k_\\text{lapse}$", N(acft.thrust_lapse, 2)),
                 ("Flat rating, $\\Delta T_\\text{flat}$", f"ISA {Q(acft.flat_rating_isa_c, 'degreeCelsius', 0)}"),
                 ("Reverse thrust ratio", N(acft.rev_thrust_ratio, 2))]
    else:
        rows += [("Maximum power, $P_\\text{max}$", f"{Q(acft.max_power_w / 1000, 'kW', 1)} ({Q(w_to_hp(acft.max_power_w), 'hp')})"),
                 ("Propeller efficiency, $\\eta_p$", N(acft.eta_prop, 2)),
                 ("Turbocharger critical altitude", f"{Q(m_to_ft(acft.critical_alt_m), 'ft')}" if acft.critical_alt_m else "none")]
    rows += [
        ("Field elevation, $h$", f"{Q(m_to_ft(elev_m), 'ft')} = {Q(elev_m, 'm', 1)}"),
        ("Outside air temperature (OAT)", Q(OAT_C, "degreeCelsius")),
        ("Reported wind", f"\\ang{{{WIND_DIR_DEG:.0f}}} / {Q(WIND_KT, 'kt')}"),
        ("Runway true heading", f"\\ang{{{RUNWAY.hdg_true_deg:.0f}}}"),
        ("Runway slope (direction of travel)", f"{N(slope_pct, 3)}\\,\\%"),
        ("Runway condition", RWY_CONDITION.title()),
        ("TODA = ASDA / LDA", f"{ft(RUNWAY.toda_m)} / {ft(RUNWAY.lda_m)}"),
    ]
    w(r"\begin{table}[H]\centering\small")
    w(rf"\caption{{{acft.name}: example inputs.}}\label{{tab:in-{label}}}")
    w(r"\begin{tabular}{@{}ll@{}}\toprule \textbf{Input} & \textbf{Value}\\\midrule")
    for name, value in rows:
        w(rf"{name} & {value}\\")
    w(r"\bottomrule\end{tabular}\end{table}")

    # ---------------------------------------------------------------- atmosphere
    temp_std_k = TEMP_SL_K - LAPSE_RATE_K_PER_M * elev_m
    temp_k, press_pa, rho = isa(elev_m, isa_dev_c)
    sig = sigma(elev_m, isa_dev_c)
    a_mps = speed_of_sound(elev_m, isa_dev_c)
    expo = G0_MPS2 / (LAPSE_RATE_K_PER_M * R_AIR)
    w(r"\subsection{Step 1: Atmosphere}")
    w(r"Standard temperature at the field elevation, then the ISA deviation from the OAT "
      r"(\eqref{eq:isa-temp} and \eqref{eq:isa-dev}):")
    w(r"\begin{align*}")
    w(rf"\Theta_\text{{std}} &= {N(TEMP_SL_K, 2)} - {N(LAPSE_RATE_K_PER_M, 4)}\times{N(elev_m, 1)} = {Q(temp_std_k, 'K', 2)}\\")
    w(rf"\Delta T &= {N(OAT_C, 1)} - ({N(temp_std_k, 2)} - {N(273.15, 2)}) = {Q(isa_dev_c, 'degreeCelsius', 2)}"
      rf"\quad\text{{(ISA }}{isa_dev_c:+.1f}\text{{)}}")
    w(r"\end{align*}")
    w(r"Pressure, temperature, density, density ratio and speed of sound (\eqref{eq:isa-p}--\eqref{eq:isa-a}):")
    w(r"\begin{align*}")
    w(rf"p &= {N(PRESS_SL_PA)}\left(\frac{{{N(temp_std_k, 2)}}}{{{N(TEMP_SL_K, 2)}}}\right)^{{{N(expo, 4)}}} = {Q(press_pa, 'Pa', 0)}\\")
    w(rf"\Theta &= {N(temp_std_k, 2)} + {N(isa_dev_c, 2)} = {Q(temp_k, 'K', 2)}\\")
    w(rf"\rho &= \frac{{{N(press_pa)}}}{{{N(R_AIR, 2)}\times{N(temp_k, 2)}}} = {Q(rho, 'kg/m^3', 4)}\\")
    w(rf"\sigma &= \frac{{{N(rho, 4)}}}{{{N(RHO_SL_KG_M3, 3)}}} = {N(sig, 4)}\\")
    w(rf"a &= \sqrt{{{N(GAMMA_AIR, 1)}\times{N(R_AIR, 2)}\times{N(temp_k, 2)}}} = {Q(a_mps, 'm/s', 1)}")
    w(r"\end{align*}")

    # ---------------------------------------------------------------- wind
    w(r"\subsection{Step 2: Wind}")
    w(r"Runway components (\eqref{eq:wind-hw}--\eqref{eq:wind-xw}), then the regulatory factor \eqref{eq:wind-perf}:")
    w(r"\begin{align*}")
    w(rf"V_w &= {N(WIND_KT)}\cos(\ang{{{WIND_DIR_DEG:.0f}}} - \ang{{{RUNWAY.hdg_true_deg:.0f}}}) = {Q(hw_kt, 'kt', 1)}"
      rf"\qquad V_x = {N(WIND_KT)}\sin(\ang{{{WIND_DIR_DEG - RUNWAY.hdg_true_deg:.0f}}}) = {Q(abs(xw_kt), 'kt', 1)}\\")
    factor = 0.5 if hw_kt >= 0 else 1.5
    w(rf"V_{{w,\text{{perf}}}} &= {N(factor, 1)}\times{N(hw_kt, 1)} = {Q(hw_perf_kt, 'kt', 1)} = {Q(hw_perf_kt * 0.514444, 'm/s', 2)}")
    w(r"\end{align*}")
    w(rf"All following steps use the performance headwind of {Q(hw_perf_kt, 'kt', 1)}.")

    # ---------------------------------------------------------------- speeds
    cond = make_conditions(acft, tow_kg, elev_m, isa_dev_c, hw_perf_kt, slope_pct, RWY_CONDITION)
    weight = cond.weight_n
    vs1 = acft.stall_speed(weight, rho, acft.cl_max_to)
    vr, v2, vtr = VR_FACTOR * vs1, V2_FACTOR * vs1, V_TR_FACTOR * vs1
    w(r"\subsection{Step 3: Weight and Takeoff Speeds}")
    w(r"\begin{align*}")
    w(rf"W &= m\,g_0 = {N(tow_kg, 1)}\times{N(G0_MPS2, 5)} = {Q(weight, 'N')}\\")
    w(rf"V_{{S1}} &= \sqrt{{\frac{{2\times{N(weight)}}}{{{N(rho, 4)}\times{N(acft.s_ref_m2, 2)}\times{N(acft.cl_max_to, 2)}}}}} = {Q(vs1, 'm/s', 2)} = {kt(vs1)}\\")
    w(rf"V_R &= {N(VR_FACTOR, 2)}\,V_{{S1}} = {Q(vr, 'm/s', 2)} = {kt(vr)}\\")
    w(rf"V_2 &= {N(V2_FACTOR, 2)}\,V_{{S1}} = {Q(v2, 'm/s', 2)} = {kt(v2)}\\")
    w(rf"V_\text{{TR}} &= {N(V_TR_FACTOR, 2)}\,V_{{S1}} = {Q(vtr, 'm/s', 2)} = {kt(vtr)}")
    w(r"\end{align*}")

    # ---------------------------------------------------------------- forces
    def forces(tas, engines=None):
        q = 0.5 * rho * tas**2
        L = acft.lift(tas, rho, acft.cl_gnd)
        D = acft.drag(tas, rho, acft.cl_gnd)
        T = acft.thrust(tas, elev_m, isa_dev_c, engines)
        F = acft.mu_roll * max(weight - L, 0)
        G = weight * math.sin(cond.slope_rad)
        acc = (T - D - F - G) / tow_kg
        return q, L, D, T, F, G, acc

    w(r"\subsection{Step 4: Forces on the Ground Roll}")
    if is_jet:
        excess = max(isa_dev_c - acft.flat_rating_isa_c, 0)
        sig_eff = sigma(elev_m, excess)
        w(rf"Thrust (\eqref{{eq:jet-excess}}--\eqref{{eq:T-jet}}). The ISA deviation of {N(isa_dev_c, 1)}\,\si{{\celsius}} exceeds the "
          rf"flat rating by {N(excess, 1)}\,\si{{\celsius}}, so")
        w(r"\begin{gather*}")
        w(rf"\sigma_\text{{eff}} = \sigma\!\left(h,\ {N(excess, 1)}\right) = {N(sig_eff, 4)}\\ "
          rf"T(V) = {N(acft.sls_thrust_n)}\times{N(sig_eff, 4)}^{{0.7}}\left(1 - {N(acft.thrust_lapse, 2)}\,\frac{{V}}{{{N(a_mps, 1)}}}\right)")
        w(r"\end{gather*}")
    else:
        turbo = acft.critical_alt_m > 0 and elev_m <= acft.critical_alt_m
        sig_p = 1.0 if turbo else sig
        w(r"Thrust \eqref{eq:T-prop}" + (", turbocharged below its critical altitude so the power is not reduced "
                                "($\\sigma_P = 1$):" if turbo else ", normally aspirated so $\\sigma_P = \\sigma$:"))
        w(r"\begin{equation*}")
        w(rf"T(V) = \min\left({N(sig_p, 4)}\times{N(acft.sls_thrust_n)},\ "
          rf"\frac{{{N(acft.eta_prop, 2)}\times{N(sig_p, 4)}\times{N(acft.max_power_w)}}}{{V}}\right)")
        w(r"\end{equation*}")
    w(r"\Needspace{16\baselineskip}")
    w(rf"Forces at brake release and at $V_R$ (\eqref{{eq:eom-accel}}, $C_L = C_{{L,\text{{gnd}}}} = {N(acft.cl_gnd, 2)}$, "
      rf"slope force $W\sin\theta$):")
    w(r"\begin{table}[H]\centering\small")
    w(rf"\caption{{{acft.name}: forces on the ground roll.}}")
    w(r"\begin{tabular}{@{}lrr@{}}\toprule \textbf{Quantity} & \textbf{At $V_\text{TAS} = V_w$ (start)} & \textbf{At $V_R$}\\\midrule")
    f0 = forces(cond.hw_mps)
    f1 = forces(vr)
    names = ["Dynamic pressure $q$ (Pa)", "Lift $L$ (N)", "Drag $D$ (N)", "Thrust $T$ (N)",
             "Rolling friction $\\mu_\\text{roll}(W-L)$ (N)", "Slope force $W\\sin\\theta$ (N)",
             "Acceleration $a$ (\\si{m/s^2})"]
    for i, name in enumerate(names):
        d = 3 if i == 6 else (1 if i == 0 else 0)
        w(rf"{name} & {N(f0[i], d)} & {N(f1[i], d)}\\")
    w(r"\bottomrule\end{tabular}\end{table}")

    # ---------------------------------------------------------------- ground roll
    to = takeoff(acft, elev_m, isa_dev_c, tow_kg, hw_perf_kt, slope_pct, RWY_CONDITION)
    t_hist, s_hist, v_hist = to["t_hist_s"], to["dist_hist_m"], to["tas_hist_mps"]
    s_vr = to["ground_roll_m"] - (vr - cond.hw_mps) * acft.ROTATION_S
    t_vr = to["ground_roll_s"] - acft.ROTATION_S
    w(r"\subsection{Step 5: Ground Roll by Numerical Integration}")
    w(r"Equation~\eqref{eq:eom-accel} is integrated with RK45 from rest until $V_\text{TAS} = V_R$. "
      r"Selected points from the solver:")
    w(r"\begin{table}[H]\centering\small")
    w(rf"\caption{{{acft.name}: ground-roll time history (RK45 output).}}")
    w(r"\begin{tabular}{@{}rrrr@{}}\toprule \textbf{$t$ (s)} & \textbf{$V_\text{TAS}$ (kt)} & "
      r"\textbf{$a$ (\si{m/s^2})} & \textbf{$s$ (ft)}\\\midrule")
    n = len(t_hist)
    picks = sorted(set([0] + [round(i * (n - 1) / 6) for i in range(1, 6)]))
    for i in picks:
        acc = forces(v_hist[i])[6]
        w(rf"{N(t_hist[i], 1)} & {N(mps_to_kt(v_hist[i]), 1)} & {N(acc, 3)} & {N(m_to_ft(s_hist[i]))}\\")
    w(rf"\midrule {N(t_vr, 2)} & {N(mps_to_kt(vr), 1)} ($V_R$) & {N(forces(vr)[6], 3)} & {N(m_to_ft(s_vr))}\\")
    w(r"\bottomrule\end{tabular}\end{table}")
    rot = (vr - cond.hw_mps) * acft.ROTATION_S
    w(r"Rotation for $t_\text{rot}$ \eqref{eq:s-rot}:")
    w(r"\begin{align*}")
    w(rf"s_\text{{rot}} &= ({N(vr, 2)} - {N(cond.hw_mps, 2)})\times{N(acft.ROTATION_S, 0)} = {Q(rot, 'm', 1)}\\")
    w(rf"s_\text{{ground}} &= {N(s_vr, 1)} + {N(rot, 1)} = {Q(to['ground_roll_m'], 'm', 1)} = {ft(to['ground_roll_m'])}")
    w(r"\end{align*}")

    # ---------------------------------------------------------------- air distance
    q2 = 0.5 * rho * v2**2
    cl_c = weight / (q2 * acft.s_ref_m2)
    d2 = acft.drag(v2, rho, cl_c)
    t2 = acft.thrust(v2, elev_m, isa_dev_c)
    sg = (t2 - d2) / weight
    gam = math.asin(sg)
    R = vtr**2 / (G0_MPS2 * (TRANSITION_LOAD_FACTOR - 1))
    h_tr = R * (1 - math.cos(gam))
    hs_ft = acft.TAKEOFF_SCREEN_HEIGHT_FT
    hs = ft_to_m(hs_ft)
    w(r"\subsection{Step 6: Air Distance to the Screen Height}")
    w(rf"Climb at $V_2$ with lift equal to weight (\eqref{{eq:cl-climb}}--\eqref{{eq:sin-gamma}}); screen height {Q(hs_ft, 'ft')} = {Q(hs, 'm', 2)}:")
    w(r"\begin{align*}")
    w(rf"q_{{V_2}} &= \tfrac12\times{N(rho, 4)}\times{N(v2, 2)}^2 = {Q(q2, 'Pa', 1)}, \qquad "
      rf"C_{{L,\text{{climb}}}} = \frac{{{N(weight)}}}{{{N(q2, 1)}\times{N(acft.s_ref_m2, 2)}}} = {N(cl_c, 3)}\\")
    w(rf"D &= {N(q2, 1)}\times{N(acft.s_ref_m2, 2)}\times({N(acft.cd0, 3)} + {N(acft.k_induced, 3)}\times{N(cl_c, 3)}^2) = {Q(d2, 'N')}, \qquad T = {Q(t2, 'N')}\\")
    w(rf"\sin\gamma &= \frac{{{N(t2)} - {N(d2)}}}{{{N(weight)}}} = {N(sg, 4)}, \qquad "
      rf"\gamma = {Q(gam, 'rad', 4)}, \qquad \text{{gradient}} = {N(100 * math.tan(gam), 1)}\,\%")
    w(r"\end{align*}")
    w(r"Transition arc (\eqref{eq:R-tr}--\eqref{eq:h-tr}):")
    w(r"\begin{align*}")
    w(rf"R_\text{{TR}} &= \frac{{{N(vtr, 2)}^2}}{{{N(G0_MPS2, 3)}\times({N(TRANSITION_LOAD_FACTOR, 1)} - 1)}} = {Q(R, 'm', 1)}\\")
    w(rf"h_\text{{TR}} &= {N(R, 1)}\,(1 - \cos {N(gam, 4)}) = {Q(h_tr, 'm', 2)}")
    w(r"\end{align*}")
    if h_tr >= hs:
        s_air_still = math.sqrt(R**2 - (R - hs)**2)
        w(rf"Since $h_\text{{TR}} \ge h_\text{{scr}}$, the screen is cleared inside the arc \eqref{{eq:s-air-arc}}:")
        w(r"\begin{equation*}")
        w(rf"s_\text{{air}} = \sqrt{{{N(R, 1)}^2 - ({N(R, 1)} - {N(hs, 2)})^2}} = {Q(s_air_still, 'm', 1)}")
        w(r"\end{equation*}")
    else:
        s_tr = R * math.sin(gam)
        s_cl = (hs - h_tr) / math.tan(gam)
        s_air_still = s_tr + s_cl
        w(rf"Since $h_\text{{TR}} < h_\text{{scr}}$, the arc is followed by a steady climb \eqref{{eq:s-air-climb}}:")
        w(r"\begin{equation*}")
        w(rf"s_\text{{air}} = {N(R, 1)}\sin {N(gam, 4)} + \frac{{{N(hs, 2)} - {N(h_tr, 2)}}}{{\tan {N(gam, 4)}}} = "
          rf"{N(s_tr, 1)} + {N(s_cl, 1)} = {Q(s_air_still, 'm', 1)}")
        w(r"\end{equation*}")
    w(r"Corrected for wind \eqref{eq:s-air-wind}, then the takeoff distance \eqref{eq:tod}:")
    w(r"\begin{align*}")
    w(rf"s_\text{{air}} &= {N(s_air_still, 1)}\times\frac{{{N(vtr, 2)} - {N(cond.hw_mps, 2)}}}{{{N(vtr, 2)}}} = {Q(to['air_dist_m'], 'm', 1)}\\")
    w(rf"\text{{TOD}}_\text{{AEO}} &= {N(to['ground_roll_m'], 1)} + {N(to['air_dist_m'], 1)} = {Q(to['tod_m'], 'm', 1)} = {ft(to['tod_m'])}")
    w(r"\end{align*}")

    # ---------------------------------------------------------------- BFL
    if multi:
        bfl = balanced_field(acft, elev_m, isa_dev_c, tow_kg, hw_perf_kt, slope_pct, RWY_CONDITION)
        w(r"\subsection{Step 7: Balanced Field Length}")
        w(r"For each trial $V_1$, the accelerate-go and accelerate-stop distances are computed "
          r"(\eqref{eq:s-go}--\eqref{eq:s-stop}) and their difference $f(V_1)$ \eqref{eq:f-v1}:")
        w(r"\begin{table}[H]\centering\small")
        w(rf"\caption{{{acft.name}: accelerate-go and accelerate-stop against trial $V_1$.}}")
        w(r"\begin{tabular}{@{}rrrr@{}}\toprule \textbf{$V_1$ (kt)} & \textbf{$s_\text{go}$ (ft)} & "
          r"\textbf{$s_\text{stop}$ (ft)} & \textbf{$f(V_1)$ (ft)}\\\midrule")
        lo, hi = 0.5 * vr, vr
        for frac in (0.0, 0.25, 0.5, 0.7, 0.85, 1.0):
            v1 = lo + frac * (hi - lo)
            g = accelerate_go(acft, cond, v1)[0]
            st = accelerate_stop(acft, cond, v1)
            w(rf"{N(mps_to_kt(v1), 1)} & {N(m_to_ft(g))} & {N(m_to_ft(st))} & {N(m_to_ft(g - st))}\\")
        w(rf"\midrule \textbf{{{N(mps_to_kt(bfl['v1_mps']), 1)}}} & \textbf{{{N(m_to_ft(bfl['todg_oei_m']))}}} & "
          rf"\textbf{{{N(m_to_ft(bfl['asd_m']))}}} & \textbf{{{N(m_to_ft(bfl['todg_oei_m'] - bfl['asd_m']), 1)}}}\\")
        w(r"\bottomrule\end{tabular}\end{table}")
        w(rf"$f$ changes sign between the trial values, so Brent's method converges to the balanced "
          rf"$V_1 = {kt(bfl['v1_mps'])}$ (bold row). Then (\eqref{{eq:bfl}}--\eqref{{eq:tofl}}):")
        w(r"\begin{align*}")
        w(rf"\text{{BFL}} &= {ft(bfl['bfl_m'])}\\")
        w(rf"1.15\times\text{{TOD}}_\text{{AEO}} &= 1.15\times{N(m_to_ft(bfl['tod_aeo_m']))} = {ft(bfl['tod_aeo_factored_m'])}\\")
        w(rf"\text{{TOFL}} &= \max\left({N(m_to_ft(bfl['bfl_m']))},\ {N(m_to_ft(bfl['tod_aeo_factored_m']))}\right) = "
          rf"{ft(bfl['tofl_m'])} = {Q(bfl['tofl_m'], 'm')}")
        w(r"\end{align*}")
        limit = "the all-engines distance with its 15\\% margin" if "AEO" in bfl["tofl_limit"] else "the balanced field length"
        w(rf"The TOFL is set by {limit}. The one-engine-inoperative climb gradient at $V_2$ is "
          rf"{N(bfl['oei_climb_grad_pct'], 1)}\,\%.")
        fig = plot_bfl(bfl, os.path.join(HERE, "figures", f"bfl_example_{label}.png"), runway=RUNWAY,
                       extra_conditions=[("Airport", AIRPORT.icao), ("Runway", RUNWAY.rwy_id),
                                         ("Outside Air Temp (OAT)", f"{OAT_C:.0f} °C"),
                                         ("Reported Wind", f"{WIND_DIR_DEG:03.0f}° / {WIND_KT:.0f} kt")])
        w(r"\begin{figure}[H]\centering")
        w(rf"\includegraphics[width=\linewidth]{{figures/{os.path.basename(fig)}}}")
        w(rf"\caption{{{acft.name}: Balanced Field Length (BFL) for this example.}}\end{{figure}}")
        to_step = 8
    else:
        bfl = None
        w(r"\subsection{Step 7: Engine-Failure Case}")
        w(r"The aircraft has one engine, so there is no accelerate-go case and no balanced field length. "
          r"The required takeoff distance is the all-engines TOD.")
        to_step = 8

    # ---------------------------------------------------------------- landing
    ld = landing(acft, elev_m, isa_dev_c, lw_kg, hw_perf_kt, use_reverse=False,
                 slope_pct=slope_pct, rwy_condition=RWY_CONDITION)
    w_l = lw_kg * G0_MPS2
    vs0, vref, vtd = ld["vs0_mps"], ld["vref_mps"], ld["vtd_mps"]
    w(rf"\subsection{{Step {to_step}: Landing}}")
    w(rf"Landing at MLW on the same runway, no reverse thrust credit (\eqref{{eq:vref}}--\eqref{{eq:ldr}}):")
    w(r"\begin{align*}")
    w(rf"V_{{S0}} &= \sqrt{{\frac{{2\times{N(w_l)}}}{{{N(rho, 4)}\times{N(acft.s_ref_m2, 2)}\times{N(acft.cl_max_ldg, 2)}}}}} = {Q(vs0, 'm/s', 2)} = {kt(vs0)}\\")
    w(rf"V_\text{{REF}} &= {N(VREF_FACTOR, 2)}\,V_{{S0}} = {kt(vref)}, \qquad V_\text{{TD}} = {N(VTD_FACTOR, 2)}\,V_{{S0}} = {kt(vtd)}\\")
    w(rf"s_\text{{air}} &= \frac{{{N(ft_to_m(50), 2)}}}{{\tan\ang{{{GLIDESLOPE_DEG:.0f}}}}}\times\frac{{{N(vref, 2)} - {N(cond.hw_mps, 2)}}}{{{N(vref, 2)}}} = {Q(ld['air_dist_m'], 'm', 1)}\\")
    w(rf"s_\text{{free}} &= ({N(vtd, 2)} - {N(cond.hw_mps, 2)})\times{N(acft.FREE_ROLL_S, 0)} = {Q(ld['free_roll_m'], 'm', 1)}\\")
    w(rf"s_\text{{brake}} &= {Q(ld['braking_roll_m'], 'm', 1)} \quad\text{{(\eqref{{eq:eom-brake}} integrated to rest, {N(ld['braking_s'], 1)}\,s)}}\\")
    w(rf"\text{{LD}} &= {N(ld['air_dist_m'], 1)} + {N(ld['free_roll_m'], 1)} + {N(ld['braking_roll_m'], 1)} = {Q(ld['ld_m'], 'm', 1)} = {ft(ld['ld_m'])}")
    if ld["ldr_m"]:
        w(rf"\\ \text{{LDR}} &= \frac{{{N(ld['ld_m'], 1)}}}{{0.6}} = {Q(ld['ldr_m'], 'm', 1)} = {ft(ld['ldr_m'])}")
    w(r"\end{align*}")

    # ---------------------------------------------------------------- runway check
    w(rf"\subsection{{Step {to_step + 1}: Runway Check}}")
    if multi:
        checks = [("Takeoff Field Length (TOFL)", bfl["tofl_m"], "TODA", RUNWAY.toda_m),
                  ("Accelerate-Stop Distance (ASD)", bfl["asd_m"], "ASDA", RUNWAY.asda_m)]
    else:
        checks = [("Takeoff Distance (TOD)", to["tod_m"], "TODA", RUNWAY.toda_m),
                  ("Takeoff ground roll", to["ground_roll_m"], "TORA", RUNWAY.tora_m)]
    if ld["ldr_m"]:
        checks.append(("Landing Distance Required (LDR)", ld["ldr_m"], "LDA", RUNWAY.lda_m))
    else:
        checks.append(("Landing Distance (LD)", ld["ld_m"], "LDA", RUNWAY.lda_m))
    w(r"\begin{table}[H]\centering\small")
    w(rf"\caption{{{acft.name}: runway check, {AIRPORT.icao} runway {RUNWAY.rwy_id}.}}")
    w(r"\begin{tabular}{@{}lrlrrl@{}}\toprule \textbf{Required} & \textbf{ft} & \textbf{Available} & "
      r"\textbf{ft} & \textbf{Margin (ft)} & \textbf{Result}\\\midrule")
    for name, req, avail_name, avail in checks:
        ok = "OK" if req <= avail else "Not OK"
        w(rf"{name} & {N(m_to_ft(req))} & {avail_name} & {N(m_to_ft(avail))} & {N(m_to_ft(avail - req))} & {ok}\\")
    w(r"\bottomrule\end{tabular}\end{table}")
    return "\n".join(out)


def main():
    for acft, label in ((CL3500, "Challenger_3500"), (SR22T, "Cirrus_SR22T")):
        tex = example(acft, label)
        path = os.path.join(HERE, f"examples_{label.lower()}.tex")
        tex = captions_below(tex)
        with open(path, "w") as f:
            f.write(f"% Generated by make_examples.py from the model. Do not edit by hand.\n{tex}\n")
        print(f"  wrote {path}")


if __name__ == "__main__":
    main()
