# Response to notebook upload review round 2 (29 October 2026)

One finding, fixed.

**Guard tests depended on ignored build output (P2).** The `delivery` fixture now writes its own
one-row CSV whose header is the column list of the committed `docs/sql/import_csv.sql`, beside
copies of the two committed SQL scripts; no file under `results/` or `data/` is read. For the
step 3 tests, the notebook's step 2 (which hashes the real CSV) is replaced by the two names
step 3 takes from it, `header` and `path`. The comparison test is skipped unless the Parquet and
all five source files are present.

Verified in a `git archive` export with no `data/` or `results/`: 36 passed, 6 skipped, 0
errors. With the local artifacts: 42 passed.

Not covered by the self-contained fixture: step 2 itself, whose hash check is exercised by the
live runs recorded in `../sql/SQLSERVER_PROBE_2026-10-29.md` and by the reviewer's corrupt-CSV
probe. My findings on this review are closed.
