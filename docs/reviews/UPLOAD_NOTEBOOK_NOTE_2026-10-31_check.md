# Check of `docs/UPLOAD_NOTEBOOK_NOTE_2026-10-31.md`

Date: 31 October 2026. Each claim of the note was tested against this repository, not read. The
sibling project uprn-epc is not checked out on this machine, so its files and the EPC probe record
the note cites could not be opened; what follows is about AHAH only.

| Item | Claim | Finding | Verdict |
| --- | --- | --- | --- |
| 1 | A pooled connection can carry an open implicit transaction into a later cell | Every connection in the notebook is opened with `with pyodbc.connect(...) as cn:` (cells 2, 6, 8, 10, 12, 14). pyodbc's documented context manager behaviour: `commit()` is called on exit even when `autocommit` is False; the connection is not closed. So a read-only cell's implicit transaction is committed when its block ends, and nothing is left open for the pool to hand on. The gap: on an exception inside the block, pyodbc's exit does not roll back, and the connection stays bound to `cn` until the next cell rebinds it, when the object is closed and pyodbc rolls back. No path was found in which a later `connect` can receive the session with the transaction still open. Not probed in a kernel (no pyodbc client here; see item 4). | premise does not hold as stated for this notebook; the four-line fix is still cheap and harmless, and `SET LOCK_TIMEOUT` turns any such wait into an error |
| 2 | `BULK INSERT` lacks `CODEPAGE = '65001'` | True: `docs/sql/import_csv.sql` line 115 has no `CODEPAGE`. The released CSV, decompressed, is 22,037,911 bytes with zero bytes above 127: every column is a code, a version label or a number, so the load is unaffected today. `CODEPAGE` is unsupported on SQL Server for Linux, where `loader/sqlserver_probe.sh` runs, so adding it breaks the probe unless the file is converted to UTF-16. | true, dormant. Better guard for this table: a build check that the CSV is pure ASCII, which makes the code page irrelevant and fails the build if a future edition changes that |
| 3 | The build writes into `results/` directly; a stop between Parquet and manifest leaves them inconsistent | True: `pipeline.py` writes the Parquet, then the CSV, then the manifest, in place. | true |
| 4 | No probe runs the notebook's own cells | True: `sqlserver_probe.sh` runs the SQL scripts with sqlcmd; the notebook was exercised by hand against a container on 29 October (`docs/sql/SQLSERVER_PROBE_2026-10-29.md`), not by an automated runner. | true |
| 5 | The probe runner can fail silently | Not as described. `set -eu` without `pipefail` is true, and line 45 ends in `\|\| true`. But a failing `sqlcmd` there yields an empty `probe_actual.txt`, and the `diff` against the 40 expected lines on the next line fails the run. On line 61 an empty result makes `grep -v '^$'` exit 1, which aborts under `set -e`. A partial result is caught by the diff. | a hygiene gap (`pipefail`), not a live silent failure |
| 6 | The site's checks have no applicability, coverage or condition | True that `CHECKS` is a (regex, sentence) list. Since the implementation review of today, every cited check must be a member of the manifest's exact name set and the descriptions state scope (Scottish rows only, set comparison). Applicability per column is in `lineage.py`, derived from the build's rules, not in a catalogue. | true; a catalogue would move what is now code into data |
| 7 | Decisions cannot revise one another | True: entries have `date`, `id`, `decision`, `why`. The file is parsed by the tests already (`test_every_decision_exists`). | true |
| 8 | Smaller items | Attribution kinds, page and hash for quoted descriptions: done today (`documents.yaml`, `column_descriptions.yaml`). Reading downloads with the script directory off `sys.path`: done ad hoc, not enforced. | partly done |

## Recommendation

- Now, half a day: `pyodbc.pooling = False`, `autocommit=True` on the read-only cells and `SET
  LOCK_TIMEOUT` in the writing cells (item 1, as belt and braces); `set -o pipefail` and explicit
  sqlcmd exit capture in the probe runner (item 5); a `csv.ascii` build check (item 2); staged
  build with promotion (item 3).
- Next release: the notebook probe (item 4), the check catalogue and decision statuses (6, 7).

## Implemented, 31 October 2026, commit after `072fdfd`

Items 1 (pooling off, autocommit on read-only cells, `cn.autocommit = True` after the DDL commit,
`SET LOCK_TIMEOUT 120000` in the cells that write or build temp tables), 2 (the build check
`csv.ascii`, which the released CSV passes with zero bytes above 127), 3 (staged build promoted as
one generation, with a rollback test) and 5 (`pipefail`, raw capture of each sqlcmd result, line
counts asserted before the diff) are in. The rebuild on the clean tree reproduced the CSV hash
`505e71b6…` with 342 checks. Items 4, 6 and 7 wait for the next release.
