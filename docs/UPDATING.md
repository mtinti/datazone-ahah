# Updating: a new AHAH edition or a corrected file

A build never searches for or accepts "latest". Each edition is chosen, downloaded, hashed and
pinned by hand; the build then refuses any other bytes.

## A new edition (for example 6)

1. Download the index CSV and its data summary from GeoDS with a personal account. Record the
   files, hashes, byte counts and licence shown in `data/sources/<folder>/SOURCES.md`, as the
   existing files do.
2. Add the edition to `ahah_ingest/sources.yaml`: version, year, file, SHA256, summary and its
   SHA256, the Great Britain row count the summary states, the data zone vintage and the code
   column. If the vintage is new, pin its data zone list under `datazone_lists`.
3. Run `python -m ahah_ingest.columns`. It reads the new header and fails if a column is unknown
   or if the presence matrix (`columns.PRESENCE`) disagrees with the file. Extend `SHORT` or the
   matrix deliberately, with a decision log entry, never by guessing a name.
4. Add the edition's units and definitions to `dictionary.UNITS`.
5. Build, read `results/BUILD_REPORT.md`, run `pytest`, regenerate the SQL and the dictionary.
   The CSV digest changes; copy the new hash, row count and digest into the loader's EDIT block
   from the manifest (the pipeline does not do this).
6. Record the decision in `ahah_ingest/decisions.yaml`.

## A corrected file from the publisher

A corrected file (for example, indicator percentiles moved to the 1 to 100 scale) is a new pin,
not an edit of the existing one: new hash in `sources.yaml` and `SOURCES.md`, a decision log entry
saying what changed and why, and a new build. Keep the earlier file's hash in the log as evidence.

## The data zone lists

data.gov.scot refreshes the lookups when higher geographies change; the codes do not. A refreshed
file is a new pin with a new hash. Both lists are cp1252; the registry says so and the reader
honours it.
