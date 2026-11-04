# Glossary

This file defines every name, abbreviation and unit suffix used in the Aircraft Performance Engine.

---

## 1. Naming conventions
| Rule | Example |
|---|---|
| Every dimensional quantity ends in its unit | `ground_roll_m`, `hw_kt`, `thrust_n` |
| Speeds use the standard AFM/POH V-speed names | `v1_mps`, `vr_mps`, `v2_mps`, `vref_mps` |
| **All speeds in the code are true airspeed (TAS)** | Output is labelled **KTAS** |
| Coefficients keep their textbook symbols, in lowercase | `cd0`, `cl_max_to`, `mu_roll`, `eta_prop` |
| Industry abbreviations are used for standard terms | `mtow_kg`, `tofl_m`, `asd_m`, `ldr_m`, `isa_dev_c` |
| Constants and class variables are in CAPS, with units | `TAKEOFF_SCREEN_HEIGHT_FT`, `STOP_DELAY_S` |
| Unit conversions are functions named `<from>_to_<to>()` | `ft_to_m()`, `mps_to_kt()` |
| Dimensionless quantities have no suffix | `sigma`, `mach`, `cl_climb` |
| Names starting with `_` are private to their file | `_build_aircraft()`, `_M_PER_FT` |

---

## 2. Unit suffixes
| Suffix | Unit | Quantity |
|---|---|---|
| `_m` | metre | length, distance, altitude |
| `_ft` | foot | length (input/output only) |
| `_m2` | square metre | area |
| `_kg` | kilogram | mass |
| `_lb` | pound (mass) | mass (input/output only) |
| `_n` | newton | force |
| `_lbf` | pound-force | force (input/output only) |
| `_w` | watt | power |
| `_hp` | horsepower | power (input/output only) |
| `_mps` | metre per second | speed |
| `_kt` | knot | speed (input/output only) |
| `_mps2` | metre per second² | acceleration |
| `_pa` | pascal | pressure |
| `_kg_m3` | kilogram per cubic metre | density |
| `_k` | kelvin | absolute temperature |
| `_c` | degree Celsius | temperature or temperature difference |
| `_s` | second | time |
| `_rad` / `_deg` | radian / degree | angle, heading |
| `_pct` | percent | ratio × 100 (gradients, slopes) |

---

## 3. V-speeds (all computed as TAS)
| Name in code | Term | Definition | Model value |
|---|---|---|---|
| `vs1_mps` | **VS1** | Stall speed in a specified configuration (here, takeoff flaps) | from `cl_max_to` |
| `vs0_mps` | **VS0** | Stall speed in the landing configuration | from `cl_max_ldg` |
| `v1_mps` | **V1** | Takeoff decision speed: an engine failure below V1 means stop, above V1 means go | solved by `balanced_field()` |
| `vr_mps` | **VR** | Rotation speed; liftoff follows after `ROTATION_S` | 1.1 × VS1 |
| `v2_mps` | **V2** | Takeoff safety speed, held in the initial climb (also with one engine out) | 1.2 × VS1 |
| `v_tr_mps` | **V_TR** | Average speed in the transition arc after liftoff | 1.15 × VS1 |
| `vref_mps` | **VREF** | Landing reference speed at the 50 ft screen height | 1.3 × VS0 |
| `vtd_mps` | **VTD** | Touchdown speed | 1.15 × VS0 |
| `tas_mps` | **TAS** | True airspeed: speed relative to the air mass | |
| `gs_mps` | **GS** | Ground speed: speed relative to the runway (GS = TAS − headwind) | |
| `hw_mps`, `hw_kt` | **HW** | Headwind component; negative means tailwind | |
| `xw_kt` | **XW** | Crosswind component; + = from the right | |

**Related terms used in the README:**
- **CAS / KCAS** is calibrated airspeed, the value the pilot's airspeed indicator shows; AFM/POH speeds are in KCAS. It equals TAS at sea level on a standard day, and is lower than TAS at altitude or on hot days.
- **VMCG** is the minimum control speed on the ground with one engine out. V1 can't be below it. It is not modelled.
- **VEF** is the speed at which the engine is assumed to fail, at least 1 s before V1. The model uses VEF = V1.

---

## 4. Industry abbreviations
| Abbreviation | Meaning |
|---|---|
| **AFM** | Airplane Flight Manual: certified performance data for transport aircraft |
| **POH** | Pilot's Operating Handbook: the light-aircraft equivalent of the AFM |
| **AEO** | All engines operating |
| **OEI** | One engine inoperative |
| **BFL** | Balanced field length: the distance where accelerate-go and accelerate-stop are equal |
| **TOFL** | Takeoff field length (certified): max(BFL, 1.15 × AEO TOD) |
| **TOD** | Takeoff distance: brake release to the takeoff screen height |
| **ASD** | Accelerate-stop distance: brake release, engine failure at V1, stop |
| **LD** | Landing distance: 50 ft screen height to full stop (unfactored) |
| **LDR** | Landing distance required: LD ÷ 0.6 (× 1.15 if wet) |
| **TORA** | Takeoff run available (runway declared distance) |
| **TODA** | Takeoff distance available: TORA + clearway |
| **ASDA** | Accelerate-stop distance available: TORA + stopway |
| **LDA** | Landing distance available: runway beyond any displaced threshold |
| **Displaced threshold** | Runway pavement before the landing threshold; usable for takeoff, not for landing |
| **Screen height** | Imaginary obstacle the aircraft must clear: takeoff 50 ft (Part 23) or 35 ft (Part 25); landing 50 ft for both |
| **Climb gradient** | Height gained per distance travelled, in % (tan γ × 100) |
| **Transition** | Curved flight path between liftoff and the steady climb |
| **Rotation** | Pitching up from VR to the liftoff attitude |
| **Glideslope** | Approach path angle, normally 3° |
| **Ground spoilers** | Wing panels that rise on touchdown or rejected takeoff to dump lift and load the brakes |
| **Reverse thrust** | Engine thrust redirected forward to help decelerate; not credited in certified dry-runway distances |
| **Free roll** | Time or distance between touchdown and full braking |
| **Flat rating** | Engine control holds rated thrust up to a set temperature (e.g. ISA+15); thrust drops only above it |
| **WAT limit** | Weight–altitude–temperature limit: the heaviest weight that still meets the OEI climb gradients |
| **ISA** | International Standard Atmosphere: 15 °C and 101,325 Pa at sea level, −6.5 °C per km |
| **ISA dev** | Temperature difference from ISA. "ISA+20" means 20 °C hotter than standard |
| **OAT** | Outside air temperature |
| **SL** | Sea level |
| **MTOW / MLW** | Maximum takeoff weight / maximum landing weight |
| **SLS** | Sea-level static: engine thrust at sea level, ISA, aircraft stationary |
| **TO / LDG / GND** | Takeoff / landing / ground |
| **ICAO** | Four-letter airport code (CYYZ, CYMX, KICT) |
| **°T** | Degrees true. METAR winds and the runway headings used here are true |
| **METAR** | Routine aviation weather report |
| **NOTAM** | Notice to air missions: e.g. a runway closure |
| **CFS** | Canada Flight Supplement: official Canadian runway and declared-distance data |
| **TCCA** | Transport Canada Civil Aviation: Bombardier's primary certifying authority |
| **CAR 525** | Canadian Aviation Regulations Part V, Standard 525: transport-category airworthiness (equivalent to 14 CFR Part 25) |
| **BFTC** | Bombardier Flight Test Center, Wichita, Kansas |
| **acft** | Aircraft (FAA abbreviation) |
| **EOM** | Equations of motion |

---

## 5. Aircraft classes (`aircraft.py`)

### Class hierarchy
```
Aircraft              base class: shared fields and methods; thrust() must be overridden
├── PropAircraft      propeller thrust model, Part 23 rules
└── JetAircraft       flat-rated turbofan model, spoilers, reverse thrust, Part 25 / CAR 525 rules
```
`C172` is a `PropAircraft` and `CL3500` (Challenger 3500) is a `JetAircraft`. Every saved profile is rebuilt as one of the two subclasses.

### Class variables
Class variables are shared by every instance of a class. They are not saved per aircraft.
| Name | `Aircraft` (base) | `PropAircraft` | `JetAircraft` | Meaning |
|---|---|---|---|---|
| `ENGINE_TYPE` | `"generic"` | `"prop"` | `"jet"` | Text label; also the key saved in the profile file |
| `TAKEOFF_SCREEN_HEIGHT_FT` | 50 | 50 | 35 | Takeoff screen height |
| `LANDING_SCREEN_HEIGHT_FT` | 50 | 50 | 50 | Landing screen height (all categories) |
| `FREE_ROLL_S` | 2 | 2 | 3 | Touchdown to full braking |
| `ROTATION_S` | 1 | 1 | 3 | VR to liftoff (Raymer: about 1 s small aircraft, 3 s large) |
| `LDR_FACTOR` | `None` | `None` | 1 / 0.6 ≈ 1.667 | LDR / LD (14 CFR 121.195); `None` = not applicable |
| `REV_CUTOFF_KT` | — | — | 60 | Reversers stowed below this speed |

### Instance variables (fields)
Instance variables are different for every aircraft and are saved in the profile file.
| Field | Class | Unit | Meaning |
|---|---|---|---|
| `name` | all | — | Aircraft name |
| `mtow_kg` | all | kg | Maximum takeoff weight, as mass |
| `mlw_kg` | all | kg | Maximum landing weight, as mass; 0 means the same as MTOW |
| `s_ref_m2` | all | m² | Reference wing area, S_ref |
| `cd0` | all | — | Zero-lift (parasite) drag coefficient, C_D0 |
| `k_induced` | all | — | Induced drag factor: C_D = C_D0 + k·C_L² |
| `cl_max_to` | all | — | Maximum lift coefficient, takeoff flaps |
| `cl_max_ldg` | all | — | Maximum lift coefficient, landing flaps |
| `cl_gnd` | all | — | Lift coefficient during the takeoff ground roll |
| `mu_roll` | all | — | Rolling friction coefficient, μ_roll |
| `mu_brake` | all | — | Braking friction coefficient on a dry runway, μ_brake |
| `sls_thrust_n` | all | N | Total sea-level static thrust, all engines |
| `n_engines` | all | — | Number of engines (jets: at least 2) |
| `max_power_w` | `PropAircraft` | W | Maximum shaft power at sea level, all engines |
| `eta_prop` | `PropAircraft` | — | Propeller efficiency, η_prop |
| `critical_alt_m` | `PropAircraft` | m | Turbocharger critical altitude; 0 = normally aspirated |
| `thrust_lapse` | `JetAircraft` | — | Thrust loss with Mach: T = T_SLS·σ_eff^0.7·(1 − lapse·M) |
| `rev_thrust_ratio` | `JetAircraft` | — | Reverse thrust as a fraction of SLS thrust |
| `flat_rating_isa_c` | `JetAircraft` | °C | Thrust is held constant up to this ISA deviation |

### Methods
| Method | Defined in | Overridden in | Returns |
|---|---|---|---|
| `__post_init__()` | `Aircraft`: MLW default, engine count check | `PropAircraft` (power check), `JetAircraft` (≥ 2 engines), both via `super()` | — |
| `engine_fraction(engines_operating)` | `Aircraft` | — | Share of thrust available: 1.0 AEO, (n−1)/n OEI |
| `stall_speed(weight_n, rho_kg_m3, cl_max)` | `Aircraft` | — | Stall speed, TAS [m/s] |
| `lift(tas_mps, rho_kg_m3, cl)` | `Aircraft` | — | Lift [N] |
| `drag(tas_mps, rho_kg_m3, cl)` | `Aircraft` | — | Drag [N] |
| `thrust(tas_mps, alt_m, isa_dev_c, engines_operating)` | `Aircraft` (raises `NotImplementedError`) | `PropAircraft`, `JetAircraft` | Forward thrust [N] |
| `cl_braking()` | `Aircraft` (returns `cl_gnd`) | `JetAircraft` (returns 0: spoilers) | C_L while braking |
| `reverse_thrust(tas_mps, use_reverse)` | `Aircraft` (returns 0) | `JetAircraft` | Reverse thrust [N] |
| `__str__()` | `Aircraft` | `PropAircraft` (adds hp via `super()`) | Text shown by `print(acft)` |

### Other names in `aircraft.py`
| Name | Meaning |
|---|---|
| `C172`, `SR22T`, `CL3500` | Built-in aircraft objects: Cessna 172S, Cirrus SR22T and Bombardier Challenger 3500 |
| `BUILT_IN` | `{name: object}` for the built-ins (never written to the profile file) |
| `AIRCRAFT_CLASSES` | `{"prop": PropAircraft, "jet": JetAircraft}`: finds the class from the text saved in a profile |
| `excess_c` | ISA deviation above the flat rating [°C] (jet thrust) |
| `sig_eff` | Density ratio used for thrust: at the excess temperature only (flat rating) |

---

## 6. Function arguments
| Argument | Unit | Meaning |
|---|---|---|
| `acft` | — | An `Aircraft` object |
| `apt`, `rwy` | — | An `Airport` and one of its `Runway` objects |
| `elev_m` | m | Field elevation (treated as pressure altitude) |
| `alt_m` | m | Pressure altitude (atmosphere and thrust functions) |
| `isa_dev_c` | °C | ISA deviation |
| `oat_c` | °C | Outside air temperature (runway analysis converts it to ISA dev) |
| `mass_kg`, `tow_kg`, `lw_kg` | kg | Mass; takeoff weight; landing weight (`None` = MTOW / MLW) |
| `hw_kt` | kt | Headwind component; negative means tailwind |
| `wind_dir_deg`, `wind_kt` | °T, kt | Wind direction (from) and speed |
| `slope_pct` | % | Runway slope in the direction of travel; + = uphill |
| `rwy_condition` | — | `"dry"` or `"wet"` |
| `engines_operating` | — | `None` = all engines; `n_engines − 1` = one engine out |
| `use_reverse` | — | Use reverse thrust when landing (jets) |
| `v1_mps` | m/s | Trial V1 for accelerate-go / accelerate-stop |
| `cond` | — | A `Conditions` object (see §8) |
| `result` | — | Result dictionary from a calculation |
| `n_curve_points` | — | Number of V1 points for the balanced-field chart |

---

## 7. Atmosphere (`atmosphere.py`)
| Name | Value | Meaning |
|---|---|---|
| `TEMP_SL_K` | 288.15 K | ISA sea-level temperature |
| `PRESS_SL_PA` | 101,325 Pa | ISA sea-level pressure |
| `RHO_SL_KG_M3` | 1.225 kg/m³ | ISA sea-level density |
| `LAPSE_RATE_K_PER_M` | 0.0065 K/m | Temperature drop with altitude in the troposphere |
| `R_AIR` | 287.05 J/(kg·K) | Specific gas constant for air |
| `G0_MPS2` | 9.80665 m/s² | Standard gravity |
| `GAMMA_AIR` | 1.4 | Ratio of specific heats for air |
| `ALT_MAX_M` | 11,000 m | Top of the troposphere (model limit) |
| `isa(alt_m, isa_dev_c)` | | Returns `temp_k, press_pa, rho_kg_m3` |
| `sigma(alt_m, isa_dev_c)` | | Density ratio σ = ρ / ρ_SL |
| `speed_of_sound(alt_m, isa_dev_c)` | | Speed of sound a = √(γRT) [m/s] |
| `temp_std_k` | K | Standard-day temperature at altitude, before ISA deviation |

---

## 8. Building blocks (`segments.py`)
**`Conditions` dataclass:** the day's numbers, built by `make_conditions()`.
| Field | Unit | Meaning |
|---|---|---|
| `elev_m`, `isa_dev_c` | m, °C | Field elevation, ISA deviation |
| `mass_kg`, `weight_n` | kg, N | Mass and weight |
| `rho_kg_m3` | kg/m³ | Air density |
| `hw_mps` | m/s | Headwind component |
| `slope_rad` | rad | Runway slope in the direction of travel (+ = uphill) |
| `mu_brake` | — | Braking μ for this runway condition (wet = 0.5 × dry) |
| `rwy_condition` | — | `"dry"` or `"wet"` |

**Functions**
| Function | Purpose |
|---|---|
| `make_conditions(acft, mass_kg, elev_m, isa_dev_c, hw_kt, slope_pct, rwy_condition)` | Build a `Conditions` object |
| `accelerate(acft, cond, tas_target_mps, gs_start_mps, dist_start_m, engines_operating)` | Ground roll until TAS reaches the target. Returns `(dist_end_m, time_s, solution)` |
| `climb_to_screen(acft, cond, vs1_mps, screen_height_ft, engines_operating)` | Transition arc and climb to the screen height. Returns `(air_dist_m, climb_grad_pct)` |
| `decelerate(acft, cond, gs_start_mps, dist_start_m, cl, use_reverse)` | Braking roll to a stop at idle thrust. Returns `(dist_end_m, time_s, solution)` |
| `_gravity_along_runway(cond)` | Weight component along a sloped runway [N] |
| `equations_of_motion(t_s, y)` | EOM passed to `solve_ivp`: returns `[gs_mps, accel_mps2]` |
| `reached_target()`, `stopped()` | Integration events: TAS reached / ground speed ≈ 0 |

**Variables inside the calculations**
| Name | Unit | Meaning |
|---|---|---|
| `t_s`, `y` | s, — | Time and state vector `[dist_m, gs_mps]` |
| `dist_m` | m | Distance along the runway |
| `lift_n`, `drag_n`, `thrust_n` | N | Aerodynamic and propulsive forces |
| `friction_n` | N | Rolling friction, μ_roll·(W − L) |
| `brake_n` | N | Braking friction, μ_brake·(W − L) |
| `rev_n` | N | Reverse thrust applied at this instant |
| `accel_mps2` | m/s² | Acceleration along the runway |
| `q_pa`, `q_climb_pa` | Pa | Dynamic pressure q = ½ρV² (in `lift()` / `drag()`; at V2) |
| `cl_climb`, `drag_climb_n`, `thrust_climb_n` | —, N, N | Lift coefficient, drag and thrust in the climb at V2 |
| `sin_gamma`, `gamma_rad` | —, rad | Climb angle γ |
| `radius_m` | m | Transition arc radius, R = V_TR² / (g·(n − 1)) |
| `h_transition_m`, `s_transition_m`, `s_climb_m` | m | Height and distance in the arc; distance in the steady climb |
| `screen_height_m` | m | Screen height |
| `cl_braking` | — | Lift coefficient while braking |
| `tas_reached_mps` | m/s | Highest TAS reached before giving up (error message) |
| `solution` | — | Object returned by `scipy.integrate.solve_ivp` |

**Variables in the thrust models**
| Name | Unit | Meaning |
|---|---|---|
| `sig` | — | Density ratio σ |
| `mach` | — | Mach number, M = TAS / a |
| `power_avail_w` | W | Shaft power available at altitude |
| `thrust_cap_n` | N | Static-thrust cap at altitude (prop model) |
| `thrust_prop_n` | N | η·P/V thrust before the cap (prop model) |

---

## 9. Takeoff, BFL and landing
### `takeoff()` result keys (all engines)
| Key | Unit | Meaning |
|---|---|---|
| `acft_name`, `mass_kg` | —, kg | Aircraft and takeoff mass used |
| `vs1_mps`, `vr_mps`, `v2_mps` | m/s | V-speeds (TAS) |
| `ground_roll_m`, `ground_roll_s` | m, s | Brake release to liftoff, including rotation |
| `climb_grad_pct` | % | AEO climb gradient at V2 |
| `screen_height_ft` | ft | 50 or 35 ft |
| `air_dist_m` | m | Liftoff to the screen height |
| `tod_m` | m | **Takeoff distance**, all engines |
| `t_hist_s`, `dist_hist_m`, `tas_hist_mps` | s, m, m/s | Time histories of the ground roll to VR |

Also in `takeoff.py`: `takeoff_speeds()` returns `(vs1, vr, v2)`; `rotation_distance()` gives the ground distance from VR to liftoff; `dist_vr_m` and `time_vr_s` are the roll to VR.

### `balanced_field()` (`bfl.py`)
| Function | Purpose |
|---|---|
| `accelerate_go(acft, cond, v1_mps)` | AEO to V1, OEI to VR, OEI rotation, OEI air distance to 35 ft. Returns `(distance_m, oei_climb_grad_pct)` |
| `accelerate_stop(acft, cond, v1_mps)` | AEO to V1, 2 s at V1, maximum braking (spoilers, idle, no reverse). Returns distance [m] |
| `balanced_field(...)` | Solves for the V1 where go = stop (`scipy.optimize.brentq`) |
| `go_minus_stop(v1_mps)` | The function brentq drives to zero |
| `plot_bfl(result, filename, runway, extra_conditions)` | Balanced Field Length (BFL) chart: go and stop vs. V1, sidebar tables, optional TODA/ASDA line |
| `conditions_rows()` | Rows for the chart's Conditions table |
| `print_bfl()`, `run_bfl_interactive()` | Print / prompt |

| Result key | Unit | Meaning |
|---|---|---|
| `v1_mps` | m/s | Balanced V1 (TAS) |
| `balance_note` | — | `"balanced"` or why it couldn't balance |
| `todg_oei_m` | m | Accelerate-go distance at V1 (OEI takeoff distance) |
| `asd_m` | m | Accelerate-stop distance at V1 |
| `bfl_m` | m | Balanced field length |
| `oei_climb_grad_pct` | % | OEI climb gradient at V2, gear down |
| `tod_aeo_m`, `tod_aeo_factored_m` | m | AEO TOD and 1.15 × AEO TOD |
| `tofl_m` | m | **Takeoff field length** = max(BFL, 1.15 × AEO TOD) |
| `tofl_limit` | — | Which case sets the TOFL |
| `v1_curve_mps`, `go_curve_m`, `stop_curve_m` | m/s, m | Curves for the chart |
| `v1_low_mps`, `v1_high_mps`, `diff_low_m`, `diff_high_m` | m/s, m | V1 search range and go − stop at each end |
| `dist_v1_m`, `dist_vr_m`, `dist_lof_m`, `dist_brake_start_m`, `dist_stop_m` | m | Distances at V1, VR, liftoff, start of braking, stop |
| `gs_v1_mps` | m/s | Ground speed at V1 |
| `oei` | — | Engines still running after the failure (n − 1) |
| `v1_bal_kt`, `vr_kt`, `bfl_ft`, `aeo_ft`, `tofl_ft`, `v1_kt`, `go_ft`, `stop_ft` | kt, ft | Plot values |
| `i_go`, `i_stop` | — | Curve points where the direct labels are placed |
| `aeo_limits`, `aeo_label` | — | Whether the AEO × 1.15 line sets the TOFL, and its label |
| `limits`, `limits_ft`, `y_top`, `y_bottom` | —, ft | Runway limit lines and the y-axis range |
| `ax_side`, `grid`, `wide` | — | Sidebar axes, figure layout, results table column widths |
| `elev_txt`, `isa_txt`, `wind_txt` | — | Values for the Conditions table |
| `wind_factored` | — | Result key set by runway analysis: the wind shown is factored (50% / 150%) |

### `landing()` result keys
| Key | Unit | Meaning |
|---|---|---|
| `acft_name`, `mass_kg` | —, kg | Aircraft and landing mass used |
| `engine_type`, `rev_used`, `rwy_condition` | — | `"prop"`/`"jet"`; reverse used; dry/wet |
| `vs0_mps`, `vref_mps`, `vtd_mps` | m/s | V-speeds (TAS) |
| `screen_height_ft` | ft | 50 ft |
| `air_dist_m` | m | 50 ft to touchdown on a 3° glideslope |
| `free_roll_m`, `free_roll_s` | m, s | Touchdown to full braking |
| `braking_roll_m`, `braking_s` | m, s | Full braking to stop |
| `ground_roll_m` | m | Free roll + braking roll |
| `ld_m` | m | **Landing distance** (unfactored) |
| `ldr_m` | m | **Landing distance required** = LD ÷ 0.6 (jets; otherwise `None`) |
| `gs_td_mps` | m/s | Ground speed at touchdown |
| `t_hist_s`, `dist_hist_m`, `tas_hist_mps` | s, m, m/s | Time histories of the braking roll |

---

## 10. Airports and runway analysis
### `Runway` and `Airport` (`airports.py`)
| Field | Unit | Meaning |
|---|---|---|
| `Runway.rwy_id` | — | Designator for one direction, e.g. `"05"`, `"24R"` |
| `Runway.hdg_true_deg` | °T | Runway true heading |
| `Runway.tora_m`, `toda_m`, `asda_m`, `lda_m` | m | Declared distances |
| `Runway.slope_pct` | % | Average slope in this direction (+ = uphill) |
| `Airport.icao`, `name` | — | ICAO code and name |
| `Airport.elev_m` | m | Airport elevation |
| `Airport.runways` | — | List of `Runway` objects (each direction separately) |
| `Airport.note` | — | Free text, e.g. which Bombardier facility is there |

| Name | Meaning |
|---|---|
| `CYYZ`, `CYMX`, `KICT` | Built-in airports: Toronto Pearson, Montréal-Mirabel, Wichita (BFTC) |
| `BUILT_IN_AIRPORTS`, `airports` | Built-ins / all airports in memory `{icao: Airport}` |
| `AIRPORT_FILE` | `airports.json`: user airports |
| `runway_pair()` | Builds both directions of one runway from length, headings, displaced thresholds and slope |
| `wind_components(wind_dir_deg, wind_kt, rwy_hdg_deg)` | Returns `(hw_kt, xw_kt)` |
| `Airport.runway(rwy_id)` | Finds a runway by designator |
| `airport_menu()`, `create_airport()`, `show_airport()`, `choose_airport()`, `choose_runway()`, `delete_airport()` | Menu actions |
| `_create_runways()`, `_ask_float()`, `_airport_from_dict()` | Private helpers |
| `load_airports()` / `save_airports()` | Read / write `airports.json` |
| `id_1`, `id_2`, `hdg_1`, `hdg_1_deg`, `hdg_2_deg` | Designators and headings of the two directions |
| `disp_1`, `disp_2`, `disp_1_ft`, `disp_2_ft` | Displaced thresholds at each end [ft] |
| `slope_1`, `slope_1_pct` | Slope in direction 1 [%] |
| `length_ft`, `length_m` | Runway length |
| `angle_rad` | Angle between the wind and the runway |
| `pair`, `chosen`, `chosen_rwy`, `new_apt`, `selected`, `codes`, `tag` | Menu helpers |

### `analyze_runway()` (`runway_analysis.py`)
| Name | Meaning |
|---|---|
| `HEADWIND_CREDIT` = 0.5, `TAILWIND_PENALTY` = 1.5 | 25.105(d): use 50% of a headwind and 150% of a tailwind |
| `WET_LDR_FACTOR` = 1.15 | 121.195(d): wet LDR = 115% of dry LDR |
| `TAILWIND_LIMIT_KT` = 10 | Typical certified tailwind limit (warning only) |
| `factored_headwind()` | Applies the 50% / 150% factors |
| `isa_dev_from_oat()` | OAT → ISA deviation at the airport elevation |
| `hw_perf_kt` | Factored headwind used in the calculations |
| `common` | Conditions shared by the takeoff and landing calls |
| `takeoff_mode` | `"balanced field …"` (multi-engine) or `"all engines …"` (single) |
| `tod_req_m`, `asd_req_m` | Required takeoff distance and accelerate-stop distance |
| `takeoff_checks`, `landing_checks` | Lists of `(name, required_m, available_name, available_m)` |
| `takeoff_ok`, `landing_ok` | Overall pass / fail |
| `warnings` | Messages such as an excessive tailwind |
| `ld_dry` | Dry-runway landing result, used for the wet LDR |
| `bfl`, `to`, `ld` | Results of `balanced_field()`, `takeoff()`, `landing()` |
| `req_m`, `avail_name`, `avail_m` | One check: required distance, which declared distance, available distance |
| `check_line()`, `mark`, `margin_ft`, `side`, `hw_txt`, `verdict_to`, `verdict_ld`, `label` | Report formatting |
| `print_runway_analysis()`, `run_runway_analysis_interactive()` | Print / prompt |
| `save_bfl_chart()` | Saves a balanced-field chart for this runway and day, with TODA / ASDA drawn on it |
| `extra`, `rwy_condition` | Airport, runway, OAT and wind rows for the chart's Conditions table; dry/wet |

---

## 11. Model constants
| Constant | File | Value | Meaning |
|---|---|---|---|
| `VR_FACTOR` | takeoff | 1.1 | VR / VS1 |
| `V2_FACTOR` | takeoff | 1.2 | V2 / VS1 |
| `V_TR_FACTOR` | segments | 1.15 | V_TR / VS1 |
| `TRANSITION_LOAD_FACTOR` | segments | 1.2 | Load factor in the transition arc |
| `STOP_DELAY_S` | bfl | 2 | 25.109: 2 s at V1 before the stop is effective |
| `AEO_TOD_FACTOR` | bfl | 1.15 | 25.113: TOD ≥ 115% of AEO distance |
| `V1_MIN_FRACTION` | bfl | 0.5 | Lowest V1 searched, as a fraction of VR |
| `WET_MU_BRAKE_FACTOR` | segments | 0.5 | Wet braking μ = 0.5 × dry (simplified) |
| `RWY_CONDITIONS` | segments | `("dry", "wet")` | Allowed runway conditions |
| `VREF_FACTOR` | landing | 1.3 | VREF / VS0 |
| `VTD_FACTOR` | landing | 1.15 | VTD / VS0 |
| `GLIDESLOPE_DEG` | landing | 3.0 | Approach path angle |
| `STOPPED_MPS` | segments | 0.1 | Speed treated as "stopped" |
| `T_MAX_S` | segments | 300 | Integration time limit |
| `MAX_STEP_S` | segments | 0.5 | Integration step limit (0.1 gives the same result to 0.1 ft) |
| `PROFILE_FILE` | profiles | `aircraft_profiles.json` | Saved aircraft |

Type-specific values (screen heights, free roll, rotation, LDR factor, reverser cutoff) are class variables, listed in §5.

---

## 12. Exceptions (`exceptions.py`)
```
Exception
└── PerformanceError                    base class: main.py catches this one
    ├── InsufficientThrustError         aircraft never reaches the target speed
    ├── ClimbPerformanceError           thrust at V2 does not exceed drag (all engines or OEI)
    └── AtmosphereRangeError            altitude outside 0 - 11,000 m
                                        (also inherits ValueError: multiple inheritance)
```
| Name | Raised by | Extra attributes |
|---|---|---|
| `PerformanceError` | (base class only) | — |
| `InsufficientThrustError` | `accelerate()` | `acft_name`, `tas_reached_mps`, `vlof_mps` (the target speed) |
| `ClimbPerformanceError` | `climb_to_screen()` | `acft_name`, `climb_grad_pct` |
| `AtmosphereRangeError` | `isa()` | `alt_m` |
| `NotImplementedError` (built-in) | `Aircraft.thrust()` | — raised if a subclass forgets to override it |
| `ValueError` (built-in) | `balanced_field()`, `make_conditions()`, `__post_init__()` | single-engine BFL, bad runway condition, bad aircraft data |
| `json.JSONDecodeError` (built-in) | `load_profiles()`, `load_airports()` | caught: damaged file, so the built-ins are used |
| `__init__()` | each custom exception | Constructor: stores the extra attributes, then calls `super().__init__(message)` |
| `alt_max_m` | `AtmosphereRangeError` | Upper altitude limit, used in the message |
| `err` | `main.py` | The caught exception object |

---

## 13. Unit conversion functions (`units.py`)
| Function | Converts |
|---|---|
| `ft_to_m()` / `m_to_ft()` | feet ↔ metres |
| `ft2_to_m2()` / `m2_to_ft2()` | ft² ↔ m² |
| `kt_to_mps()` / `mps_to_kt()` | knots ↔ m/s |
| `lb_to_kg()` / `kg_to_lb()` | pounds (mass) ↔ kilograms |
| `lbf_to_n()` / `n_to_lbf()` | pounds-force ↔ newtons |
| `hp_to_w()` / `w_to_hp()` | horsepower ↔ watts |
| `c_to_k()` / `k_to_c()` | °C ↔ K (absolute temperatures only) |

Every function accepts a single number or a NumPy array. The raw factors are private constants: `_M_PER_FT`, `_MPS_PER_KT`, `_KG_PER_LB`, `_N_PER_LBF`, `_W_PER_HP`, `_K_AT_0C`.

---

## 14. Profiles, menu and sensitivity
**`profiles.py`**
| Name | Meaning |
|---|---|
| `profiles` | In-memory dict of all loaded aircraft `{name: Aircraft}` |
| `COMMON_QUESTIONS`, `PROP_QUESTIONS`, `JET_QUESTIONS` | `(field, prompt, unit shown, min, max)` for each question |
| `EXTRA_QUESTIONS` | `{PropAircraft: PROP_QUESTIONS, JetAircraft: JET_QUESTIONS}` |
| `CONVERTERS` | `{unit shown: (to SI function, from SI function)}` |
| `_identity()` | Returns its input unchanged: the "conversion" for dimensionless values |
| `questions_for(acft_class)` | Questions for `PropAircraft` or `JetAircraft` |
| `_build_aircraft()` | Rebuild a saved profile as the right subclass |
| `load_profiles()` / `save_profiles()` | Read / write `aircraft_profiles.json` (user profiles only) |
| `menu()`, `create_profile()`, `show_profile()`, `choose_profile()`, `delete_profile()`, `ask_number()` | Menu actions and prompt |
| `acft_class`, `template`, `allowed` | Chosen class; built-in used for defaults; field names the class accepts |
| `to_si`, `from_si`, `default_shown`, `value_shown` | Conversion functions; default and entered value in the unit shown |
| `user_input`, `prompt`, `default`, `min_value`, `max_value` | Prompt helpers |

**`main.py`**: `main()` is the top-level menu and the program's entry point.

**`takeoff.py` / `landing.py`**: `ask()` prompts for a number with a default; `run_takeoff_interactive()` and `run_landing_interactive()` ask for conditions, run and print; `print_takeoff()` and `print_landing()` print results. `wet` is the yes/no answer for a wet runway.

**`sensitivity.py`**
| Name | Meaning |
|---|---|
| `takeoff_metric_m()` | TOFL for multi-engine aircraft, AEO TOD for single-engine |
| `landing_metric_m()` | Unfactored LD with no reverse thrust credit |
| `takeoff_label()` | `"TOFL"` or `"TOD"` |
| `run_sweeps()`, `plot_sensitivity()`, `print_summary()` | Sweeps, 2×2 plot, % change table |
| `SWEEPS`, `PANELS`, `sweeps` | Sweep ranges; panel titles; how each sweep sets the conditions |
| `results` | `{sweep name: (x_values, to_ft, ld_ft)}` |
| `x_values`, `to_m`, `ld_m`, `to_ft`, `ld_ft` | Swept values and the resulting distances |
| `to_conditions` | Conditions for one sweep point |
| `base_to_ft`, `base_ld_ft` | Baseline distances for the % changes |
| `TO_COLOR`, `LD_COLOR` | Takeoff (blue) and landing (orange) colours, from `plot_style` |
| `is_multi`, `base_x`, `x0`, `i0` | Multi-engine flag; baseline value of each sweep; its index |
| `outer`, `charts`, `ax_side` | Figure layout: 2×2 chart grid and the sidebar |
| `change_rows` | The five changes listed in the Change From Baseline table |
| `to_abbr`, `to_name`, `summary` | "TOFL"/"TOD", its full name, and the Change From Baseline table rows |
| `y_all`, `pad`, `min_gap`, `label_y`, `upper`, `lower`, `mid`, `x_text`, `y_to`, `y_ld`, `i_end`, `pct` | End-label placement: keeps the two labels at each end from overlapping |
| `dx`, `span` | Label offset direction; x-axis range of the sweep |

**`plot_style.py`:** one look for every chart. House rules:
1. Roboto font, bundled in `fonts/`
2. Titles and labels in Title Case
3. Abbreviations written as Full Name (ABBR)
4. Chart on the left, with Conditions and Results tables in a sidebar on the right
5. Solid dark left and bottom axis lines with visible tick marks

| Name | Meaning |
|---|---|
| `use_style()` | Sets fonts, colours and axis defaults |
| `title_case(text)` | Capitalizes every word (also after hyphens); leaves abbreviations and units as written |
| `style_axes(ax, title, xlabel, ylabel)` | Grid, frame and number format; applies Title Case to the title and labels |
| `add_metres_axis(ax)` | Second y-axis showing the same distances in metres (`ax_m`) |
| `figure_title(fig, title)` | One bold Title Case title, top left |
| `draw_table(ax, top, heading, rows, col_headers, col_widths, row_height_in, swatches)` | Bordered sidebar table: dark header bar, alternating rows, optional colour swatches |
| `footnote(fig, text)` | Small note along the bottom edge |
| `table_height(ax, rows, col_headers, row_height_in)` | Height a table will take in the sidebar |
| `stack_tables(ax, tables)` | Draws all sidebar tables so the first starts level with the top of the charts and the last ends level with their bottom; rows grow to fill, equal gaps between tables (`fill_row_in`, `max_row_height_in`, `n_rows`, `n_gaps`, `heights`) |
| `align_layout(fig, plot_axes, side_ax, title_text, foot_text)` | Lines up the layout: title and footnote start at the charts' left edge, sidebar matches the plot areas top to bottom, right margin mirrors the left (`renderer`, `inv`, `fig_box()`, `tight`, `left`, `top_tight`, `bottom_tight`, `plot_top`, `plot_bottom`) |
| `title_text`, `foot` | The title and footnote Text objects passed to `align_layout()` |
| `_register_project_fonts()`, `FONT_DIR` | Loads the bundled Roboto files from the `fonts/` folder |
| `_KEEP_AS_IS` | Units and symbols that `title_case()` never changes |
| `AXIS` | Colour of the solid axis lines and tick marks |
| `BLUE`, `ORANGE`, `INK`, `INK_2`, `INK_3`, `GRID`, `GRID_MINOR`, `PANEL`, `HEADER_FILL`, `ROW_FILL`, `LIMIT_RED`, `FONT_FAMILY` | Colours and fonts |
| `core`, `part`, `fix()` | Word handling inside `title_case()` |
| `ax_h_in`, `row_h`, `n_cols`, `x_edges`, `x_label`, `table_h` | Table geometry inside `draw_table()` |

**Input/output values (non-SI, suffix shows the unit):** `elev_ft`, `mass_lb`, `tow_lb`, `lw_lb`, `weight_pct`.

Short-lived formatting and plotting locals (`axes`, `ax`, `fig`, `labels`, `title`, `rows`, `idx`, `value_txt`, `unit_txt`, `default_txt`, `rev_txt`, `wet_txt`, `filename`) follow ordinary Python naming and are not listed.

---

## 15. Regulations referenced
| Reference | Covers |
|---|---|
| **14 CFR Part 23** | Normal-category (light) aircraft; 50 ft takeoff screen height |
| **14 CFR Part 25 / CAR 525** | Transport-category aircraft (US / Canada); 35 ft takeoff screen height |
| **25.105** | Takeoff: wind factors (50% headwind, 150% tailwind) and runway slope |
| **25.107** | Takeoff speeds: V1 ≤ VR, V2 ≥ 1.2 VS (simplified) |
| **25.109** | Accelerate-stop distance, including the 2 s allowance at V1 |
| **25.111** | Takeoff path (OEI from VEF) |
| **25.113** | Takeoff distance: max(OEI distance, 115% of AEO distance) |
| **25.125** | Landing distance from 50 ft |
| **121.195(b), (d)** | Dispatch: landing within 60% of the runway; wet runway 115% |
| **ICAO Doc 7488** | Manual of the ICAO Standard Atmosphere |

## Report generator (`report/make_examples.py`)
| Name | Meaning |
|---|---|
| `make_examples.py` | Runs each step of the model for one aircraft and writes the numbers into LaTeX |
| `examples_challenger_3500.tex`, `examples_cirrus_sr22t.tex` | Generated worked examples, read by `performance_model.tex` with `\input` |

## Flowcharts (`flowcharts/`)
| Name | Meaning |
|---|---|
| `flowcharts.html` | Source of both flowcharts; open in a browser to view and rearrange |
| `make_flowcharts.py` | Exports the charts to PNG and PDF |
| `calculation_flow.png` | How one runway check is computed, inputs to OK / limited |
| `program_flow.png` | What `main.py` does: menu loop, function per option, error handling |
| Symbols | Rounded = start / end; rectangle = process; double-sided rectangle = function call; diamond = decision; parallelogram = input / output; cylinder = saved file; dashed red = error |
