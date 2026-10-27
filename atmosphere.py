"""
Module:   atmosphere
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    International Standard Atmosphere, troposphere only (0 to 11 km), with an
    ISA deviation for hot and cold days.

Basis:
    Anderson, Introduction to Flight, Ch. 3; ICAO Doc 7488
"""

from exceptions import AtmosphereRangeError

# ISA sea-level constants [ICAO-7488]
TEMP_SL_K = 288.15
PRESS_SL_PA = 101325.0
RHO_SL_KG_M3 = 1.225
LAPSE_RATE_K_PER_M = 0.0065
R_AIR = 287.05                # J/(kg·K)
G0_MPS2 = 9.80665
GAMMA_AIR = 1.4

ALT_MAX_M = 11000.0           # tropopause; above this the temperature stops falling


def isa(alt_m, isa_dev_c=0.0):
    """
    Returns (temp_k, press_pa, rho_kg_m3) at pressure altitude alt_m.

    alt_m     : pressure altitude [m], valid 0 - 11000 m
    isa_dev_c : ISA deviation [°C], e.g. 20 means an ISA+20 hot day

    """
    if alt_m < 0 or alt_m > ALT_MAX_M:
        raise AtmosphereRangeError(alt_m, ALT_MAX_M)

    temp_std_k = TEMP_SL_K - LAPSE_RATE_K_PER_M * alt_m

    # Pressure altitude is defined on the standard profile, so a hot or cold day
    # changes temperature and density but not pressure.
    press_pa = PRESS_SL_PA * (temp_std_k / TEMP_SL_K) ** (G0_MPS2 / (LAPSE_RATE_K_PER_M * R_AIR))

    temp_k = temp_std_k + isa_dev_c
    rho_kg_m3 = press_pa / (R_AIR * temp_k)
    return temp_k, press_pa, rho_kg_m3


def sigma(alt_m, isa_dev_c=0.0):
    """Density ratio σ = ρ / ρ_SL. Used to scale engine power with altitude."""
    return isa(alt_m, isa_dev_c)[2] / RHO_SL_KG_M3


def speed_of_sound(alt_m, isa_dev_c=0.0):
    """Speed of sound a = sqrt(γ R T) [m/s]."""
    temp_k = isa(alt_m, isa_dev_c)[0]
    return (GAMMA_AIR * R_AIR * temp_k) ** 0.5
