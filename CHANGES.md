## v0.1.0 (2026-08-02)

- Initial release: pure-Python, zero-dependency port of msts 0.1.1
  (https://codeberg.org/duras/msts) for MicroPython.
- `compute`: geocentric ecliptic position and phase from a Unix timestamp.
- `phase_name_to_string`: English name for all eight phase constants.
- Ported line-for-line from the OCaml source; same constants, same
  formulas, same accuracy bounds.
