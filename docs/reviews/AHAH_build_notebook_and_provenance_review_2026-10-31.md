# Review of the build, notebook and provenance updates — 31 October 2026

Reviewed commit: `521f2e405aa570100665d80a3501e274fa9b672d`, including the changes since
`d73500975f18633649db4d244a6e247527c1c6dd`. This covers the provenance review fixes, staged
build promotion, the ASCII check, notebook connections and lock timeouts, and the SQL probe.
The edited upload note and its untracked response were read as supporting material and preserved.

Two P2 findings remain in build promotion. The notebook upload and provenance corrections passed
the checks below. GitHub Pages is still disabled: the new diagnostic works, but publication remains
open. There is also one P3 correction to the probe's usage instruction.

## Findings

### 1. P2 — Keep the recovery files when rollback itself fails

Location: [ahah_ingest/pipeline.py, lines 84–91](../../ahah_ingest/pipeline.py#L84), together with
the staging cleanup at [lines 61–65](../../ahah_ingest/pipeline.py#L61).

`promote()` assumes every rollback rename succeeds. If one raises, its `finally` still deletes
the entire `.previous_*` directory; `build()` then deletes `.staging_*` as well. A second filesystem
error therefore destroys the old accepted generation instead of leaving it available for recovery.
This is the error path the new promotion code is meant to protect.

Reproduced in a temporary directory using the real `build()` and `promote()`, with only
`_build_into()` replaced by a writer of four labelled dummy outputs:

1. Start with four old outputs and write four new staged outputs.
2. Make `os.replace(staging/manifest.json, results/manifest.json)` raise `OSError`.
3. Also make the first rollback rename, `results/ahah_datazone.parquet` back into staging, raise.
4. After the exception, `results/` contains only the new Parquet and CSV. The old outputs,
   both manifests and both reports are gone; neither recovery directory remains.

Delete the backup only after promotion or rollback has completed successfully. On a rollback
failure, retain both directories, report their paths and preserve the original error as well as
the rollback error. Add a regression that injects failure during rollback. The existing
`test_promotion_is_all_or_nothing` deliberately makes its injected failure happen once and all
rollback moves succeed, so it cannot catch this case.

### 2. P2 — Sequential file renames do not publish a complete generation atomically

Location: [ahah_ingest/pipeline.py, lines 77–83](../../ahah_ingest/pipeline.py#L77).

All four current files are removed before any replacements are installed, and the new files are
then installed individually. During those operations `results/` is incomplete. Termination by
SIGTERM, SIGKILL or a process crash does not execute the Python rollback. This leaves the public
output directory incomplete after the process has stopped, contrary to the new guarantee that it
always holds one complete accepted build.

Reproduced by pausing a child process immediately after the first new file was promoted and then
sending it SIGTERM. The child exited with signal 15. `results/` held just the new
`ahah_datazone.parquet`; its CSV, manifest and report were absent. The old files survived under
`.previous_*`, but the implementation neither restores them automatically nor makes normal
consumers use that directory. Successful promotion also exposes incomplete intermediate states
to readers; catching Python exceptions does not change that.

Publish complete generation directories through one atomic pointer change, with consumers
resolving a generation once, or implement a durable recovery protocol that prevents consumers
from using an incomplete generation. Test interruption at promotion boundaries. Staging does
successfully protect the old outputs while the build and its validation are running; the remaining
gap is the publication step itself.

### 3. P3 — Change the documented probe invocation from `sh` to `bash`

Location: [loader/sqlserver_probe.sh, lines 1–6](../../loader/sqlserver_probe.sh#L1).

The script now needs Bash for `set -euo pipefail`, but its usage comment still says
`sh loader/sqlserver_probe.sh`. An explicit `sh` ignores the new Bash shebang. Running that
invocation in the Ubuntu 22.04 SQL Server container exited with status 2 at line 6:
`set: Illegal option -o pipefail`. Document `bash loader/sqlserver_probe.sh` or direct executable
invocation.

## Status of the previous provenance review

The fixes for findings 2–6 and both P3 notes in the
[previous implementation review](AHAH_provenance_site_implementation_review_2026-10-31.md)
are present and their regression tests pass:

- Absent editions cite their presence checks, including an injected failed absence check.
- Edition pages retain quotations, corrections and qualifications together.
- Edition 1 hospital, green-space and physical-environment descriptions are corrected against
  the pinned paper. The earlier assumption that A&E selection began in edition 5.1 remains
  withdrawn; edition 1 already used A&E hospitals.
- Check descriptions distinguish header names from order, Scottish rows from other rows, and
  each readback check's actual scope.
- Column pages show changed configuration alongside historical build results.
- The conventions page is generated and linked; indicator and domain percentile minima are
  stated separately.

Previous finding 1 is partly resolved: the ten-minute polling failure is replaced by an immediate,
accurate configuration error. Publication itself remains open. At review time GitHub reported
`has_pages: false`, and the [public site](https://mtinti.github.io/datazone-ahah/) returned HTTP 404.
The [latest Pages run](https://github.com/mtinti/datazone-ahah/actions/runs/41183379723) passed its
27 provenance tests, generation and MkDocs build, then failed with the expected message that
Pages is not enabled. The [CI run for the same commit](https://github.com/mtinti/datazone-ahah/actions/runs/41183379715)
succeeded. The repository still needs Pages configured to serve `gh-pages` from `/` before
publication can be verified. No repository settings or publishing actions were changed in this review.

## Validation performed

| Check | Result |
| --- | --- |
| Full local suite, Python 3.12.11 | **71 passed** in 15.63 seconds |
| Fresh `git archive HEAD` checkout, without ignored source data or built data files | **65 passed, 6 skipped** in 4.18 seconds; skips explicitly require the source data/build outputs |
| Full build into a temporary output directory | **342 checks passed**, 35,296 rows × 90 columns; all four outputs promoted and staging removed |
| Rebuilt data versus committed manifest | Both CSV and Parquet hashes match; CSV has zero non-ASCII bytes |
| Site generation and `mkdocs build --strict` | Passed; 90 column pages, five editions, 12 sources, four documents, nine decisions, 327 distinct cited checks |
| Built HTML links and anchors | 144 HTML pages, **5,653 local links checked**, no broken targets |
| Notebook regenerated in the temporary checkout | All 15 cells' source and notebook metadata match the shipped notebook; random cell IDs ignored |
| Actual notebook code cells in a Jupyter kernel against a fresh SQL Server | Loaded **35,296 rows**, all five SQL checks passed, all eight join cases passed |
| Session state after each notebook step | Pooling disabled; the connection exposed after each step had `autocommit=True` and `@@TRANCOUNT=0`; steps 3, 5 and 7 reported `@@LOCK_TIMEOUT=120000` |
| SQL probe's actual rendering and join queries against the loaded table | All **40 rendered cells** matched the CSV text; all **eight join results** matched expectations |
| Shell runner with a fake Docker executable | Success returned 0; rendering/join sqlcmd errors returned 23 even with complete correct output; short or empty rendering/join output returned 1 — seven scenarios passed |
| Bash syntax checks | `loader/sqlserver_probe.sh` and `.github/scripts/pages_publish.sh` passed |
| Promotion failure probes | Reproduced findings 1 and 2 above; ordinary successful promotion also checked |

The rebuild reproduced compressed CSV SHA256
`505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574`, Parquet SHA256
`00561c1df048f3f19e0ffd369684b89e7a4d448386abe8dc4c92f32a1428ffc3`, and digest
`1313739416145945439820`. Comparing check records required treating the two-code set in
`v2.no_route_code_zones` as a set: its string representation changed order between processes.
All check names, outcomes and semantic values agreed. The review build correctly records a dirty
tree because the upload note was already edited; it was not substituted for the committed manifest.

The notebook test used SQL Server 2022 Developer `16.0.4305.5`, pyodbc 5.3.0, ODBC Driver 18,
pandas 3.0.3 and a real kernel. Only connection settings and the delivery folder were changed in
the temporary notebook; diagnostic cells inspected session state between its own steps. Windows
and the HIC server were not exercised. The upload failure scenarios proposed for the future
automated notebook harness were not all rerun in this review.

The full shell runner could not access the Docker socket through its shell invocation under the
workspace sandbox. Its control flow was therefore tested with the fake executable, and its SQL
queries were separately run through permitted Docker commands against the real loaded table.
The bulk-import path was not rerun; the actual upload test used the notebook's pyodbc path.

All build, notebook, promotion and site artifacts were kept outside the checkout in the temporary
review directory `ahah-implementation-followup-3g2qm72e`. The temporary SQL Server container was
stopped and removed. Implementation files, existing reviews and the user's two pending documentation
changes were preserved; this review is the only repository file added by the reviewer.
