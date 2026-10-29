# Response to the plans review, round 2, 29 October 2026

All three findings were re-checked against the files and hold.

| Finding | Verified how | Resolution in `AHAH_SQL_Plan.md` |
| --- | --- | --- |
| 1. v2 domain `_exp` columns must be kept | The v2 file has no `r`, `h`, `g`, `e` columns; `S01006506` has the four `_exp` values quoted | Nothing is dropped. The four values go to `domain_<x>_exp`, v2 only, documented as the exponentially transformed domain ranks (the v2 build code), not the probit scores of v3 onward. The presence matrix marks v2 domain scores absent and the `_exp` row present. A fidelity check compares every v2 zone's four values with the file |
| 2. Blanket `-1` rejection would reject v4 | `S01008132`, `ah4e = -1.0000`, the only exact `-1` cell in v4 | The code check is narrowed to the v2 decile and indicator columns. Domain scores accept any real value. The v4 row is a named accepted fixture |
| 3. v1 green space is an area, not a share | Scottish `gpas` runs 0 to 277.5 | Described as an area measure within a 900-metre buffer, unit unconfirmed, no range rule |

Also done: the order-of-work sentence now says the text output, Parquet writer and SQL
generator are copied and extended with the two new types.

Still open, and labelled unconfirmed in the plan: the meaning of v2's `ur` column and of its
`-1` code, and the v1 green space area unit.
