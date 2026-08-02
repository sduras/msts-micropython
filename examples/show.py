#!/usr/bin/env micropython

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import msts

# NOTE: on some MicroPython ports, time.time() is seconds since
# 2000-01-01 rather than the Unix epoch (1970-01-01). Check your
# port's `time` module docs. msts.compute always expects a Unix
# timestamp.

if len(sys.argv) == 1:
    t = time.time()
elif len(sys.argv) == 2:
    try:
        t = float(sys.argv[1])
    except ValueError:
        sys.stderr.write("show: not a number: %s\n" % sys.argv[1])
        sys.exit(1)
else:
    sys.stderr.write("usage: show.py [unix_timestamp]\n")
    sys.exit(1)

e = msts.compute(t)
pos = e.position
ph = e.phase

print("Unix time   : %.0f" % t)
print("Longitude   : %9.4f deg" % pos.longitude_deg)
print("Latitude    : %9.4f deg" % pos.latitude_deg)
print("Distance    : %.1f km" % pos.distance_km)
print("Phase       : %s" % msts.phase_name_to_string(ph.name))
print("Illuminated : %.1f %%" % (ph.illuminated_fraction * 100.0))
print("Phase angle : %9.4f deg" % ph.phase_angle_deg)
print("Elongation  : %9.4f deg" % ph.elongation_deg)
