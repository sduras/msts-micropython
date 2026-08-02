# msts-micropython

Geocentric lunar ephemerides from a Unix timestamp: the Moon's ecliptic
position, distance, and phase.

This is a Python port of [msts][origin], the OCaml library, rewritten
for MicroPython on resource-constrained microcontrollers. It implements
the same algorithm with the same accuracy bounds. Use this version
on-device, and the OCaml original wherever a full OCaml toolchain is
available.

[origin]: https://codeberg.org/duras/msts

The implementation follows [Paul Schlyter](http://stjarnhimlen.se/)'s
algorithm: Keplerian orbital elements propagated from a fixed epoch with
empirical perturbation corrections.

The library depends only on the standard `math` module. It performs no
I/O, reads no files, keeps no global state, and is fully deterministic.
`compute` is total for finite inputs; invalid arguments raise
`ValueError` naming the offending parameter.

Results are validated against JPL Horizons (DE441) over the interval
1900-01-01 through 2100-12-31.

Guaranteed error bounds:

- 2° in ecliptic longitude
- 0.5° in ecliptic latitude
- 1% in distance
- 0.02 in illuminated fraction

Typical errors are substantially smaller.

## Requirements

- MicroPython, or
- CPython 3

Only the standard `math` module is required.

## Installation

### MicroPython

Either:

- Install `micropython-msts` from **Tools → Manage packages…** in
  [Thonny](https://thonny.org/), or
- Copy `msts.py` onto the target device, for example:

```sh
mpremote cp msts.py :
```

Or simply place it alongside your own modules.

### CPython

Install from PyPI:

```sh
pip install micropython-msts
```

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

`compute` takes a Unix timestamp and returns a small result structure. It
performs no I/O and allocates only three small objects, making it
inexpensive enough to call on every wake cycle of a battery-powered
device.

Some applications:

- **Clock or watch firmware** — moon-phase complications for
  MicroPython-based clocks and smartwatches.
- **E-ink or OLED displays** — ESP32 or RP2040 boards that wake on a
  timer, compute the current phase, and update a display without network
  access.
- **Garden automation** — irrigation or planting reminders keyed to the
  lunar phase alongside existing sensor data.
- **Outdoor lighting** — dim or disable solar- or LoRa-powered lighting
  near the full moon when ambient light is already higher.
- **Education** — classroom demonstrations of basic orbital mechanics by
  varying the timestamp and observing the resulting position and phase.
- **Astrophotography helpers** — approximate moon phase and brightness
  for scheduling. Not suitable where precise rise/set times or
  arcsecond-level accuracy are required.

## Differences from the OCaml original

- `phase_name` is represented by small integer constants
  (`msts.NEW_MOON`, `msts.WAXING_CRESCENT`, ...) instead of an OCaml
  variant type or Python `enum`, since MicroPython has no standard
  `enum` module.
- `Invalid_argument` becomes `ValueError`.
- Field names, function names, formulas, constants, and documented
  accuracy bounds otherwise match the OCaml implementation one-for-one.

## License

ISC. See [LICENSE](LICENSE).
