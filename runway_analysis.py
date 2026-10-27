"""
Module:   runway_analysis
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Checks whether an aircraft can take off and land on a given runway today.
    Twins: TOFL <= TODA and accelerate-stop <= ASDA. Singles: TOD <= TODA and
    ground roll <= TORA. Landing: LDR <= LDA for jets (x 1.15 wet), LD <= LDA
    for props. Reported wind is factored 50% headwind / 150% tailwind.

Basis:
    14 CFR 25.105(d), 25.109, 25.113, 121.195; CAR 525
"""

from aircraft import Aircraft, JetAircraft
from airports import Airport, Runway, wind_components
from atmosphere import isa
from bfl import balanced_field, plot_bfl
from landing import landing
from takeoff import takeoff, ask
from units import ft_to_m, m_to_ft, mps_to_kt, lb_to_kg, kg_to_lb, k_to_c

# Reported wind is not guaranteed for the whole takeoff, so the rules give
# only half the benefit of a headwind and 1.5 times the penalty of a tailwind.
HEADWIND_CREDIT = 0.5          # [14CFR25] §25.105(d)(1)
TAILWIND_PENALTY = 1.5         # [14CFR25] §25.105(d)(1)
WET_LDR_FACTOR = 1.15          # [14CFR121] §121.195(d)
TAILWIND_LIMIT_KT = 10.0       # typical AFM limit; only triggers a warning


def factored_headwind(hw_kt):
    return hw_kt * (HEADWIND_CREDIT if hw_kt >= 0 else TAILWIND_PENALTY)


def isa_dev_from_oat(elev_m, oat_c):
    return oat_c - k_to_c(isa(elev_m)[0])


def analyze_runway(acft: Aircraft, apt: Airport, rwy: Runway, oat_c=15.0, wind_dir_deg=0.0,
                   wind_kt=0.0, rwy_condition="dry", tow_kg=None, lw_kg=None, use_reverse=False):
    """Check takeoff and landing on one runway. Returns every number plus pass/fail."""
    tow_kg = acft.mtow_kg if tow_kg is None else tow_kg
    lw_kg = acft.mlw_kg if lw_kg is None else lw_kg
    isa_dev_c = isa_dev_from_oat(apt.elev_m, oat_c)
    hw_kt, xw_kt = wind_components(wind_dir_deg, wind_kt, rwy.hdg_true_deg)
    hw_perf_kt = factored_headwind(hw_kt)
    common = dict(elev_m=apt.elev_m, isa_dev_c=isa_dev_c, hw_kt=hw_perf_kt,
                  slope_pct=rwy.slope_pct, rwy_condition=rwy_condition)

    result = {
        "acft_name": acft.name, "icao": apt.icao, "rwy_id": rwy.rwy_id, "rwy": rwy,
        "elev_m": apt.elev_m, "oat_c": oat_c, "isa_dev_c": isa_dev_c,
        "wind_dir_deg": wind_dir_deg, "wind_kt": wind_kt,
        "hw_kt": hw_kt, "xw_kt": xw_kt, "hw_perf_kt": hw_perf_kt,
        "rwy_condition": rwy_condition, "tow_kg": tow_kg, "lw_kg": lw_kg,
        "warnings": [],
    }
    if hw_kt < -TAILWIND_LIMIT_KT:
        result["warnings"].append(f"tailwind {-hw_kt:.0f} kt exceeds the typical "
                                  f"{TAILWIND_LIMIT_KT:.0f} kt certified limit")

    if acft.n_engines >= 2:
        bfl = balanced_field(acft, mass_kg=tow_kg, n_curve_points=2, **common)
        result.update(takeoff_mode="balanced field (engine failure at V1)",
                      v1_mps=bfl["v1_mps"], vr_mps=bfl["vr_mps"], v2_mps=bfl["v2_mps"],
                      tod_req_m=bfl["tofl_m"], asd_req_m=bfl["asd_m"],
                      tofl_limit=bfl["tofl_limit"], oei_climb_grad_pct=bfl["oei_climb_grad_pct"])
        checks = [("TOFL", bfl["tofl_m"], "TODA", rwy.toda_m),
                  ("ASD", bfl["asd_m"], "ASDA", rwy.asda_m)]
    else:
        to = takeoff(acft, mass_kg=tow_kg, **common)
        result.update(takeoff_mode="all engines (single-engine aircraft)",
                      vr_mps=to["vr_mps"], v2_mps=to["v2_mps"], tod_req_m=to["tod_m"])
        checks = [("TOD", to["tod_m"], "TODA", rwy.toda_m),
                  ("Ground roll", to["ground_roll_m"], "TORA", rwy.tora_m)]
    result["takeoff_checks"] = checks
    result["takeoff_ok"] = all(req <= avail for _, req, _, avail in checks)

    ld = landing(acft, mass_kg=lw_kg, use_reverse=use_reverse, **common)
    if isinstance(acft, JetAircraft):
        # §121.195 factors the DRY distance, even when the runway is wet.
        ld_dry = ld if rwy_condition == "dry" else landing(
            acft, mass_kg=lw_kg, use_reverse=use_reverse, **{**common, "rwy_condition": "dry"})
        ldr_m = ld_dry["ldr_m"] * (WET_LDR_FACTOR if rwy_condition == "wet" else 1.0)
        label = "LDR (dry ÷0.6" + (" × 1.15 wet)" if rwy_condition == "wet" else ")")
        result["landing_checks"] = [(label, ldr_m, "LDA", rwy.lda_m)]
    else:
        result["landing_checks"] = [("LD (unfactored)", ld["ld_m"], "LDA", rwy.lda_m)]
    result.update(vref_mps=ld["vref_mps"], ld_m=ld["ld_m"])
    result["landing_ok"] = all(req <= avail for _, req, _, avail in result["landing_checks"])
    return result


def print_runway_analysis(result):
    def check_line(name, req_m, avail_name, avail_m):
        ok = req_m <= avail_m
        mark = "OK  " if ok else "NO  "
        margin_ft = m_to_ft(avail_m - req_m)
        return (f"  {name:<24} {m_to_ft(req_m):7,.0f} ft   vs {avail_name} {m_to_ft(avail_m):7,.0f} ft"
                f"   {mark} (margin {margin_ft:+,.0f} ft)")

    side = "R" if result["xw_kt"] >= 0 else "L"
    hw_txt = (f"headwind {result['hw_kt']:.0f} kt" if result["hw_kt"] >= 0
              else f"TAILWIND {-result['hw_kt']:.0f} kt")
    print(f"\n{'=' * 78}")
    print(f"  {result['acft_name']} at {result['icao']} RWY {result['rwy_id']}"
          f"   ({result['rwy_condition'].upper()} runway)")
    print(f"{'=' * 78}")
    print(f"  Elevation {m_to_ft(result['elev_m']):,.0f} ft   OAT {result['oat_c']:.0f} °C "
          f"(ISA{result['isa_dev_c']:+.0f})   slope {result['rwy'].slope_pct:+.2f}%")
    print(f"  Wind {result['wind_dir_deg']:03.0f}°/{result['wind_kt']:.0f} kt: {hw_txt}, "
          f"crosswind {abs(result['xw_kt']):.0f} kt from the {side}")
    print(f"  Performance wind (50% head / 150% tail): {result['hw_perf_kt']:+.1f} kt")

    print(f"\n  TAKEOFF at {kg_to_lb(result['tow_kg']):,.0f} lb  [{result['takeoff_mode']}]")
    if "v1_mps" in result:
        print(f"  V1 {mps_to_kt(result['v1_mps']):.0f}   VR {mps_to_kt(result['vr_mps']):.0f}   "
              f"V2 {mps_to_kt(result['v2_mps']):.0f} KTAS   OEI gradient "
              f"{result['oei_climb_grad_pct']:.1f}%   (TOFL limited by {result['tofl_limit']})")
    else:
        print(f"  VR {mps_to_kt(result['vr_mps']):.0f}   V2 {mps_to_kt(result['v2_mps']):.0f} KTAS")
    for line in result["takeoff_checks"]:
        print(check_line(*line))

    print(f"\n  LANDING at {kg_to_lb(result['lw_kg']):,.0f} lb   VREF {mps_to_kt(result['vref_mps']):.0f} KTAS"
          f"   (unfactored LD {m_to_ft(result['ld_m']):,.0f} ft)")
    for line in result["landing_checks"]:
        print(check_line(*line))

    for warning in result["warnings"]:
        print(f"\n  Warning: {warning}")
    verdict_to = "TAKEOFF OK" if result["takeoff_ok"] else "TAKEOFF NOT POSSIBLE"
    verdict_ld = "LANDING OK" if result["landing_ok"] else "LANDING NOT POSSIBLE"
    print(f"\n  {verdict_to}    {verdict_ld}")


def run_runway_analysis_interactive(acft: Aircraft, apt: Airport, rwy: Runway):
    print(f"\n--- Today's conditions at {apt.icao} RWY {rwy.rwy_id} for {acft.name} ---")
    oat_c = ask("OAT [°C]", 15)
    wind_dir_deg = ask("Wind direction [°true, from]", rwy.hdg_true_deg)
    wind_kt = ask("Wind speed [kt]", 0)
    wet = input("  Runway wet? (y/n, default n): ").strip().lower() == "y"
    tow_lb = ask("Takeoff weight [lb]", round(kg_to_lb(acft.mtow_kg)))
    lw_lb = ask("Landing weight [lb]", round(kg_to_lb(acft.mlw_kg)))
    rwy_condition = "wet" if wet else "dry"
    result = analyze_runway(acft, apt, rwy, oat_c, wind_dir_deg, wind_kt,
                            rwy_condition, lb_to_kg(tow_lb), lb_to_kg(lw_lb))
    print_runway_analysis(result)
    if acft.n_engines >= 2:
        save_bfl_chart(acft, apt, rwy, result)
    return result


def save_bfl_chart(acft: Aircraft, apt: Airport, rwy: Runway, result):
    bfl = balanced_field(acft, elev_m=apt.elev_m, isa_dev_c=result["isa_dev_c"],
                         mass_kg=result["tow_kg"], hw_kt=result["hw_perf_kt"],
                         slope_pct=rwy.slope_pct, rwy_condition=result["rwy_condition"])
    bfl["wind_factored"] = True
    filename = f"bfl_{acft.name.replace(' ', '_')}_{apt.icao}_{rwy.rwy_id}.png"
    extra = [
        ("Airport", apt.icao),
        ("Runway", rwy.rwy_id),
        ("Outside Air Temp (OAT)", f"{result['oat_c']:.0f} °C"),
        ("Reported Wind", f"{result['wind_dir_deg']:03.0f}° / {result['wind_kt']:.0f} kt"),
    ]
    print(f"  Saved chart: {plot_bfl(bfl, filename, runway=rwy, extra_conditions=extra)}")
