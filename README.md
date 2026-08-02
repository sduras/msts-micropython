# msts-micropython

Geocentric lunar ephemerides from a Unix timestamp: the Moon's ecliptic
position, distance, and phase.

This is a pure-Python port of [msts][origin], the OCaml library, rewritten
for MicroPython on resource-constrained microcontrollers. Same algorithm
and accuracy bounds; use this one on-device and the OCaml original 
wherever a full OCaml toolchain is available.

[origin]: https://codeberg.org/duras/msts

The algorithm is Paul Schlyter's: Keplerian orbital elements propagated
from a fixed epoch with empirical perturbation corrections. The library
depends only on the `math` module from the standard library, reads no
files, and keeps no state. `compute` is deterministic and total for
finite inputs; invalid inputs raise `ValueError` naming the offending
argument.

Results are validated against JPL Horizons (DE441) over the supported
interval 1900-01-01 through 2100-12-31. Guaranteed bounds: 2 degrees in
ecliptic longitude, 0.5 degrees in ecliptic latitude, 1% in distance,
0.02 in illuminated fraction. Typical errors are much smaller.

## Requirements

MicroPython or CPython 3, with the standard `math` module. Nothing else.

## Installation

Copy `msts.py` to the device (e.g. with `mpremote cp msts.py :`) or drop
it into your project alongside your own modules.

## Example

```python
import msts

# J2000.0 = 2000-01-01T12:00:00Z
e = msts.compute(946728000.0)
print("%s  %.1f%%  %.0f km" % (
    msts.phase_name_to_string(e.phase.name),
    e.phase.illuminated_fraction * 100.0,
    e.position.distance_km,
))
```

## Example uses

`compute` is a single float-in, struct-out call with no I/O and no
allocation beyond three small objects, so it's cheap enough to call on
every wake cycle of a battery-powered device. Some fits:

- **Clock or watch firmware**: a moon-phase complication on a
  MicroPython-based smartwatch or wall clock face.
- **E-ink or OLED moon-phase display**: an ESP32 or Pi Pico that wakes
  on a timer, calls `compute`, and draws the phase name and illuminated
  fraction — no network or RTC chip beyond whatever gives you Unix time.
- **Garden helper**: irrigation or planting reminders keyed to lunar
  phase alongside your existing sensor readings.
- **Outdoor lighting automation**: dim or skip a solar/LoRa night-light
  around the full moon when ambient light is already higher.
- **Education and demo boards**: a classroom orbital-mechanics demo
  where students change the timestamp and watch position and phase
  update on a small display.
- **Astro-adjacent scheduling**: rough moonrise/moon-brightness context
  for a time-lapse camera controller (not a substitute for a proper
  ephemeris if you need arcsecond precision or actual rise/set times).

## Differences from the OCaml original

- `phase_name` is a set of small integer constants
  (`msts.NEW_MOON`, `msts.WAXING_CRESCENT`, ...) rather than a variant
  type, since MicroPython has no `enum` module.
- `Invalid_argument` becomes `ValueError`.
- Everything else — field names, function names, formulas, constants,
  accuracy bounds — matches the original one-to-one.

## License

ISC. See [LICENSE](LICENSE).
