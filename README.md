# datazone-ahah

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23783415.svg)](https://doi.org/10.5281/zenodo.23783415)
[![ci](https://github.com/mtinti/datazone-ahah/actions/workflows/ci.yml/badge.svg)](https://github.com/mtinti/datazone-ahah/actions/workflows/ci.yml)

AHAH for SQL Server, by data zone. Software DOI <https://doi.org/10.5281/zenodo.23783415> (concept, every release);
pinned sources <https://doi.org/10.5281/zenodo.23783247>.

The Access to Healthy Assets and Hazards index (AHAH, Geographic Data Science Lab, University of
Liverpool, hosted by the Geographic Data Service) in one table for SQL Server: every edition, one
row per Scottish data zone per edition, every value exactly as published. Built the way
[postcode-simd](https://github.com/mtinti/postcode-simd) is built: pinned sources, blocking
checks, a CSV with a row digest, generated import and check scripts, and a loader.

## What is in the table

`ahah_datazone`, 35,296 rows by 90 columns, keyed by `ahah_version` and `datazone_code`.

| Edition | Year | Scottish data zones | Rows |
| --- | --- | --- | --- |
| 1 | 2016 | 2011 | 6,976 |
| 2 | 2017 | 2011 | 6,976 |
| 3 | 2022 | 2011 | 6,976 |
| 4 | 2024 | 2011 | 6,976 |
| 5.1 | 2026 | 2022 | 7,392 |

Column names are those of the version 5.1 file. Earlier editions are mapped onto them, every
file column exactly once, and a column an edition does not publish is NULL for it. The data
dictionary, `docs/DATA_DICTIONARY.md`, lists every column with its file name in each edition.

Three warnings:

- **Rank 1 is the healthiest** area, in every rank, percentile and decile. This is the opposite
  of SIMD, where 1 is the most deprived.
- **Editions are not comparable.** Methods, units, the ranked population and, for 5.1, the data
  zones all change. Use one edition per study. Never compare editions over time.
- **Ranks are over Great Britain**, not Scotland. Indicator percentiles run 0 to 100, domain and
  index percentiles 1 to 100 (`docs/PERCENTILES.md`).

**Pinned sources archived on Zenodo: <https://doi.org/10.5281/zenodo.23783247>.** Every file the
build reads, byte for byte with its SHA256, under the Open Government Licence v3.0 with the
attribution below. A fresh checkout restores `data/sources/` from that record.

## Build

```
pip install -r requirements.txt
python -m ahah_ingest.pipeline       # results/ahah_datazone.csv.gz, .parquet, manifest.json, BUILD_REPORT.md
python -m ahah_ingest.sql_check      # docs/sql/import_csv.sql, check_loaded_digest.sql
python -m ahah_ingest.dictionary     # docs/DATA_DICTIONARY.md
python -m pytest
```

The build reads the pinned files under `data/sources/` (hashes in each folder's `SOURCES.md` and
in `ahah_ingest/sources.yaml`), stops on any changed byte, any check failure, or any value that
does not fit `decimal(38,20)`. It never goes through a float.

## Load into SQL Server

Carry `results/ahah_datazone.csv.gz`, the two scripts in `docs/sql/` and
`loader/load_ahah_to_sqlserver.py` to the server; fill in the EDIT block; run the loader. It
verifies the file hash, imports, and runs the check script, whose expected row count and digest
come from the manifest, never from the loaded table. When the server cannot read the
client's files, which rules out `BULK INSERT`, use `loader/upload_ahah.ipynb` instead: it sends the
rows through pyodbc in chunks, then runs the same digest check and shows the table in use. Regenerate it
after a rebuild with `python loader/make_notebook.py`. `loader/compare_sql_with_sources.py` then compares every
cell of the loaded table with the original GeoDS files, independently of the build. `loader/sqlserver_probe.sh` runs the loader's SQL
against a throwaway SQL Server 2022 container and adds two probes: SQL Server's rendering of
chosen cells equals the CSV text, and the left join by data zone returns every cohort row once
with its status (`matched`, `no_code`, `other_vintage`, `not_a_datazone`).

## Join

By data zone only, with a left join so no cohort row disappears. Version 4 on 2011 zones:

```sql
SELECT c.pseudo_id, a.dentist, a.GP, a.hospital, a.pharmacy,
       a.domain_h, a.domain_g, a.domain_e, a.domain_r, a.ahah, a.ahah_rnk, a.ahah_pct,
       CASE WHEN c.DataZone2011Code IS NULL OR LTRIM(RTRIM(c.DataZone2011Code)) = N'' THEN N'no_code'
            WHEN a.datazone_code IS NOT NULL THEN N'matched'
            WHEN v.datazone_code IS NOT NULL THEN N'other_vintage'
            ELSE N'not_a_datazone' END AS ahah_status
FROM cohort AS c
LEFT JOIN ahah_datazone AS a ON a.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND a.ahah_version = N'4'
LEFT JOIN ahah_datazone AS v ON v.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND v.ahah_version = N'5.1';
```

The overall rank alone identifies the data zone, so raw values are for use inside a safe haven;
the release form is decided separately (`docs/AHAH_Plan.md`, disclosure section).

## Licence and attribution

AHAH is published under the UK Open Government Licence v3.0 (GeoDS access tier "Open"). Cite
Daras K, Green MA, Davies A, Barr B, Singleton A (2019), *Scientific Data* 6, 107,
doi:10.1038/s41597-019-0114-6, and state that the data were provided by the Geographic Data
Service, a Smart Data Research UK investment, ES/Z504464/1. The data zone lists are Scottish
Government open data under the same licence.

## Repository layout

```text
ahah_ingest/     the build: sources.yaml (pins), mapping.yaml, output_schema.yaml, decisions.yaml, code
data/sources/    pinned downloads (not committed) and their SOURCES.md (committed)
results/         build output; manifest.json and BUILD_REPORT.md are committed
docs/            plans, reviews, data dictionary, generated SQL, how it is built, updating
loader/          the SQL Server loader, the pyodbc upload notebook and the container probe; copy to local/ to fill in
tests/           31 unit tests plus 6 that need the pinned files
```

## Documents

- `docs/HOW_IT_IS_BUILT.md` and `docs/UPDATING.md`.
- `docs/AHAH_Plan.md` and `docs/AHAH_SQL_Plan.md`: the plans, reviewed in six rounds with the implementation (`docs/reviews/`).
- `docs/DATA_DICTIONARY.md`, `docs/PERCENTILES.md`.
- `ahah_ingest/decisions.yaml`: the decision log; its hash travels in the Parquet and the manifest.
- `results/BUILD_REPORT.md`: every check, rows per edition, three zones cell for cell against the source.
