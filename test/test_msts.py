import sys
import os
from math import cos, radians

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import msts

failures = 0


def check(name, condition):
    global failures
    if not condition:
        sys.stderr.write("FAIL: %s\n" % name)
        failures += 1


def check_raises_value_error(name, f):
    try:
        f()
        check(name, False)
    except ValueError:
        check(name, True)


t_1900 = -2208988800.0
t_1950 = -631152000.0
t_j2000 = 946728000.0
t_2100 = 4133894400.0

t_new_moon = 947182440.0
t_full_moon = 948429600.0
t_perigee = 948326400.0
t_apogee = 949363200.0


def check_ranges(t, e):
    ts = "t=%.0f" % t
    pos = e.position
    ph = e.phase
    check(ts + " longitude_deg in [0, 360)", 0.0 <= pos.longitude_deg < 360.0)
    check(ts + " latitude_deg in [-90, +90]", -90.0 <= pos.latitude_deg <= 90.0)
    check(ts + " distance_km > 0", pos.distance_km > 0.0)
    check(ts + " illuminated_fraction in [0, 1]", 0.0 <= ph.illuminated_fraction <= 1.0)
    check(ts + " phase_angle_deg in [0, 180]", 0.0 <= ph.phase_angle_deg <= 180.0)
    check(ts + " elongation_deg in [0, 360)", 0.0 <= ph.elongation_deg < 360.0)


def phase_name_matches_elongation(name, elong):
    if name == msts.NEW_MOON:
        return elong < 22.5 or elong >= 337.5
    elif name == msts.WAXING_CRESCENT:
        return 22.5 <= elong < 67.5
    elif name == msts.FIRST_QUARTER:
        return 67.5 <= elong < 112.5
    elif name == msts.WAXING_GIBBOUS:
        return 112.5 <= elong < 157.5
    elif name == msts.FULL_MOON:
        return 157.5 <= elong < 202.5
    elif name == msts.WANING_GIBBOUS:
        return 202.5 <= elong < 247.5
    elif name == msts.LAST_QUARTER:
        return 247.5 <= elong < 292.5
    else:
        return 292.5 <= elong < 337.5


def k_consistent_with_phase_angle(k, alpha):
    expected = (1.0 + cos(radians(alpha))) / 2.0
    return abs(k - expected) < 1e-4


def phase_angle_consistent_with_elongation(alpha, elong):
    psi = elong if elong <= 180.0 else 360.0 - elong
    return abs(alpha - (180.0 - psi)) < 1e-10


def check_consistency(t, e):
    ts = "t=%.0f" % t
    ph = e.phase
    check(ts + " phase_name consistent with elongation_deg",
          phase_name_matches_elongation(ph.name, ph.elongation_deg))
    check(ts + " illuminated_fraction consistent with phase_angle_deg",
          k_consistent_with_phase_angle(ph.illuminated_fraction, ph.phase_angle_deg))
    check(ts + " phase_angle_deg consistent with elongation_deg",
          phase_angle_consistent_with_elongation(ph.phase_angle_deg, ph.elongation_deg))


def main():
    check("phase_name_to_string New Moon",
          msts.phase_name_to_string(msts.NEW_MOON) == "New Moon")
    check("phase_name_to_string Waxing Crescent",
          msts.phase_name_to_string(msts.WAXING_CRESCENT) == "Waxing Crescent")
    check("phase_name_to_string First Quarter",
          msts.phase_name_to_string(msts.FIRST_QUARTER) == "First Quarter")
    check("phase_name_to_string Waxing Gibbous",
          msts.phase_name_to_string(msts.WAXING_GIBBOUS) == "Waxing Gibbous")
    check("phase_name_to_string Full Moon",
          msts.phase_name_to_string(msts.FULL_MOON) == "Full Moon")
    check("phase_name_to_string Waning Gibbous",
          msts.phase_name_to_string(msts.WANING_GIBBOUS) == "Waning Gibbous")
    check("phase_name_to_string Last Quarter",
          msts.phase_name_to_string(msts.LAST_QUARTER) == "Last Quarter")
    check("phase_name_to_string Waning Crescent",
          msts.phase_name_to_string(msts.WANING_CRESCENT) == "Waning Crescent")

    check_raises_value_error(
        "phase_name_to_string out of range",
        lambda: msts.phase_name_to_string(8))

    for t in (t_1900, t_1950, t_j2000, t_2100,
              t_new_moon, t_full_moon, t_perigee, t_apogee):
        e = msts.compute(t)
        check_ranges(t, e)
        check_consistency(t, e)

    check("t_new_moon phase_name is New Moon",
          msts.compute(t_new_moon).phase.name == msts.NEW_MOON)
    check("t_full_moon phase_name is Full Moon",
          msts.compute(t_full_moon).phase.name == msts.FULL_MOON)

    check_raises_value_error("compute nan", lambda: msts.compute(float("nan")))
    check_raises_value_error("compute inf", lambda: msts.compute(float("inf")))
    check_raises_value_error("compute -inf", lambda: msts.compute(float("-inf")))

    if failures:
        sys.stderr.write("%d failure(s)\n" % failures)
        sys.exit(1)
    print("all tests passed")


main()
