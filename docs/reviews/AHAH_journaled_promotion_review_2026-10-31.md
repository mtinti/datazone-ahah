# Review of journaled promotion and consumer guards — 31 October 2026

Reviewed commit: `7b10be7dd929dd5e0564f352786ca768c5ad5502` (version 0.2.0), covering changes
since `521f2e405aa570100665d80a3501e274fa9b672d`. The checkout was clean at the start.

Two P2 findings remain, both requiring overlapping operations on the same `results/` directory.
Recovery after a stopped, single writer now works in the tested cases. The new notebook generator
guards also pass. GitHub Pages is enabled and publishing successfully.

## Findings

### 1. P2 — Recovery can delete a running build's prepared generation

Location: [ahah_ingest/pipeline.py, lines 133–136](../../ahah_ingest/pipeline.py#L133), reached
automatically by [build(), line 64](../../ahah_ingest/pipeline.py#L64).

`recover()` deletes every `.new` file and staging directory without checking whether a writer is
still using them. No process lock or other ownership mechanism serializes recovery with a build.
Consequently, a second build's automatic recovery, or a concurrent `--recover`, can discard the
first build's files while that build is still running.

Reproduced with a real child process running `build()` in a temporary directory, using labelled
fixture generations with valid file hashes:

1. Pause the child after all four new outputs have moved to `<name>.new`, immediately before
   `_write_atomic()` writes the journal. The old generation is still intact.
2. Call `recover()` from the other process. It reports `removed 5 leftover(s) of an unfinished
   build`: four new files and the live writer's staging folder.
3. Resume the writer. It writes the journal, `_swap()` skips all four now-missing `.new` files,
   removes the journal and returns the **new** manifest successfully.
4. `verify_results()` subsequently passes, but its manifest and all four installed outputs are
   still the **old** generation. The newly built generation has been deleted without the writer
   reporting failure.

The pause controls scheduling; it does not alter rename behavior or inject a filesystem error.
Only the expensive data-building function was replaced with a fixture writer. This demonstrates
a silent loss of a completed build, not merely an interrupted build returning an error.

Make build and recovery share exclusive ownership of the results directory before inspecting or
deleting another operation's files. That ownership must cover preparation as well as publication;
a journal written only after preparation cannot establish it. Add a two-process regression for
this overlap, including the automatic recovery at the beginning of a second build.

### 2. P2 — Verification can succeed while the directory contains a mixture

Location: [ahah_ingest/pipeline.py, lines 146–160](../../ahah_ingest/pipeline.py#L146).

`verify_results()` checks for a journal and `.new` files once, before reading the manifest and
hashing the data files. A writer can begin promotion after that check. Verification has no read
lock or stable snapshot, so hashes obtained at different times do not establish that the files
beside the manifest still form the verified generation.

Reproduced with a second real child process and the normal SHA256 function:

1. Start verification of the complete old generation with `files=True`.
2. After it hashes the old Parquet, let the writer prepare the new generation, write the journal
   and replace only the Parquet. Pause that writer before the CSV replacement.
3. Let verification hash the still-old CSV and return.

The call succeeds and returns the old manifest even though `.promote.json` exists and the output
directory now contains **new Parquet + old CSV + old manifest**. Both individual hashes matched
when read; they did not describe the directory at the point it was accepted. Thus the new guard
does not enforce the stated rule that consumers refuse every mixed generation. A consumer that
opens the output paths after verification can use different files from the ones checked.

Coordinate readers with the publication lock for the duration of verification and consumption,
or have consumers use an immutable snapshot of the manifest and its files. The SQL probe's
separate `--verify`, manifest reads and CSV copy need the same protection. Merely checking that
no writer had started at the beginning is insufficient. Add a reader/writer overlap regression;
the existing static-marker and hash-mismatch tests do not exercise this sequence.

## Scope and assumptions

These findings are conditional on overlapping processes sharing one results directory. They do
not claim that an ordinary sequential build fails. There is currently no enforced single-process
restriction, and recovery runs automatically at the start of every build. If the intended scope
is strictly serialized use, enforce that restriction and state it in the guarantee.

The two earlier reproductions in the
[previous review](AHAH_build_notebook_and_provenance_review_2026-10-31.md) are addressed for
serialized use: the rollback path that deleted the backup has been removed, and the journal lets
recovery finish a killed writer's publication. The committed SIGKILL probe passes. The usage
comment now correctly invokes Bash. The new findings concern live overlap, which those tests
do not cover.

## Validation performed

| Check | Result |
| --- | --- |
| Full local suite, Python 3.12.11 | **74 passed** in 15.74 seconds |
| Fresh `git archive HEAD` checkout without ignored data/build outputs | **68 passed, 6 skipped** in 3.75 seconds; skips require those files |
| Committed `docs/reviews/probes/promotion_kill_probe.py` | Passed: SIGKILL, refusal of the interrupted state, forward recovery |
| Full build into a temporary directory | **342 checks passed**, 35,296 rows × 90 columns; only the four expected outputs remain |
| Verification of the rebuilt outputs | Passed with both file hashes matching the committed manifest |
| Notebook generator invoked by absolute script path from outside its checkout, without `PYTHONPATH` | Passed; all 15 cells' source and notebook metadata match the shipped notebook, ignoring random cell IDs |
| Notebook generator with a journal, a `.new` file, or a corrupted CSV | All three rejected with `ResultsIncomplete`; existing notebook preserved |
| SQL probe with the same three invalid states and a fake Docker executable | All three exited 1 at verification before starting the SQL import |
| Dictionary with either interruption marker | Both refused |
| Site evidence with either interruption marker | Both suppressed build pass evidence |
| Site generation and `mkdocs build --strict` | Passed: 90 columns, five editions, 12 sources, four documents, nine decisions, 327 cited checks |
| Bash syntax checks | Both the SQL probe and Pages publisher passed |
| Controlled two-process overlap probes | Reproduced both findings above |

The rebuild reproduced CSV SHA256
`505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574` and Parquet SHA256
`00561c1df048f3f19e0ffd369684b89e7a4d448386abe8dc4c92f32a1428ffc3`. Its identity correctly records
the reviewed clean commit and package 0.2.0. The committed manifest's package 0.1.0 remains valid
historical evidence for its recorded build commit `1b6263b`; it is not presented as a 0.2.0 build.

No new live SQL upload was needed for this diff: the generated notebook's execution cells are
unchanged from the notebook exercised against SQL Server in the previous review. This review
tested the changed generator and consumer guards rather than claiming another live upload run.

## Pages deployment is now resolved

GitHub reports Pages configured from `gh-pages`, folder `/`, with status `built`.
The [Pages workflow for the reviewed commit](https://github.com/mtinti/datazone-ahah/actions/runs/41186341537)
and [CI](https://github.com/mtinti/datazone-ahah/actions/runs/41186340686) succeeded.
The [live site](https://mtinti.github.io/datazone-ahah/) returned HTTP 200 and identifies the
site revision as `7b10be7`, package 0.2.0, with check evidence separately attributed to build
`1b6263b`. This closes the previous deployment blocker. No publishing or settings changes were
made by the reviewer.

All probes and generated artifacts were placed outside the checkout under the temporary review
directory `ahah-journal-review-ak8oz781`; the overlap probe and its JSON results are retained there
as `concurrent_promotion_probe.py` and `concurrent_probe_results.json`. Child processes were
resumed and reaped. This Markdown review is the only repository file added by the reviewer.
