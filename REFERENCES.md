# References

Every source the model's methods and data come from. The code cites them by the **key** in square brackets, e.g. `[RAYMER] Ch. 17`, in each file header and in the docstring of the function that uses them.

> Chapter numbers refer to the editions listed. Check them against your own copies, since chapter numbering changes between editions.

## Textbooks
| Key | Reference | Used for |
|---|---|---|
| **[ANDERSON-APD]** | Anderson, J. D., *Aircraft Performance and Design*, McGraw-Hill, 1999. Ch. 6 | Takeoff and landing equations of motion, ground-roll forces, drag polar, stall speed |
| **[ANDERSON-ITF]** | Anderson, J. D., *Introduction to Flight*, 8th ed., McGraw-Hill, 2016. Ch. 3 | International Standard Atmosphere equations, speed of sound |
| **[RAYMER]** | Raymer, D. P., *Aircraft Design: A Conceptual Approach*, 6th ed., AIAA, 2018. Ch. 17 | Transition arc (n = 1.2, V_TR = 1.15 VS), rotation time, rolling and braking friction, V-speed ratios |
| **[TORENBEEK]** | Torenbeek, E., *Synthesis of Subsonic Airplane Design*, Delft University Press / Kluwer, 1982 | Balanced field length: accelerate-go vs. accelerate-stop |
| **[FILIPPONE]** | Filippone, A., *Advanced Aircraft Flight Performance*, Cambridge University Press, 2012 | Jet takeoff with engine failure, turbofan thrust lapse, flat rating |
| **[MAIR-BIRDSALL]** | Mair, W. A. and Birdsall, D. L., *Aircraft Performance*, Cambridge University Press, 1992 | Engine-out takeoff analysis, balanced field length |
| **[OJHA]** | Ojha, S. K., *Flight Performance of Aircraft*, AIAA, 1995 | Takeoff and landing with runway slope and wind |
| **[GUDMUNDSSON]** | Gudmundsson, S., *General Aviation Aircraft Design: Applied Methods and Procedures*, Butterworth-Heinemann, 2014 | Propeller thrust (T = ηP/V with a static-thrust limit); light-aircraft takeoff |

## Industry guidance
| Key | Reference | Used for |
|---|---|---|
| **[AIRBUS-GTG]** | Airbus, *Getting to Grips with Aircraft Performance*, Flight Operations Support & Line Assistance, 2002 | V1, balanced field, declared distances (TORA/TODA/ASDA/LDA), wind factoring, wet runways, reverse thrust credit |

## Regulations and standards
| Key | Reference | Used for |
|---|---|---|
| **[14CFR23]** | 14 CFR Part 23, Airworthiness Standards: Normal Category Airplanes | 50 ft takeoff screen height (light aircraft) |
| **[14CFR25]** | 14 CFR Part 25, Airworthiness Standards: Transport Category Airplanes. §25.105, .107, .109, .111, .113, .125 | Wind factors and slope, takeoff speeds, accelerate-stop (2 s at V1), takeoff path, TOFL = max(BFL, 1.15 × AEO), landing from 50 ft |
| **[CAR525]** | Transport Canada, Canadian Aviation Regulations, Standard 525 (Transport Category Aeroplanes) | Canadian equivalent of Part 25 |
| **[14CFR121]** | 14 CFR §121.195, Landing limitations | LDR = LD ÷ 0.6; wet runway × 1.15 |
| **[ICAO-7488]** | ICAO Doc 7488/3, *Manual of the ICAO Standard Atmosphere*, 1993 | ISA constants |
| **[ICAO-A14]** | ICAO Annex 14, *Aerodromes*, Vol. I | Definitions of declared distances |
| **[NIST-811]** | NIST Special Publication 811, *Guide for the Use of the International System of Units*, 2008. App. B | Unit conversion factors |

## Data sources
| Key | Reference | Used for |
|---|---|---|
| **[C172-POH]** | Cessna Model 172S *Pilot's Operating Handbook*, Section 5 | C172S weights, power, validation distances |
| **[BBD-CL3500]** | Bombardier, *Challenger 3500 Factsheet*, 2024 | Thrust, flat rating, published takeoff and landing distances |
| **[AOPA-CL350]** | AOPA Aircraft Guide, *Bombardier Challenger 350*; AeroCorner, *Bombardier Challenger 350* | Challenger MTOW and MLW |
| **[AOPA-SR22T]** | AOPA Aircraft Guide, *Cirrus SR22T* | SR22T MTOW, power, VS0, published takeoff and landing distances |
| **[OURAIRPORTS]** | OurAirports runway database (ourairports.com), accessed 2026-10-21 | Runway lengths, true headings, displaced thresholds, threshold elevations |
| **[WIKI-APT]** | Wikipedia articles: Toronto Pearson, Montréal–Mirabel | Airport elevations |

## Methods that are simplifications (no single source)
- Flat-rated thrust as σ evaluated only above ISA + 15 °C, with T ∝ σ^0.7 (1 − k·M): simplified from [FILIPPONE]
- Wet runway as 0.5 × dry braking friction: simplified from [AIRBUS-GTG]
- Challenger wing area and aerodynamic coefficients: engineering estimates; `cl_max_to` calibrated to [BBD-CL3500]
- SR22T static thrust calibrated to the 1,517 ft ground roll in [AOPA-SR22T]; 25,000 ft turbo critical altitude is assumed
