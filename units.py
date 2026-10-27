"""
Module:   units
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Unit conversions, named <from>_to_<to>(), e.g. ft_to_m(5000) = 1524.0.
    Every factor in the project is defined once, here.

Basis:
    NIST Special Publication 811, App. B
"""

# Use the functions below, not these factors directly.
_M_PER_FT = 0.3048                 # exact
_MPS_PER_KT = 1852.0 / 3600.0      # exact (1 NM = 1852 m)
_KG_PER_LB = 0.45359237            # exact (pound-mass)
_N_PER_LBF = 4.4482216152605       # exact (pound-force)
_W_PER_HP = 745.69987158227        # mechanical horsepower
_K_AT_0C = 273.15                  # exact


def ft_to_m(ft):
    return ft * _M_PER_FT


def m_to_ft(m):
    return m / _M_PER_FT


def ft2_to_m2(ft2):
    return ft2 * _M_PER_FT**2


def m2_to_ft2(m2):
    return m2 / _M_PER_FT**2


def kt_to_mps(kt):
    return kt * _MPS_PER_KT


def mps_to_kt(mps):
    return mps / _MPS_PER_KT


def lb_to_kg(lb):
    return lb * _KG_PER_LB


def kg_to_lb(kg):
    return kg / _KG_PER_LB


def lbf_to_n(lbf):
    return lbf * _N_PER_LBF


def n_to_lbf(n):
    return n / _N_PER_LBF


def hp_to_w(hp):
    return hp * _W_PER_HP


def w_to_hp(w):
    return w / _W_PER_HP


# Absolute temperatures only. A temperature difference is the same in °C and K.
def c_to_k(c):
    return c + _K_AT_0C


def k_to_c(k):
    return k - _K_AT_0C
