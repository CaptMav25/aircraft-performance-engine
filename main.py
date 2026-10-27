"""
Module:   main
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Entry point. One menu for aircraft and airport profiles and every
    calculation. Run: python3 main.py
"""

from aircraft import CL3500
from airports import airport_menu, load_airports, CYYZ
from bfl import run_bfl_interactive
from exceptions import PerformanceError
from landing import run_landing_interactive
from profiles import menu as profile_menu, load_profiles
from runway_analysis import run_runway_analysis_interactive
from takeoff import run_takeoff_interactive


def main():
    load_profiles()
    load_airports()
    acft = CL3500
    apt, rwy = CYYZ, CYYZ.runway("05")
    while True:
        print("\n" + "=" * 62)
        print("  AIRCRAFT PERFORMANCE ENGINE: TAKEOFF & LANDING")
        print(f"  Aircraft: {acft.name} ({acft.ENGINE_TYPE}, {acft.n_engines} eng)"
              f"    Runway: {apt.icao} {rwy.rwy_id}")
        print("=" * 62)
        print("  1. Aircraft profiles (create / view / select / delete)")
        print("  2. Airports & runways (create / view / select / delete)")
        print("  3. Runway analysis: can I take off and land here today?")
        print("  4. Balanced field length (engine failure at V1)")
        print("  5. Takeoff calculation (all engines)")
        print("  6. Landing calculation")
        print("  7. Sensitivity plots")
        print("  8. Quit")
        choice = input("Choose 1-8: ").strip()

        try:
            if choice == "1":
                acft = profile_menu(acft)
            elif choice == "2":
                apt, rwy = airport_menu((apt, rwy))
            elif choice == "3":
                run_runway_analysis_interactive(acft, apt, rwy)
            elif choice == "4":
                run_bfl_interactive(acft)
            elif choice == "5":
                run_takeoff_interactive(acft)
            elif choice == "6":
                run_landing_interactive(acft)
            elif choice == "7":
                from sensitivity import run_sweeps, print_summary, plot_sensitivity
                print("\n  Running sweeps (about 5-10 s)...")
                results = run_sweeps(acft)
                print_summary(acft, results)
                print(f"  Saved plot: {plot_sensitivity(acft, results)}")
            elif choice == "8":
                print("Goodbye.")
                break
            else:
                print("  Pick 1-8.")
        except PerformanceError as err:      # any model error: thrust, climb, altitude
            print(f"\n  Error ({type(err).__name__}): {err}")


if __name__ == "__main__":
    main()
