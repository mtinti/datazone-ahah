# Response to the review of the journaled promotion — 31 October 2026

Review: [AHAH_journaled_promotion_review_2026-10-31.md](AHAH_journaled_promotion_review_2026-10-31.md)
(and its [follow-up](AHAH_implementation_followup_2026-10-31_no_new_changes.md), which found no change
because the review had not been acted on). Both findings reproduced in principle from the code: nothing
serialised a build, a recovery and a verification on the same `results/` folder, and `verify_results`
read the folder's state in two steps.

## What changed

One process owns `results/` at a time. `owned()` in `ahah_ingest/pipeline.py` takes an OS lock
(`flock`, non-blocking) on `results/.lock`:

- `build` holds it from before its opening `recover` until its promotion is published and the
  staging folder removed. The lock covers preparation as well as publication, as the review asked;
  the journal no longer has to establish ownership.
- `recover`, `promote` and `verify_results` each hold it for their whole run. The marker test, the
  manifest read and the two hashes now describe one state.
- A second claimant is refused at once with `ResultsBusy` (a `ResultsIncomplete`), never made to
  wait and never allowed to act on another process's files. The kernel releases the lock when the
  holder dies, so the SIGKILL case still recovers with no stale lock to clear.
- The lock is reentrant within a process (`build` calls `recover` and `promote` under it).

Consumers that open the files after verifying them must do so under the same ownership. The SQL
probe used to run `--verify`, then read `results/manifest.json` twice and gunzip the CSV: four
reads of a folder a build could have changed between them. It now runs
`python3 -m ahah_ingest.pipeline --export "$W"`, which verifies and copies the manifest and the
uncompressed CSV into `$W` while owning the folder, and the script reads only `$W` from then on.
The notebook generator and the dictionary read nothing after `verify_results` returns. The
provenance site read `manifest.json` directly and tested the journal separately; it now reads
through `verify_results` (`read_manifest`), so one owned read decides both.

## Finding 1, recovery deletes a running build's prepared files: closed

Regression `test_a_running_build_owns_results_and_recovery_verification_and_a_second_build_are_refused`
in `tests/test_build_rules.py` runs a real `build()` in a child process (fixture outputs, real
renames) and pauses it at the review's point, after every `.new` file is in place and before the
journal is written. From the parent, `recover`, `verify_results` and a second `build` all raise
`ResultsBusy`; the old generation is untouched and all four `.new` files are still there. Released,
the child publishes the new generation whole and exits 0.

## Finding 2, verification passes on a mixture: closed

The same test pauses the child a second time after the first swap (journal present, one new file in
place, three `.new`). `verify_results` raises `ResultsBusy` instead of hashing. A verification that
starts before a promotion holds the lock until it returns, so the promotion cannot begin meanwhile.

## What the tests do not cover

- A filesystem where `flock` is advisory only across hosts (NFS, SMB shares). `results/` is a local
  folder in this repository; the guarantee is stated for one host.
- The Windows branch (`msvcrt.locking`) is written but not run. No consumer runs on Windows: the
  loader notebook reads the CSV, not `results/`.
- A consumer written later that calls `verify_results` and then opens the files outside
  `with owned(results)`. The docstring says so; nothing enforces it.

## Validation

| Check | Result |
| --- | --- |
| `python3 -m pytest tests/` | 77 passed (74 before, plus the overlap, reentrancy and export tests) |
| `docs/reviews/probes/promotion_kill_probe.py` (now ignores `.lock` in its listing) | PROBE PASSED |
| `python3 -m ahah_ingest.pipeline --verify` and `--export` | results complete, 35,296 rows; copy and manifest written |
| `bash loader/sqlserver_probe.sh` against a fresh SQL Server 2022 container | import, five digest checks, 40 rendered cells and 8 join rows all pass |
| `python3 -m ahah_ingest.provenance_site` then `mkdocs build --strict` | 90 columns, 327 cited checks, evidence usable; strict build clean |

No rebuild of `results/` was needed: the outputs and their hashes are unchanged by this change.
