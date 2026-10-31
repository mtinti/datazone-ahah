# Response to the build, notebook and provenance review of 31 October 2026

Review: [AHAH_build_notebook_and_provenance_review_2026-10-31.md](AHAH_build_notebook_and_provenance_review_2026-10-31.md).
Both P2 findings concern the promotion step added that morning; both reproduce from the code,
and the design was replaced rather than patched.

| # | Finding | Reproduced | Fix | Test or probe |
| --- | --- | --- | --- | --- |
| 1 | P2: a failed rollback move still deleted the backup folder | yes: the `finally` ran `rmtree` on `.previous_*` whatever happened in the `except` | there is no rollback any more and nothing is deleted before the new generation is in place (see 2) | `test_promotion_interrupted_before_the_journal_leaves_the_old_generation`: a failure while placing the new files leaves the old four untouched |
| 2 | P2: four sequential renames expose an incomplete folder; a signal skips the Python rollback | yes | journaled, forward-only promotion in `pipeline.promote`: (1) the new files are placed beside the old as `<name>.new`; (2) a journal is written atomically; (3) each `.new` replaces its file by atomic rename; (4) the journal is removed. A crash before (2) leaves the old generation complete; after (2) the new generation is already complete on disk and `recover()` finishes the swap, which `build()` runs first and `python -m ahah_ingest.pipeline --recover` runs by hand. Consumers cannot use a mixture: `verify_results` refuses a folder with a journal or `.new` files, and with `files=True` a Parquet or CSV whose SHA256 is not the manifest's. The dictionary, the notebook generator, the SQL probe (`--verify`) and the site's evidence all read the manifest through it | `test_promotion_interrupted_after_the_journal_is_finished_forward_and_refused_meanwhile` (the exact mixed state), `test_a_build_recovers_before_it_starts_and_a_pending_journal_blocks_promotion`, `test_verify_results_refuses_a_file_the_manifest_does_not_describe`; and [probes/promotion_kill_probe.py](probes/promotion_kill_probe.py), which SIGKILLs a child between two renames: mixture plus journal on disk, nothing deleted, `verify_results` refuses, `recover` completes, output `PROBE PASSED` |
| 3 | P3: usage comment says `sh` | yes | comment says `bash`, with the reason | none needed |

What this does not give: a single atomic swap of four files, which a POSIX filesystem has no
operation for. The guarantee is instead that a consumer never reads a mixture (it is refused with
the recovery command) and that recovery is always forward and never destructive. The limit of the
`files=False` path, used by the dictionary and the site, is that it checks only the journal and
`.new` markers, not the hashes.

On the note's item 1: the reviewer's response to my check (`UPLOAD_NOTEBOOK_NOTE_2026-10-31_check-response.md`)
showed by probe that the pool hands a later handle the physical connection in manual-commit mode,
which pyodbc records as `autocommit=True` without resetting; my reasoning about the `with` block
was beside the point. `pyodbc.pooling = False` is the fix that matters and is in. The check file's
verdict on item 1 stands corrected by that response.

My findings on the review are closed. The suite is 74 tests passing. Pages enablement remains with
Michele.
