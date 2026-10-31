# How the table is built

Read this once for the rules; read `../results/BUILD_REPORT.md` for a particular run's
evidence, `../ahah_ingest/decisions.yaml` for the policy, and [UPDATING.md](UPDATING.md) for a
new edition. The plans in this folder are the design record and were reviewed in six rounds
(`reviews/`); this page is the implementation as it stands.

## One path

```text
ahah_ingest/sources.yaml ──► verify every pinned file's SHA256 (editions, summaries, data zone lists)
                                │
          read each edition as text ──► header equals the mapping ──► GB row count equals the summary
                                │
          keep the S01 rows ──► map file columns to table columns ──► Decimal for scores, int for ranks
                                │
          one frame, all editions ──► key unique ──► per edition: every zone of the vintage once,
          NULL exactly where the edition has no column, ranges, the version 2 code, rank unique
                                │
          write Parquet ──► reopen and compare every cell
          render text ──► write CSV ──► reopen and compare every cell ──► row digest
                                │
          manifest.json + BUILD_REPORT.md
```

The sequence is `build` in `../ahah_ingest/pipeline.py`. Every step runs every time. Any failed
check stops the build before a file is written.

## The rules

| Rule | Where | Evidence |
| --- | --- | --- |
| A pin is a hash; changed bytes stop the build | `core/sources.py: verify` | `source.*` checks |
| Every file column maps to exactly one table column; nothing dropped | `columns.py`, `mapping.yaml` | `v*.header_is_mapped`; the test that regenerates the mapping |
| Values never pass through a float | `reader.py`, `core/text_output.py` | `decimal_round_trip`; the rendering tests |
| A decimal that does not fit `decimal(38,20)` stops the build | `text_output.render_decimal` | `test_decimal_that_does_not_fit_is_refused` |
| NULL only where an edition has no column | `columns.PRESENCE`, `checks.check_edition` | `v*.presence_matrix` |
| Every zone of the vintage, once, from an independent list | `sources.yaml: datazone_lists` | `v*.every_zone_of_<vintage>_present_once` |
| Ranks, percentiles, deciles stored as published, GB-wide, 1 = healthiest | `decisions.yaml` | range checks per edition |
| v2 `-1` only in the eleven routed indicators and deciles of two zones | `checks.py` | `v2.no_route_code_zones`, `v2.no_route_code_outside_routed` |
| v1 and v2 domains are exponential-scale, kept apart from the probit scores | `mapping.yaml` | review round 3 and its probe |
| The CSV digest is computed from the accepted table, never from the file | `pipeline.py` | `check_loaded_digest.sql` compares with the manifest |

## The files that leave

- `results/ahah_datazone.csv.gz`: the shared form. Empty cell = NULL; decimals with 20 places.
- `results/ahah_datazone.parquet`: the same rows, typed, with the decision log hash in metadata.
- `results/manifest.json`: hashes, counts, the digest total, every check.
- The four outputs are written into a staging folder inside `results/` and published only after
  every check has passed, by a journaled, forward-only promotion: the new files are first placed
  beside the old ones as `<name>.new`, a journal is written, then each is renamed into place and
  the journal removed. A crash before the journal leaves the old generation complete; a crash
  after it leaves a mixture that `python -m ahah_ingest.pipeline --recover` (also run at the
  start of every build) finishes forward. Nothing is deleted before the new generation is in
  place. Every consumer reads the manifest through `verify_results`, which refuses a folder with
  a journal or `.new` files and, for the loader and the probe, a Parquet or CSV whose SHA256 is
  not the manifest's (`python -m ahah_ingest.pipeline --verify`). One process owns `results/`
  at a time, through an OS lock on `results/.lock` (`owned` in `pipeline.py`): a build holds it
  from its opening recovery until its promotion is published, and recovery and verification
  hold it for their whole run, so recovery never deletes a running build's prepared files and
  verification never hashes files mid-swap. A second claimant is refused at once (`ResultsBusy`),
  and the kernel drops the lock when its holder dies. The SQL probe copies the CSV out under
  that ownership (`--export`) and reads only the copy. The manifest records the
  build identity (commit, whether the tree was clean, package and schema version), and the check
  `csv.ascii` asserts that no byte of the CSV is above 127, so no import code page can alter it.
- `docs/sql/import_csv.sql`, `docs/sql/check_loaded_digest.sql`: generated from the schema.
- `loader/load_ahah_to_sqlserver.py`: carries this build's hash, row count and digest.
