# Handover from the SIMD chat (29 October 2026): AHAH work done there

## Files written or changed in `~/git_projects/AHAH/`

- `docs/AHAH_Plan.md`: the ingestion plan. It follows the postcode-simd build and links to the
  matching files in `github.com/mtinti/postcode-simd`.
  - AHAH travels with data zones. The postcode route is only optional.
  - The open question is version 4 (2011 zones) or 5.1 (2022 zones). The HEAL-Scot data request
    asks for v4, while DataLoch's specification offers v5.1.
  - The plan records the licence findings and the corrected code repository.
- Nothing else in the folder was changed, apart from this file.

## Licence and terms

- GeoDS shows the dataset as "Open", under the OGL v3.0. Its About page says Open data are for
  "any purpose" after registration, "with attribution".
- No other terms were shown at registration or download; Michele confirmed this. So the files
  can be archived on Zenodo with attribution:
  - the paper: Daras et al. 2019, *Scientific Data* 6, 107, doi:10.1038/s41597-019-0114-6;
  - the statement that the data were provided by the Geographic Data Service, a Smart Data
    Research UK investment, ES/Z504464/1.
- The GeoDS user guide (`https://service.geods.ac.uk/user_guide.pdf`) didn't respond and has not
  been read.

## Code repository

- The build code is in https://github.com/GeographicDataService/ahah, tags v3, v4 and v5.
- `AHAH_V5`, the repository named on the GeoDS page, returns 404.

## Why indicator percentiles run 0 to 100 and domain percentiles 1 to 100

- **The two formulas:**
  - indicators: `(rnk / rnk.max() * 100).astype(int)`, which gives 101 values;
  - domains and index: `pd.qcut(rnk, 100, labels=False) + 1`, which gives 100 values.
- **Where they are:** at v3 and v4, `ahah/create_index.py` (v4 commit `722fe5f`, lines 62–97).
  At v5, `AHAH_Build_Indicator.ipynb` (commit `6ebb0ae`), the "Create Index" cell (`In [23]`),
  lines 66, 77 and 88.
- **Checked:** recomputing from the published ranks reproduces every percentile column in v3, v4
  and v5.1, with 0 mismatches. The exact formula for the domain percentiles is
  `max(1, ceil((r−1)·100/(n−1)))`.
- **Against their own documentation:** the v5 methodology report, section 7 (page 7), says
  indicator percentiles are "(1-100)". So the files contradict it.
- **Reading:** one scale was intended, and the indicator formula is a shortcut carried over since
  v3.

## Corrections to `docs/PERCENTILES.md`

- The notebook exists only at v5; v3 and v4 used `create_index.py`.
- The code divides by `max(rank)`, not n. Dividing by n works only in v5.1; it gives 20,180 wrong
  v3 cells and 2,010 wrong v4 cells.
- The 48 domain mismatches with `ceil(r·100/n)` come from `qcut`'s bin edges using n−1, not from
  ties.

## Other facts from the code and files

- Rank 1 is the best area in every column, so a low percentile means good. That is the opposite
  of SIMD, where band 1 is the most deprived.
- v4 ranks the five health indicators with `method="dense"`; the other versions use `min`.
- Ranks can't be recomputed from the published values, which are rounded. Keep the published
  ranks unchanged.
- v1 and v2 publish deciles, not percentiles. In v2, 11 indicator decile columns have `-1` in 2
  rows; this is not investigated.
- The v3 file has **41,729** rows, all with distinct codes. `data/sources/geods_previous/SOURCES.md`
  says 41,728, which needs correcting.
- `data/sources/geods/SOURCES.md` still says the registration terms are "not recorded". It can now
  say that no further terms were shown.

## Can the versions go in one long table?

They can be stored together, but they can't be compared with each other.

| | v1 | v2 | v3 | v4 | v5.1 |
| --- | --- | --- | --- | --- | --- |
| Data zones | 2011 | 2011 | 2011 | 2011 | **2022** |
| Domains | 3, no green | 4 | 4 | 4 | 4 |
| Bands | deciles | ranks and deciles | ranks and percentiles | ranks and percentiles | ranks and percentiles |
| Names | short | short | short | prefixed `ah4` | long |

- Scottish median GP values per version: 1.32, 1.34, 3.93, 2.64 and 2.36. The units or methods
  change between versions.
- The number of areas ranked across Great Britain changes: 41,728 or 41,729, then 42,648, then
  43,064.
- v3 and v4 cover the same zones, yet their overall index ranks correlate at only 0.76.

The proposal, not yet in the plan, is one table keyed by `(ahah_version, data_zone_code)` with
`data_zone_vintage`:

- common names only where the concept is the same, and NULL where a version lacks a column;
- values as published;
- a README warning to use one version per study and never compare versions over time.

## Disclosure benchmark from SIMD 2020v2

The seven domain quintiles alone single out 1,923 of 6,976 data zones (27.6%). Run the same count
on the AHAH bands before anything is released.

## Draft GitHub issue for GeographicDataService/ahah (not posted; Michele posts it)

**Title:** Indicator percentiles run 0–100, domain and index percentiles 1–100

Hello, and thank you for AHAH. I work at HIC (Health Informatics Centre, University of Dundee),
and I'm loading AHAH into our trusted research environment so research projects there can use it.
While checking the files, I noticed the percentiles use two scales from v3 onwards:

- The 15 indicator percentiles (`GP_pct`, `NO2_pct`, …) take 101 values, 0 to 100.
- The 4 domain percentiles and `ahah_pct` take 100 values, 1 to 100.

This comes from two formulas in the build code:

- Indicators: `(rnk / rnk.max() * 100).astype(int)`. Rank 1 becomes 0, and only the highest rank
  reaches 100.
- Domains and index: `pd.qcut(rnk, 100, labels=False) + 1`.

The same two formulas appear in `ahah/create_index.py`, which built
[v3](https://github.com/GeographicDataService/ahah/tree/v3) and
[v4](https://github.com/GeographicDataService/ahah/blob/722fe5f/ahah/create_index.py#L62-L97).
They also appear in
[`AHAH_Build_Indicator.ipynb`](https://github.com/GeographicDataService/ahah/blob/v5/AHAH_Build_Indicator.ipynb),
which replaced it for v5: the "Create Index" cell (`In [23]`), lines 66, 77 and 88. Applying
these formulas to the published ranks reproduces every published percentile in v3, v4 and v5.1.

The v5 technical methodology (section 7, Output Variables) describes `[indicator]_pct` as
"National percentile for each indicator (1-100)". The published indicator percentiles include 0,
so the files and the methodology disagree. Could you confirm which is intended? If 1 to 100 is
meant, the indicator percentiles could use the same `qcut` formula as the domains. Otherwise, a
note in the methodology and dictionary would help users.

Also, the GeoDS dataset page links the code as `AHAH_V5`, which returns 404. The code seems to be
here.

## Scratch files

Everything is under
`/private/tmp/claude-502/-Users-mtinti-git-projects-SIMD/e0ba9a37-3a8c-4c8d-bb2c-4fe5e744399d/scratchpad/`:

- the percentile checks, in `ahah_pct/`: `probe_pct.py`, run as
  `python3 -I probe_pct.py v5 v4 v3 v12`, plus its outputs;
- the upstream code, in `ahah_pct/repos/src/`;
- the `pypdf` environment used to read the PDF, in `pdfenv/`.

The scratchpad belongs to the SIMD session and may be cleared. Copy anything worth keeping into
the AHAH folder.
