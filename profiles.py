"""
Module:   profiles
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Create, view, select and delete aircraft profiles. User profiles are saved
    to aircraft_profiles.json and rebuilt as PropAircraft or JetAircraft on
    load. The user types lb, ft2, hp and lbf; everything is stored in SI.
"""

import json
import os
from dataclasses import asdict, fields

from aircraft import PropAircraft, JetAircraft, AIRCRAFT_CLASSES, C172, CL3500, BUILT_IN
from units import (lb_to_kg, kg_to_lb, ft2_to_m2, m2_to_ft2, lbf_to_n, n_to_lbf, hp_to_w, w_to_hp,
                   ft_to_m, m_to_ft)

PROFILE_FILE = "aircraft_profiles.json"


def _identity(x):
    return x


# Unit shown to the user -> (convert to SI, convert from SI)
CONVERTERS = {
    "lb":  (lb_to_kg, kg_to_lb),
    "ft²": (ft2_to_m2, m2_to_ft2),
    "lbf": (lbf_to_n, n_to_lbf),
    "hp":  (hp_to_w, w_to_hp),
    "ft":  (ft_to_m, m_to_ft),
    "-":   (_identity, _identity),
}

# (field, prompt, unit the user types in, min, max). Limits are in that unit and
# only catch typing mistakes; they are not certification limits.
COMMON_QUESTIONS = [
    ("mtow_kg",      "MTOW (max takeoff weight)",          "lb",  200,  1_500_000),
    ("mlw_kg",       "MLW (max landing weight)",           "lb",  200,  1_500_000),
    ("s_ref_m2",     "Reference wing area",                "ft²", 20,   10_000),
    ("cd0",          "CD0 (zero-lift drag coefficient)",   "-",   0.01, 0.10),
    ("k_induced",    "k (induced drag factor)",            "-",   0.01, 0.20),
    ("cl_max_to",    "CL_max, takeoff flaps",              "-",   0.8,  3.5),
    ("cl_max_ldg",   "CL_max, landing flaps",              "-",   0.8,  3.5),
    ("cl_gnd",       "CL during ground roll",              "-",   0.0,  1.5),
    ("mu_roll",      "μ rolling friction",                 "-",   0.01, 0.30),
    ("mu_brake",     "μ braking friction",                 "-",   0.05, 0.80),
    ("sls_thrust_n", "SLS thrust (sea-level static, total)", "lbf", 50,  500_000),
]

PROP_QUESTIONS = [
    ("n_engines",    "Number of engines",                  "-",   1,    2),
    ("max_power_w",  "Max power (sea level, total)",       "hp",  10,   20_000),
    ("eta_prop",     "η_prop (propeller efficiency)",      "-",   0.3,  0.9),
    ("critical_alt_m", "Turbo critical altitude (0 = not turbocharged)", "ft", 0, 40_000),
]

JET_QUESTIONS = [
    ("n_engines",        "Number of engines",                      "-", 2, 4),
    ("flat_rating_isa_c", "Flat rating: thrust held to ISA + [°C]", "-", 0, 30),
    ("thrust_lapse",     "Thrust lapse with Mach (≈0.9 turbofan)", "-", 0.0, 1.0),
    ("rev_thrust_ratio", "Reverse thrust ratio (0 = none)",        "-", 0.0, 0.6),
]

profiles = {}

EXTRA_QUESTIONS = {PropAircraft: PROP_QUESTIONS, JetAircraft: JET_QUESTIONS}


def questions_for(acft_class):
    return COMMON_QUESTIONS + EXTRA_QUESTIONS[acft_class]


def _build_aircraft(values):
    values = dict(values)
    engine_type = values.pop("engine_type", "prop")
    acft_class = AIRCRAFT_CLASSES[engine_type]
    # Ignore keys this class doesn't have, so a hand-edited file can't crash the load.
    allowed = {f.name for f in fields(acft_class)}
    return acft_class(**{key: val for key, val in values.items() if key in allowed})


def load_profiles():
    profiles.clear()
    profiles.update(BUILT_IN)
    if not os.path.exists(PROFILE_FILE):
        return profiles

    f = open(PROFILE_FILE)
    try:
        data = json.load(f)
    except json.JSONDecodeError as err:
        print(f"  Warning: {PROFILE_FILE} is damaged ({err.msg}); using built-in aircraft only.")
    else:
        for name, values in data.items():
            if name not in BUILT_IN:        # built-ins always come from the code
                profiles[name] = _build_aircraft(values)
    finally:
        f.close()
    return profiles


def save_profiles():
    # ENGINE_TYPE is a class variable, so asdict() leaves it out. It is saved
    # by hand so the loader knows which class to rebuild.
    data = {name: {"engine_type": acft.ENGINE_TYPE, **asdict(acft)}
            for name, acft in profiles.items() if name not in BUILT_IN}
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def ask_number(prompt, unit, min_value, max_value, default):
    unit_txt = f" [{unit}]" if unit != "-" else ""
    while True:
        user_input = input(f"  {prompt}{unit_txt} (default {default:g}): ").strip()
        if user_input == "":
            return default
        try:
            value = float(user_input)
        except ValueError:
            print("    Please enter a number.")
            continue
        if not min_value <= value <= max_value:
            print(f"    Must be between {min_value:g} and {max_value:g}.")
            continue
        return value


def create_profile():
    print("\n--- Create aircraft profile ---")

    while True:
        name = input("  Aircraft name: ").strip()
        if not name:
            print("    Name can't be empty.")
        elif name in profiles:
            if input(f"    '{name}' exists. Overwrite? (y/n): ").lower() == "y":
                break
        else:
            break

    while True:
        engine = input("  Engine type - (p)ropeller or (j)et: ").strip().lower()
        if engine in ("p", "prop", "propeller"):
            acft_class, template = PropAircraft, C172
            break
        if engine in ("j", "jet"):
            acft_class, template = JetAircraft, CL3500
            break
        print("    Type p or j.")

    print(f"  Press Enter to accept the default ({template.name} value).\n")

    values = {"name": name}
    for field, prompt, unit, min_value, max_value in questions_for(acft_class):
        to_si, from_si = CONVERTERS[unit]
        default_shown = float(f"{from_si(getattr(template, field)):.4g}")
        value_shown = ask_number(prompt, unit, min_value, max_value, default_shown)
        values[field] = to_si(value_shown)

    if values["mlw_kg"] > values["mtow_kg"]:
        print("  Warning: MLW is higher than MTOW.")
    if values["cl_max_ldg"] < values["cl_max_to"]:
        print("  Warning: landing CL_max is usually higher than takeoff CL_max.")

    acft = acft_class(**values)
    profiles[name] = acft
    save_profiles()
    print(f"\n  '{name}' saved.")
    return acft


def show_profile(acft):
    print(f"\n--- {acft.name}  ({acft.ENGINE_TYPE}) ---")
    for field, prompt, unit, _, _ in questions_for(type(acft)):
        _, from_si = CONVERTERS[unit]
        value = from_si(getattr(acft, field))
        value_txt = f"{value:,.0f}" if value >= 1000 else f"{value:.4g}"
        unit_txt = unit if unit != "-" else ""
        print(f"  {prompt:<42} {value_txt:>10} {unit_txt}")


def choose_profile():
    names = list(profiles)
    print("\n--- Saved profiles ---")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}  ({profiles[name].ENGINE_TYPE})")
    user_input = input("  Pick a number (Enter to cancel): ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(names):
        return profiles[names[int(user_input) - 1]]
    return None


def delete_profile():
    acft = choose_profile()
    if acft is None:
        return
    if acft.name in BUILT_IN:
        print(f"  The built-in {acft.name} can't be deleted.")
        return
    if input(f"  Delete '{acft.name}'? (y/n): ").lower() == "y":
        del profiles[acft.name]
        save_profiles()
        print("  Deleted.")


def menu(selected=None):
    """Profile menu. Returns the aircraft selected when the user picks Done."""
    load_profiles()
    selected = selected or C172
    while True:
        print(f"\n===== Aircraft Profiles  (selected: {selected.name}) =====")
        print("  1. Create new profile")
        print("  2. View a profile")
        print("  3. Select profile to use")
        print("  4. Delete a profile")
        print("  5. Done (use selected aircraft)")
        choice = input("Choose 1-5: ").strip()

        if choice == "1":
            selected = create_profile()
        elif choice == "2":
            acft = choose_profile()
            if acft:
                show_profile(acft)
        elif choice == "3":
            acft = choose_profile()
            if acft:
                selected = acft
                print(f"  Using {acft}")
        elif choice == "4":
            delete_profile()
            if selected.name not in profiles:
                selected = C172
        elif choice == "5":
            return selected
        else:
            print("  Pick 1-5.")
