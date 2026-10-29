# Response to round 3 (29 October 2026)

Both findings were re-probed before the plan changed.

1. **`ur` nullable boolean (P1): accepted, resolved by type choice.** Read the copied writers:
   `text_output.py` renders `bool` with `bool(v)` and no null check, so `None` becomes `0`;
   `output.py` casts the series with `astype(bool)`. Rather than add a nullable-boolean path,
   `ur` becomes a nullable `tinyint` with a 0/1 check, which goes through the nullable-integer
   path postcode-simd already has and tests. The SQL plan's type table and tests now say so.
   What this does not cover: a boolean type is still unsupported for nulls in the copied code;
   nothing in the AHAH schema uses it, and the build should fail if a mapping declares one.

2. **v1 domain scale (P2): accepted.** Probe on the pinned v1 file, n = 41,729: for every value
   of `h`, `e` and `r`, `n·(1−exp(−x/23))/(1−exp(−100/23))` is within 5.9e-6 of an integer.
   Minimum 0.000544, maximum 100 in each column. So v1 domains are the exponential scale. The
   SQL plan now maps v1 `h`, `e`, `r` into `domain_h_exp`, `domain_e_exp`, `domain_r_exp`,
   leaves `domain_g_exp` NULL for v1 and the probit columns NULL for v1 and v2, updates the
   presence matrix and the fidelity test, and records that the v1 environment domain includes
   green space. Published values unchanged; inverted ranks are not derived or published.

3. **Editorial, line 63:** the fixed count of three is replaced by the list of column groups.

Not changed: the v1 index `ahah` stays in the `ahah` column. It is the average of the
exponential domain values in v1 and v2 and of the probit domain scores in v3 onward, so the
same caveat applies and the dictionary should say it per edition. That is a dictionary task,
not a schema change.

My findings on this round are closed.
