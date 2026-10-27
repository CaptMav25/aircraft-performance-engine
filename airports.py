"""
Module:   airports
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Airport and Runway classes, the built-in CYYZ, CYMX and KICT runways, and
    the airport menu. Each runway direction is its own Runway because heading,
    slope and declared distances differ by direction.

Note:
    Declared distances are approximated: TORA = TODA = ASDA = runway length,
    LDA = length minus displaced threshold. Official values are in the CFS /
    FAA Chart Supplement.

Basis:
    OurAirports runway data; ICAO Annex 14 (declared distances)
"""

import json
import math
import os
from dataclasses import dataclass, field, asdict
from typing import List

from units import ft_to_m, m_to_ft

AIRPORT_FILE = "airports.json"


@dataclass
class Runway:
    """One runway direction, e.g. CYYZ 05."""
    rwy_id: str
    hdg_true_deg: float      # true, not magnetic, because METAR winds are true
    tora_m: float
    toda_m: float
    asda_m: float
    lda_m: float
    slope_pct: float = 0.0   # + = uphill in this direction

    def __str__(self):
        return (f"RWY {self.rwy_id:<4} hdg {self.hdg_true_deg:5.1f}°T  "
                f"TORA {m_to_ft(self.tora_m):6,.0f}  TODA {m_to_ft(self.toda_m):6,.0f}  "
                f"ASDA {m_to_ft(self.asda_m):6,.0f}  LDA {m_to_ft(self.lda_m):6,.0f} ft  "
                f"slope {self.slope_pct:+.2f}%")


@dataclass
class Airport:
    icao: str
    name: str
    elev_m: float
    runways: List[Runway] = field(default_factory=list)
    note: str = ""

    def runway(self, rwy_id):
        for rwy in self.runways:
            if rwy.rwy_id.upper() == rwy_id.upper():
                return rwy
        raise KeyError(f"{self.icao} has no runway {rwy_id}")

    def __str__(self):
        return f"{self.icao} {self.name} (elev {m_to_ft(self.elev_m):,.0f} ft, {len(self.runways)} runways)"


def runway_pair(id_1, hdg_1_deg, id_2, hdg_2_deg, length_ft, disp_1_ft=0.0, disp_2_ft=0.0,
                slope_1_pct=0.0):
    """
    Both directions of one physical runway. A displaced threshold only shortens
    the LDA landing toward it; the slope flips sign for the other direction.
    """
    length_m = ft_to_m(length_ft)
    return [
        Runway(id_1, hdg_1_deg, length_m, length_m, length_m, length_m - ft_to_m(disp_1_ft), slope_1_pct),
        Runway(id_2, hdg_2_deg, length_m, length_m, length_m, length_m - ft_to_m(disp_2_ft), -slope_1_pct),
    ]


def wind_components(wind_dir_deg, wind_kt, rwy_hdg_deg):
    """Returns (headwind, crosswind) in kt. Wind direction is where it blows from;
    negative headwind is a tailwind, positive crosswind is from the right."""
    angle_rad = math.radians(wind_dir_deg - rwy_hdg_deg)
    return wind_kt * math.cos(angle_rad), wind_kt * math.sin(angle_rad)


CYYZ = Airport(
    icao="CYYZ",
    name="Toronto Pearson International",
    elev_m=ft_to_m(569),
    runways=(runway_pair("05", 47, "23", 227, 11_120, 135, 485, -0.036)
             + runway_pair("06L", 47, "24R", 227, 9_697, 0, 197, +0.175)
             + runway_pair("06R", 47, "24L", 227, 9_000, 0, 0, +0.244)
             + runway_pair("15L", 137, "33R", 317, 11_050, 0, 0, -0.118)
             + runway_pair("15R", 137, "33L", 317, 9_088, 588, 588, -0.077)),
    note="Bombardier Global final assembly is on the north side of the airfield.",
)

CYMX = Airport(
    icao="CYMX",
    name="Montréal-Mirabel International",
    elev_m=ft_to_m(271),
    runways=runway_pair("06", 45.4, "24", 225.4, 12_000, 0, 0, -0.150),
    note="Runway 11/29 omitted: sources disagree on its length and report it closed by NOTAM.",
)

KICT = Airport(
    icao="KICT",
    name="Wichita Dwight D. Eisenhower National",
    elev_m=ft_to_m(1_333),
    runways=(runway_pair("01L", 20, "19R", 200, 10_302, 0, 0, +0.165)
             + runway_pair("01R", 20, "19L", 200, 7_302, 0, 0, -0.014)
             + runway_pair("14", 150, "32", 330, 6_301, 0, 0, -0.159)),
    note="Bombardier Flight Test Center (BFTC) is in Wichita, on the former Learjet site.",
)

BUILT_IN_AIRPORTS = {apt.icao: apt for apt in (CYYZ, CYMX, KICT)}

airports = {}


def _airport_from_dict(values):
    values = dict(values)
    values["runways"] = [Runway(**rwy) for rwy in values.get("runways", [])]
    return Airport(**values)


def load_airports():
    # Built-ins always come from the code, so a bad edit to the file can't break them.
    airports.clear()
    airports.update(BUILT_IN_AIRPORTS)
    if not os.path.exists(AIRPORT_FILE):
        return airports
    f = open(AIRPORT_FILE)
    try:
        data = json.load(f)
    except json.JSONDecodeError as err:
        print(f"  Warning: {AIRPORT_FILE} is damaged ({err.msg}); using built-in airports only.")
    else:
        for icao, values in data.items():
            if icao not in BUILT_IN_AIRPORTS:
                airports[icao] = _airport_from_dict(values)
    finally:
        f.close()
    return airports


def save_airports():
    data = {icao: asdict(apt) for icao, apt in airports.items() if icao not in BUILT_IN_AIRPORTS}
    with open(AIRPORT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _ask_float(prompt, default=None, min_value=-1e9, max_value=1e9):
    default_txt = f" (default {default:g})" if default is not None else ""
    while True:
        user_input = input(f"  {prompt}{default_txt}: ").strip()
        if not user_input and default is not None:
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


def _create_runways():
    print("\n  -- Add a runway (both directions) --")
    id_1 = input("  Designator, first direction (e.g. 06): ").strip().upper()
    id_2 = input("  Designator, opposite direction (e.g. 24): ").strip().upper()
    hdg_1 = _ask_float(f"True heading of {id_1} [°]", None, 0, 360)
    length_ft = _ask_float("Runway length [ft]", None, 500, 25_000)
    disp_1 = _ask_float(f"Displaced threshold at {id_1} end [ft]", 0, 0, length_ft)
    disp_2 = _ask_float(f"Displaced threshold at {id_2} end [ft]", 0, 0, length_ft)
    slope_1 = _ask_float(f"Slope when using {id_1} [%] (+ = uphill)", 0, -3, 3)
    pair = runway_pair(id_1, hdg_1, id_2, (hdg_1 + 180) % 360, length_ft, disp_1, disp_2, slope_1)
    print("  TORA, TODA and ASDA are set to the runway length. Edit airports.json for exact"
          " declared distances.")
    return pair


def create_airport():
    print("\n--- Create airport ---")
    icao = input("  ICAO code (e.g. CYOW): ").strip().upper()
    if not icao:
        print("    ICAO code can't be empty.")
        return None
    if icao in BUILT_IN_AIRPORTS:
        print(f"    {icao} is built in and can't be replaced.")
        return None
    name = input("  Airport name: ").strip() or icao
    elev_ft = _ask_float("Elevation [ft]", 0, -1_000, 14_000)
    apt = Airport(icao, name, ft_to_m(elev_ft))
    while True:
        apt.runways += _create_runways()
        if input("  Add another runway? (y/n): ").strip().lower() != "y":
            break
    airports[icao] = apt
    save_airports()
    print(f"\n  Saved {apt}")
    return apt


def show_airport(apt):
    print(f"\n--- {apt} ---")
    for rwy in apt.runways:
        print(f"  {rwy}")
    if apt.note:
        print(f"  Note: {apt.note}")


def choose_airport():
    codes = list(airports)
    print("\n--- Airports ---")
    for i, icao in enumerate(codes, 1):
        tag = "  (built-in)" if icao in BUILT_IN_AIRPORTS else ""
        print(f"  {i}. {airports[icao]}{tag}")
    user_input = input("  Pick a number (Enter to cancel): ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(codes):
        return airports[codes[int(user_input) - 1]]
    return None


def choose_runway(apt):
    print(f"\n--- Runways at {apt.icao} ---")
    for i, rwy in enumerate(apt.runways, 1):
        print(f"  {i}. {rwy}")
    user_input = input("  Pick a number (Enter to cancel): ").strip()
    if user_input.isdigit() and 1 <= int(user_input) <= len(apt.runways):
        return apt.runways[int(user_input) - 1]
    return None


def delete_airport():
    apt = choose_airport()
    if apt is None:
        return
    if apt.icao in BUILT_IN_AIRPORTS:
        print(f"  {apt.icao} is built in and can't be deleted.")
        return
    if input(f"  Delete {apt.icao}? (y/n): ").strip().lower() == "y":
        del airports[apt.icao]
        save_airports()
        print("  Deleted.")


def airport_menu(selected=None):
    load_airports()
    selected = selected or (CYYZ, CYYZ.runway("05"))
    while True:
        apt, rwy = selected
        print(f"\n===== Airports & Runways  (selected: {apt.icao} RWY {rwy.rwy_id}) =====")
        print("  1. Create new airport")
        print("  2. View an airport")
        print("  3. Select airport and runway")
        print("  4. Delete an airport")
        print("  5. Done (use selected runway)")
        choice = input("Choose 1-5: ").strip()
        if choice == "1":
            new_apt = create_airport()
            if new_apt and new_apt.runways:
                selected = (new_apt, new_apt.runways[0])
        elif choice == "2":
            chosen = choose_airport()
            if chosen:
                show_airport(chosen)
        elif choice == "3":
            chosen = choose_airport()
            if chosen:
                chosen_rwy = choose_runway(chosen)
                if chosen_rwy:
                    selected = (chosen, chosen_rwy)
                    print(f"  Using {chosen.icao} {chosen_rwy}")
        elif choice == "4":
            delete_airport()
        elif choice == "5":
            return selected
        else:
            print("  Pick 1-5.")
