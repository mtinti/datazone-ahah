# Response to implementation review round 2 (29 October 2026)

No findings to answer. The one soft point, that `loader/sqlserver_probe.sh` printed the join
results instead of asserting them, is addressed: the probe now compares the eight-row cohort
(a matched code, NULL, empty, whitespace only, a 2022 code, a malformed code, a padded
lower-case code, a repeated code) against an expected list and exits 1 on any difference.
Re-run on the same container image: five checks pass, 40 rendered cells equal, join asserted.

Still untested, as the review says: Windows integrated authentication, server-visible Windows
paths and the loader's pyodbc branch. These are exercised on first use at the site, as with
postcode-simd.
