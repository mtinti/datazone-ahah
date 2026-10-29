# Plan: ingest the AHAH index for Scotland

Status: proposed, 29 October 2026. The files of every version are downloaded and pinned (see
`data/sources/*/SOURCES.md`). Nothing is built yet.

## Aim

Bring the Access to Healthy Assets and Hazards index (AHAH) into the safe haven as a pinned,
checked table for Scotland's data zones. The first user is HEAL-Scot, whose data request asks
for AHAH linked by data zone.

AHAH is published by data zone, and the data travels with data zones. A project joins it on the
data zone code its records already carry, real or pseudonymised. Postcodes are not needed. A
project that holds postcodes and no data zone can get the zone from the postcode-simd tables
first, but that is an optional extra route, not the design.

The build follows the one we already use for SIMD, in
[postcode-simd](https://github.com/mtinti/postcode-simd). Each section below links to the part of
that repository that solved the same problem.

## What AHAH is

AHAH is published by the Geographic Data Science Lab at the University of Liverpool, and hosted
by the Geographic Data Service (GeoDS). It scores every small area of Great Britain on how near
it is to things that help or harm health.

| Domain | Indicators |
| --- | --- |
| Retail environment | fast food outlets, pubs and bars, tobacconists, gambling outlets |
| Health services | GP surgeries, hospitals, pharmacies, dentists, leisure centres |
| Physical environment | blue space, active green space, passive green space (vegetation index from satellite images) |
| Air quality | NO₂, PM₁₀, SO₂ |

The 15 indicators make four domain scores and one overall index. Each has a value, a rank and a
percentile.

What the [GeoDS page](https://data.geods.ac.uk/dataset/access-to-healthy-assets-hazards-ahah)
says on 29 October 2026:

| | |
| --- | --- |
| Current version | 5.1, May 2026 |
| Licence | UK Open Government Licence |
| Access | every download needs a GeoDS login |
| Scotland's areas | 2022 data zones (`DZ22CD`) from version 5. Version 4 and earlier use 2011 data zones |
| Files | the index, domains and indicators (CSV), the same with boundaries (Parquet), a data summary (CSV), a variable dictionary (CSV), the methodology report (PDF) |
| Older versions | versions 1 to 4 (2016 to 2024), in a separate GeoDS record |
| Code | [GeographicDataService/ahah](https://github.com/GeographicDataService/ahah), tags v3, v4 and v5. The repository `AHAH_V5` named on the GeoDS page does not exist |

The downloaded files confirm this (see `data/sources/geods/SOURCES.md`). Version 5.1 has 7,392
Scottish rows, the 2022 data zones, although its code column is named `lsoa21cd` and the
dictionary says "(2011)". Versions 1 to 4 each have 6,976 Scottish rows, the 2011 data zones.

## Which edition HEAL-Scot releases: version 4 or version 5.1

**Decided on 29 October 2026: HEAL-Scot takes version 4**, on the 2011 data zones, as the data
request asks. The build still carries every edition; the choice of which edition to match and
release is made at release time, not in the build. The rest of this section records how the
decision was reached.

- The data request (DRS) asks for **version 4**. Version 4 uses the 2011 data zones, which
  matches the DRS's mapping of 2011 data zones to pseudonymised IDs.
- DataLoch's data specification (DSF) offers **version 5.1**, on the 2022 data zones. A mapping
  built for 2011 zones cannot reach those.

The two vintages do not correspond one to one, so neither version can be converted to the other
vintage. The postcode-simd plans refuse such conversion for the same reason. The project must
choose a version, and then map the data zones of that vintage. Both can be released, each on
its own mapping, if the project wants both.

The examples in this plan use version 5.1.

## The design, step by step

### 1. Pin the source

Every file the build reads is named in a registry with its URL, publisher, licence and SHA256.
Changed bytes stop the build. Nothing is updated silently.

- In postcode-simd: [`simd_ingest/sources.yaml`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/sources.yaml)
  and the fetcher, [`simd_ingest/core/fetch.py`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/core/fetch.py).

AHAH needs a login, so the build cannot download it. Someone downloads the files once by hand
and puts them in the source folder. The build then runs in offline mode and checks each hash, as
postcode-simd does with `--source-mode offline`. The registry records the GeoDS page, the
version, the date of download and who downloaded it.

The files to pin: the CSV of the index, the variable dictionary, the data summary and the
methodology report. The Parquet file with boundaries is not needed: the data zone code is enough
to join.

### 2. Archive the source

The downloaded files can go into a Zenodo record, so the build can be repeated if GeoDS moves or
retires them. What the GeoDS pages say, read on 29 October 2026:

- The [dataset page](https://data.geods.ac.uk/dataset/access-to-healthy-assets-hazards-ahah)
  gives the licence as the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/),
  and marks the dataset "Open". The OGL allows copying and redistribution, with attribution.
- The [About page](https://data.geods.ac.uk/about) says Open data are "freely available to all
  for any purpose following a simple registration", and "can be used by all with attribution".
  A user agreement is described only for Safeguarded and Secure data.
- The attribution asked for is the paper (Daras K, Green MA, Davies A, Barr B, Singleton A, 2019,
  *Scientific Data* 6, 107, [doi:10.1038/s41597-019-0114-6](https://doi.org/10.1038/s41597-019-0114-6))
  and the statement that the data were provided by the Geographic Data Service, a Smart Data
  Research UK investment, ES/Z504464/1.

No further terms were shown at registration or download (Michele Tinti, 29 October 2026). The
files can therefore be archived under the OGL, with the attribution above. The GeoDS user guide,
`https://service.geods.ac.uk/user_guide.pdf`, did not respond on 29 October 2026 and is not
read.

- In postcode-simd: [`docs/plans/Zenodo_Plan.md`](https://github.com/mtinti/postcode-simd/blob/main/docs/plans/Zenodo_Plan.md),
  the upload script [`simd_ingest/zenodo_sources.py`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/zenodo_sources.py),
  and the published sources record [10.5281/zenodo.23119743](https://doi.org/10.5281/zenodo.23119743).
  The registry's `redistribution` and `mirror` fields say what may be uploaded and where each
  copy is.

### 3. Read and check

Keep the Scottish rows, those whose code starts with `S01`. Store each value as published.
Nothing is recalculated.

The build fails, rather than warns, when:

- a code is not a data zone of the edition's vintage: 2022 for version 5.1, 2011 for versions
  1 to 4;
- a data zone is missing, or appears twice. Scotland has 7,392 data zones of 2022 and 6,976 of
  2011. The list to check against is the official data zone list of that vintage, pinned as
  a source of its own (the Scottish Government boundaries or lookup for 2011 and for 2022), not
  a list taken from postcodes;
- a column named in the edition's mapping file is missing, or has an unexpected type, or a
  column of the file is not in the mapping;
- the row count of the whole file, before the Scottish filter, differs from its data summary
  (the summaries count Great Britain: 41,729, 42,648 or 43,064 rows);
- a rank, percentile or decile is outside its range. Indicator percentiles run 0 to 100 and
  domain and index percentiles 1 to 100, as published (`PERCENTILES.md`); an issue was logged
  with the authors on 29 October 2026 and the values are kept as they are.

- In postcode-simd: the checks are in [`simd_ingest/core/checks.py`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/core/checks.py),
  and the rules are explained in [`docs/HOW_IT_IS_BUILT.md`](https://github.com/mtinti/postcode-simd/blob/main/docs/HOW_IT_IS_BUILT.md).

### 4. One table, keyed by data zone

The output is one row per data zone per edition, keyed by edition and data zone code. It has
every published value, rank, percentile and decile, stored as published. Column names are those
of the version 5.1 file; earlier editions map onto them, and a column an edition does not
publish is NULL for it. The shape, the types and the per-edition rules are in
`AHAH_SQL_Plan.md`.

This table is the product. A project's records join to it on their data zone code. For
HEAL-Scot, the pseudonymised zone is mapped back to the real code inside the safe haven first,
and that mapping must be of the same vintage as the AHAH version.

AHAH is not added to the postcode-simd tables. If a project has only postcodes, those tables
already give each postcode its `DataZone2011Code` and `DataZone2022Code`, so the zone can be
found there first. That is a convenience for such projects, not part of this build.

- In postcode-simd: the output schema and its column descriptions,
  [`simd_ingest/output_schema_history.yaml`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/output_schema_history.yaml);
  the export rules, [`simd_ingest/export_contract.yaml`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/export_contract.yaml).

### 5. Load into SQL Server and check the load

The build writes a CSV and a manifest with its row count and a digest of every row. A generated
import script loads it into SQL Server, and a generated check script recomputes the digest on
the loaded table.

- In postcode-simd: [`simd_ingest/sql_check.py`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/sql_check.py)
  writes [`docs/sql/import_csv.sql`](https://github.com/mtinti/postcode-simd/blob/main/docs/sql/import_csv.sql)
  and [`docs/sql/check_loaded_digest.sql`](https://github.com/mtinti/postcode-simd/blob/main/docs/sql/check_loaded_digest.sql).

### 6. Example joins

The main query adds AHAH to a table by its data zone code. Each row gets a status: the code is
empty, is not a data zone, is a data zone of the other vintage, or matched. A code of the other
vintage is never converted. Unlike SIMD, there is no PHS guidance on which AHAH version to use
for which year. The README says so, and the query uses the version the project chose.

A second, optional query shows how a project with postcodes only finds the zone first, through
the postcode-simd history table.

- In postcode-simd: the data zone procedure in the plan for SQL Server procedures. The plan is
  on this machine and not yet committed: `~/git_projects/SIMD/docs/plans/SIMD_Procedure_Plan.md`,
  section "The data zone procedure". It sets out the statuses, the vintage rule and the code
  clean-up (trim and upper case only). An AHAH query or procedure would follow it.
- For the optional postcode route: [`docs/sql/spd/link_as_of.sql`](https://github.com/mtinti/postcode-simd/blob/main/docs/sql/spd/link_as_of.sql)
  and [`docs/LINKAGE_BY_ERA.md`](https://github.com/mtinti/postcode-simd/blob/main/docs/LINKAGE_BY_ERA.md).

### 7. Record the decisions

Every policy choice goes into a decision log with its reason and the evidence: the version, the
vintage, the Scottish filter, and what the build refuses.

- In postcode-simd: [`simd_ingest/decisions.yaml`](https://github.com/mtinti/postcode-simd/blob/main/simd_ingest/decisions.yaml),
  and the runbook for new releases, [`docs/UPDATING.md`](https://github.com/mtinti/postcode-simd/blob/main/docs/UPDATING.md).

## Disclosure

The AHAH values and ranks of every data zone are public. A released rank or value can
therefore identify the zone, as a SIMD domain rank can; a few ranks are tied, which is why
"can" and not "does". What must be assessed is the complete released combination, SIMD bands
and every AHAH edition included. Percentile bands lower the risk but do not
remove it. For SIMD 2020v2, the seven domain quintiles alone single out 1,923 of the 6,976 data
zones (27.6%). The same count should be run for the AHAH bands the project wants to release,
before extraction. What is released is decided at extraction, not by the build.

## Tests

- Hashes: a changed file stops the build.
- Checks: a synthetic file with a missing zone, a duplicate zone, a 2011 code in a 2022 file, a
  missing column, and an out-of-range rank each fails with its own message.
- Values: a sample of zones, chosen in advance, equals the published CSV cell for cell.
- Join by data zone: a code of the right vintage matches. A code of the other vintage, an empty
  code and a malformed code each get their status. Lower case and surrounding spaces match.
  Every zone of the official list finds exactly one AHAH row.
- SQL Server: the import and check scripts load the synthetic table and pass, and fail on a
  changed value.

- In postcode-simd: [`tests/`](https://github.com/mtinti/postcode-simd/tree/main/tests), for
  example `test_pipeline.py`, `test_snapshot_pins.py` and `test_exports.py`.

## Order of work

1. Settled on 29 October 2026: HEAL-Scot releases version 4. What is matched is decided at release time; the build carries all five editions.
2. Done on 29 October 2026: the files of versions 1 to 5.1 are downloaded, their hashes
   recorded, and the variable dictionary and methodology report read.
3. Write the registry, the reader and the checks, with their tests.
4. Write the output table, the CSV, the manifest and the SQL scripts.
5. Write the example joins and the README.
6. Archive the sources on Zenodo, with the attribution GeoDS asks for.

## Open questions

- ~~Which edition HEAL-Scot releases.~~ Settled: version 4 (29 October 2026). The build ingests all five editions; what is matched and released is decided later.
- Whether this lives in its own repository, as assumed here, or as a new source inside
  postcode-simd.
- Which AHAH columns HEAL-Scot needs. A HEAL-Scot meeting page (Jira/Confluence, read 29 October
  2026) lists twelve version 4 columns: the code, four health indicators (`ah4dent`, `ah4gp`,
  `ah4hosp`, `ah4phar`), the four domain scores (`ah4h`, `ah4g`, `ah4e`, `ah4r`) and the overall
  score, rank and percentile (`ah4ahah`, `ah4ahah_rnk`, `ah4ahah_pct`). All twelve are in the
  pinned v4 file and in the table (as `dentist`, `GP`, `hospital`, `pharmacy`, `domain_h`,
  `domain_g`, `domain_e`, `domain_r`, `ahah`, `ahah_rnk`, `ahah_pct`, edition `4`). They are
  raw scores and a rank, so released as they are they identify the data zone outright: the
  rank alone is unique for every zone. The release form, bands or values, is still to decide.
