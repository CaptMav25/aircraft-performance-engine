"""
Module:   exceptions
Project:  Aircraft Performance Engine
Author:   M. Barsoum

Purpose:
    Errors the model raises on purpose. All inherit from PerformanceError, so
    the menu can catch them with one except clause.
"""


class PerformanceError(Exception):
    """Base class for every error raised by the performance model."""


class InsufficientThrustError(PerformanceError):
    """The aircraft cannot accelerate to liftoff speed."""

    def __init__(self, acft_name, tas_reached_mps, vlof_mps):
        self.acft_name = acft_name
        self.tas_reached_mps = tas_reached_mps
        self.vlof_mps = vlof_mps
        super().__init__(
            f"{acft_name} never reaches VLOF: it only reaches "
            f"{tas_reached_mps:.1f} m/s TAS, but VLOF is {vlof_mps:.1f} m/s."
        )


class ClimbPerformanceError(PerformanceError):
    """Thrust at V2 does not exceed drag, so the aircraft cannot climb."""

    def __init__(self, acft_name, climb_grad_pct):
        self.acft_name = acft_name
        self.climb_grad_pct = climb_grad_pct
        super().__init__(
            f"{acft_name} cannot climb at V2: climb gradient would be {climb_grad_pct:.1f} %."
        )


class AtmosphereRangeError(PerformanceError, ValueError):
    """
    Altitude is outside the troposphere model.
    Inherits from BOTH PerformanceError and ValueError (multiple inheritance),
    so code that catches either one will catch it.
    """

    def __init__(self, alt_m, alt_max_m):
        self.alt_m = alt_m
        super().__init__(f"Altitude {alt_m:.0f} m is outside the ISA model (0 - {alt_max_m:.0f} m).")
