# Copyright (c) 2026 Sergiy Duras <sergiy@duras.org>
# SPDX-License-Identifier: ISC
#
"""Geocentric lunar ephemeris computation. Computes the Moon's
geocentric ecliptic position and phase from a Unix timestamp using
Keplerian orbital elements with empirical perturbation corrections.
Depends only on the standard `math` module. No file I/O, no state.
Validity interval: 1900-01-01 through 2100-12-31.

Origin: OCaml msts library,
https://codeberg.org/duras/msts

Reference: Paul Schlyter, "Planetary Positions",
http://www.stjarnhimlen.se/comp/ppcomp.html
"""

__version__ = "0.1.0"

from math import atan2, cos, fmod, isinf, isnan, pi, sin, sqrt

_SCHLYTER_EPOCH_OFFSET_DAYS = 10956.0

_SUN_PERIHELION_BASE_DEG = 282.9404
_SUN_PERIHELION_RATE = 4.70935e-5

_SUN_ECCENTRICITY_BASE = 0.016709
_SUN_ECCENTRICITY_RATE = -1.151e-9

_SUN_MEAN_ANOMALY_BASE_DEG = 356.0470
_SUN_MEAN_ANOMALY_RATE = 0.9856002585

_MOON_NODE_BASE_DEG = 125.1228
_MOON_NODE_RATE = -0.0529538083

_MOON_INCLINATION_DEG = 5.1454

_MOON_PERIHELION_BASE_DEG = 318.0634
_MOON_PERIHELION_RATE = 0.1643573223

_MOON_SEMI_MAJOR_AXIS_ER = 60.2666

_MOON_ECCENTRICITY = 0.054900

_MOON_MEAN_ANOMALY_BASE_DEG = 115.3654
_MOON_MEAN_ANOMALY_RATE = 13.0649929509

_EARTH_EQUATORIAL_RADIUS_KM = 6378.14

_EVECTION_COEFF_DEG = -1.274
_VARIATION_COEFF_DEG = 0.658
_YEARLY_EQUATION_COEFF_DEG = -0.186
_LON_PERT4_COEFF_DEG = -0.059
_LON_PERT5_COEFF_DEG = -0.057
_LON_PERT6_COEFF_DEG = 0.053
_LON_PERT7_COEFF_DEG = 0.046
_LON_PERT8_COEFF_DEG = 0.041
_LON_PERT9_COEFF_DEG = 0.035
_LON_PERT10_COEFF_DEG = -0.031
_LON_PERT11_COEFF_DEG = -0.015
_LON_PERT12_COEFF_DEG = 0.011

_LAT_PERT1_COEFF_DEG = -0.173
_LAT_PERT2_COEFF_DEG = -0.055
_LAT_PERT3_COEFF_DEG = -0.046
_LAT_PERT4_COEFF_DEG = 0.033
_LAT_PERT5_COEFF_DEG = 0.017

_DIST_PERT1_COEFF_ER = -0.58
_DIST_PERT2_COEFF_ER = -0.46

_PHASE_NEW_MOON_UPPER_DEG = 22.5
_PHASE_WAXING_CRESCENT_UPPER_DEG = 67.5
_PHASE_FIRST_QUARTER_UPPER_DEG = 112.5
_PHASE_WAXING_GIBBOUS_UPPER_DEG = 157.5
_PHASE_FULL_MOON_UPPER_DEG = 202.5
_PHASE_WANING_GIBBOUS_UPPER_DEG = 247.5
_PHASE_LAST_QUARTER_UPPER_DEG = 292.5
_PHASE_WANING_CRESCENT_UPPER_DEG = 337.5

_DEG_PER_RAD = 180.0 / pi

NEW_MOON = 0
WAXING_CRESCENT = 1
FIRST_QUARTER = 2
WAXING_GIBBOUS = 3
FULL_MOON = 4
WANING_GIBBOUS = 5
LAST_QUARTER = 6
WANING_CRESCENT = 7

_PHASE_NAMES = (
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
)


def phase_name_to_string(name):
    if not 0 <= name <= 7:
        raise ValueError("phase_name_to_string: name must be 0..7")
    return _PHASE_NAMES[name]


class Position:
    __slots__ = ("longitude_deg", "latitude_deg", "distance_km")

    def __init__(self, longitude_deg, latitude_deg, distance_km):
        self.longitude_deg = longitude_deg
        self.latitude_deg = latitude_deg
        self.distance_km = distance_km


class Phase:
    __slots__ = ("name", "illuminated_fraction", "phase_angle_deg", "elongation_deg")

    def __init__(self, name, illuminated_fraction, phase_angle_deg, elongation_deg):
        self.name = name
        self.illuminated_fraction = illuminated_fraction
        self.phase_angle_deg = phase_angle_deg
        self.elongation_deg = elongation_deg


class Ephemeris:
    __slots__ = ("position", "phase")

    def __init__(self, position, phase):
        self.position = position
        self.phase = phase


def _normalize_deg(x):
    r = fmod(x, 360.0)
    if r < 0.0:
        r += 360.0
    return r


def _sin_deg(x):
    return sin(x / _DEG_PER_RAD)


def _cos_deg(x):
    return cos(x / _DEG_PER_RAD)


def _classify_phase(elong):
    if elong < _PHASE_NEW_MOON_UPPER_DEG or elong >= _PHASE_WANING_CRESCENT_UPPER_DEG:
        return NEW_MOON
    elif elong < _PHASE_WAXING_CRESCENT_UPPER_DEG:
        return WAXING_CRESCENT
    elif elong < _PHASE_FIRST_QUARTER_UPPER_DEG:
        return FIRST_QUARTER
    elif elong < _PHASE_WAXING_GIBBOUS_UPPER_DEG:
        return WAXING_GIBBOUS
    elif elong < _PHASE_FULL_MOON_UPPER_DEG:
        return FULL_MOON
    elif elong < _PHASE_WANING_GIBBOUS_UPPER_DEG:
        return WANING_GIBBOUS
    elif elong < _PHASE_LAST_QUARTER_UPPER_DEG:
        return LAST_QUARTER
    else:
        return WANING_CRESCENT


def compute(unix_time):
    if isnan(unix_time) or isinf(unix_time):
        raise ValueError("compute: unix_time must be finite")

    d = unix_time / 86400.0 - _SCHLYTER_EPOCH_OFFSET_DAYS

    w_s = _SUN_PERIHELION_BASE_DEG + _SUN_PERIHELION_RATE * d
    e_s = _SUN_ECCENTRICITY_BASE + _SUN_ECCENTRICITY_RATE * d
    m_s = _SUN_MEAN_ANOMALY_BASE_DEG + _SUN_MEAN_ANOMALY_RATE * d
    l_s = _normalize_deg(w_s + m_s)

    e_sun = _normalize_deg(
        m_s + _DEG_PER_RAD * e_s * _sin_deg(m_s) * (1.0 + e_s * _cos_deg(m_s))
    )
    x_sun = _cos_deg(e_sun) - e_s
    y_sun = sqrt(1.0 - e_s * e_s) * _sin_deg(e_sun)
    lambda_s = _normalize_deg(atan2(y_sun, x_sun) * _DEG_PER_RAD + w_s)

    n_moon = _MOON_NODE_BASE_DEG + _MOON_NODE_RATE * d
    w_moon = _MOON_PERIHELION_BASE_DEG + _MOON_PERIHELION_RATE * d
    m_moon = _MOON_MEAN_ANOMALY_BASE_DEG + _MOON_MEAN_ANOMALY_RATE * d
    l_moon = _normalize_deg(n_moon + w_moon + m_moon)

    e_moon = _normalize_deg(
        m_moon
        + _DEG_PER_RAD
        * _MOON_ECCENTRICITY
        * _sin_deg(m_moon)
        * (1.0 + _MOON_ECCENTRICITY * _cos_deg(m_moon))
    )
    x_v = _cos_deg(e_moon) - _MOON_ECCENTRICITY
    y_v = sqrt(1.0 - _MOON_ECCENTRICITY * _MOON_ECCENTRICITY) * _sin_deg(e_moon)
    r_moon = _MOON_SEMI_MAJOR_AXIS_ER * sqrt(x_v * x_v + y_v * y_v)
    v_moon = atan2(y_v, x_v) * _DEG_PER_RAD
    l_orb = _normalize_deg(v_moon + w_moon)

    x_ecl = r_moon * (
        _cos_deg(n_moon) * _cos_deg(l_orb)
        - _sin_deg(n_moon) * _sin_deg(l_orb) * _cos_deg(_MOON_INCLINATION_DEG)
    )
    y_ecl = r_moon * (
        _sin_deg(n_moon) * _cos_deg(l_orb)
        + _cos_deg(n_moon) * _sin_deg(l_orb) * _cos_deg(_MOON_INCLINATION_DEG)
    )
    z_ecl = r_moon * _sin_deg(l_orb) * _sin_deg(_MOON_INCLINATION_DEG)
    rxy = sqrt(x_ecl * x_ecl + y_ecl * y_ecl)
    lambda0 = _normalize_deg(atan2(y_ecl, x_ecl) * _DEG_PER_RAD)
    beta0 = atan2(z_ecl, rxy) * _DEG_PER_RAD
    r0 = sqrt(rxy * rxy + z_ecl * z_ecl)

    d_m = _normalize_deg(l_moon - l_s)
    f = _normalize_deg(l_moon - n_moon)

    delta_lambda = (
        _EVECTION_COEFF_DEG * _sin_deg(m_moon - 2.0 * d_m)
        + _VARIATION_COEFF_DEG * _sin_deg(2.0 * d_m)
        + _YEARLY_EQUATION_COEFF_DEG * _sin_deg(m_s)
        + _LON_PERT4_COEFF_DEG * _sin_deg(2.0 * m_moon - 2.0 * d_m)
        + _LON_PERT5_COEFF_DEG * _sin_deg(m_moon - 2.0 * d_m + m_s)
        + _LON_PERT6_COEFF_DEG * _sin_deg(m_moon + 2.0 * d_m)
        + _LON_PERT7_COEFF_DEG * _sin_deg(2.0 * d_m - m_s)
        + _LON_PERT8_COEFF_DEG * _sin_deg(m_moon - m_s)
        + _LON_PERT9_COEFF_DEG * _sin_deg(d_m)
        + _LON_PERT10_COEFF_DEG * _sin_deg(m_moon + m_s)
        + _LON_PERT11_COEFF_DEG * _sin_deg(2.0 * f - 2.0 * d_m)
        + _LON_PERT12_COEFF_DEG * _sin_deg(m_moon - 4.0 * d_m)
    )

    delta_beta = (
        _LAT_PERT1_COEFF_DEG * _sin_deg(f - 2.0 * d_m)
        + _LAT_PERT2_COEFF_DEG * _sin_deg(m_moon - f - 2.0 * d_m)
        + _LAT_PERT3_COEFF_DEG * _sin_deg(m_moon + f - 2.0 * d_m)
        + _LAT_PERT4_COEFF_DEG * _sin_deg(f + 2.0 * d_m)
        + _LAT_PERT5_COEFF_DEG * _sin_deg(2.0 * m_moon + f)
    )

    delta_r = _DIST_PERT1_COEFF_ER * _cos_deg(
        m_moon - 2.0 * d_m
    ) + _DIST_PERT2_COEFF_ER * _cos_deg(2.0 * d_m)

    lambda_ = _normalize_deg(lambda0 + delta_lambda)
    beta = beta0 + delta_beta
    dist_km = (r0 + delta_r) * _EARTH_EQUATORIAL_RADIUS_KM

    d_elong = _normalize_deg(lambda_ - lambda_s)
    psi = d_elong if d_elong <= 180.0 else 360.0 - d_elong
    alpha = 180.0 - psi
    k = (1.0 + _cos_deg(alpha)) / 2.0

    return Ephemeris(
        Position(lambda_, beta, dist_km),
        Phase(_classify_phase(d_elong), k, alpha, d_elong),
    )
