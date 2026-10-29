# Why indicator percentiles run 0 to 100 and domain percentiles 1 to 100

Observed in every file from version 3 onward: the indicator percentiles (14 indicators in v3 and
v4, 15 in v5.1) take 101 distinct values, 0 to 100; the four domain percentiles and the index percentile take 100 values, 1 to 100.

The cause is two formulas in the published build code, https://github.com/GeographicDataService/ahah:
`ahah/create_index.py` for v3 and v4 (v4 commit `722fe5f`, lines 62 to 97), and the "Create
Index" cell of `AHAH_Build_Indicator.ipynb` for v5 (commit `6ebb0ae`).

```python
# indicators: truncation toward zero, divided by the largest rank
idx[f"{col}_pct"] = (idx[f"{col}_rnk"] / idx[f"{col}_rnk"].max() * 100).astype(int)
# domains and index: a hundred equal bins, labelled 1 to 100
idx[f"domain_{d}_pct"] = pd.qcut(idx[f"domain_{d}_rnk"], 100, labels=False) + 1
idx["ahah_pct"] = pd.qcut(idx["ahah_rnk"], 100, labels=False) + 1
```

Checked on 29 October 2026 against the published ranks of v3, v4 and v5.1, with zero mismatches:

- indicator percentile = floor(rank × 100 / max rank). Rank 1 to about 430 become 0, and only
  the largest rank reaches 100. The divisor is the largest rank, not the number of areas: in v4
  the five health indicators are ranked with `method="dense"`, so the largest GP rank is 42,644
  in a file of 42,648 areas, and dividing by the number of areas gives 199 wrong cells.
- domain and index percentile = max(1, ceil((rank − 1) × 100 / (n − 1))), which is what
  `qcut` on the ranks produces.

The v5 methodology report, section 7, says indicator percentiles are "(1-100)". The files
contradict it. The likely reading is that one scale was intended and the indicator line is a
shortcut carried since v3. An issue was logged with the authors on 29 October 2026 (text in `ISSUE_DRAFT_percentiles.md`).
Until they answer, the build takes the files as they are.

Consequences for the build:

- Store the published values unchanged. The checks accept 0 to 100 for indicator percentiles
  and 1 to 100 for domain and index percentiles, and fail outside those.
- The two kinds of percentile are not the same scale. The data dictionary says so on each column.
- Rank 1 is the best area in every column, so a low percentile is good. SIMD is the opposite:
  band 1 is most deprived. The README says this once, early.
- Ranks cannot be recomputed from the published values, which are rounded. The published ranks
  are the only exact ordering; anyone who wants one consistent scale derives it from them, as a
  named derived column.
