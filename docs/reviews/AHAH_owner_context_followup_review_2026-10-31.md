# Review of owner-context and command-validation fixes — 31 October 2026

Reviewed commit: `028e78d4225ee3cf6a136d574bab935d6939b802`, including the implementation in
`15f58bd`, against the preceding reviewed commit `1370934`. The checkout was clean.

Malformed commands are now rejected correctly. Competing threads and forked children no longer
take the reentrant path and delete the owner's staging files. One P2 follow-up remains in fork
cleanup. It is **not a blocker for the current documented CLI workflow**, which does not fork
while holding ownership.

## Finding

### P2 — Complete fork cleanup: clearing the cache leaves inherited locks and contexts behind

Location: [ahah_ingest/pipeline.py, lines 68–70](../../ahah_ingest/pipeline.py#L68), together with
the inherited context cleanup at [lines 92–94](../../ahah_ingest/pipeline.py#L92) and
[lines 108–112](../../ahah_ingest/pipeline.py#L108).

The child callback clears `_HELD`, but it does not close the lock descriptors inherited from the
parent. Those descriptors still exist even though the child no longer tracks them. This breaks
the guarantee that a killed owner releases the lock, when a forked child survives that owner.
It also leaves inherited `owned()` contexts trying to remove records that the callback deleted.

Two reproducible consequences were checked in fresh interpreters on the local POSIX filesystem:

1. **A surviving child keeps a dead owner's lock.** A process entered `owned(results)`, forked a
   child and remained inside the block. The child waited without acquiring ownership itself.
   After the supervisor killed and reaped the owner with SIGKILL, an independent claimant still
   received `ResultsBusy`. It could acquire ownership only after the child exited. Thus recovery
   can remain blocked by an unrelated long-lived child after the actual build process has died.
2. **Ordinary child unwinding raises `KeyError`.** A child forked inside `with owned(results)`
   was allowed to leave that block normally. Cleanup reached `del _HELD[key]` for the parent's
   captured key, but the fork callback had cleared it, so the child raised `KeyError`.

The new committed regression calls `os._exit()` in the child and waits for that child before the
parent leaves ownership. It verifies refusal while the parent lives, but neither of these cleanup
cases. The existing SIGKILL probe has no surviving forked child, so it also passes.

Close the child's inherited lock descriptors before clearing its ownership records, without
calling unlock on the parent's shared lock. Closing the child's copy while the parent retains
its descriptor does not release the parent's lock. Make inherited context unwinding recognize
that it is running in a different process, so it does not access cleared records, unlock the
parent's lock or close an already-cleaned descriptor. Cover both a surviving child after owner
death and normal child exit from an inherited ownership block.

This is the incomplete part of the preceding recommendation to reset inherited ownership and
close inherited descriptors appropriately. The response's choice to leave the descriptors alone
prevents an accidental explicit unlock, but also leaves these two lifecycle problems.

## Status of the previous findings

- **Malformed export selected a build: closed.** Five real command-line invocations with malformed
  arguments returned exit code 2 and a usage message, with no normal output and no changes to the
  temporary checkout's manifest or build report. These included a missing export destination and
  an extra export argument. A valid export to a directory containing spaces succeeded.
- **Reentrant ownership bypass: original reproductions fixed.** The regression refuses both a
  competing thread and a forked child while retaining the owner's prepared file. Same-caller
  nesting still passes. The remaining issue concerns the inherited descriptors and context
  cleanup described above, rather than the original destructive bypass.

Previous review: [results ownership review](AHAH_results_ownership_review_2026-10-31.md).

## Validation performed

| Check | Result |
| --- | --- |
| Full local suite, Python 3.12.11 | **79 passed** in 17.92 seconds |
| Fresh `git archive HEAD` checkout without ignored source/build data | **73 passed, 6 skipped** in 5.08 seconds; skips require those files |
| Committed SIGKILL/recovery probe | Passed |
| Real CLI: `--export`, `--export one two`, `--verify x`, `--recover --verify`, `build` | All returned usage errors with exit code 2; saved manifest/report unchanged |
| Real CLI: `--verify` | Passed against the existing 35,296-row release |
| Real CLI: `--export` to a destination with spaces | Passed; exported manifest matches the source and CSV hash matches that manifest |
| Forked child survives killed owner | Reproduced lock retention until the child exited |
| Forked child leaves inherited ownership normally | Reproduced `KeyError` |
| Git whitespace check | Passed |

The exported CSV SHA256 was
`11351af109e574017a8d00f493d044dd92942f42c72624fa0c4efe054da6d5d8`, matching the existing manifest.
The data transformations, notebook cells and SQL bodies did not change in this diff; this review
did not repeat the full data build, live SQL upload or notebook kernel run.

The [CI run](https://github.com/mtinti/datazone-ahah/actions/runs/41196177930) and
[Pages workflow](https://github.com/mtinti/datazone-ahah/actions/runs/41196177909) for the reviewed
commit succeeded. Windows locking and filesystems shared across hosts were not exercised.

The fork finding applies only when a process forks while ownership is held. The ordinary CLI
workflow remains usable, and the earlier non-blocking assessment still applies. Complete the
cleanup before relying on this API from fork-based callers.

Probes and artifacts are retained outside the checkout under
`ahah-owner-context-review-l84_wukd`, including `fork_lifecycle_probe.py`,
`fork_lifecycle_results.json` and `cli_results.json`. The killed owner was reaped, the surviving
child was released, and ownership could subsequently be acquired. This review is the only
repository file added by the reviewer; implementation files and earlier reviews were preserved.
