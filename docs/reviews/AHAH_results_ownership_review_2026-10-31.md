# Review of results ownership and snapshot export — 31 October 2026

Reviewed commit: `13709344308d032675f0eb12c6c9e75e21e5eaa2`, covering changes since `7b10be7`.
The checkout was clean at the start and remained unchanged throughout validation.

The two earlier overlap reproductions are fixed for independently launched processes. Verification
and export also correctly block competing writers, and export produces a stable copy. Two P2
findings remain: the ownership cache can be bypassed by another thread or a forked child, and
malformed `--export` arguments select the build operation.

## Findings

### 1. P2 — Reentrancy must identify the owning caller, not just the directory

Location: [ahah_ingest/pipeline.py, lines 67–89](../../ahah_ingest/pipeline.py#L67).

`owned()` skips the OS lock whenever the resolved directory appears in `_HELD`. That dictionary
is shared by all threads and copied into a child by `fork()`. Its entries contain a descriptor and
depth, but no owning process or thread identity. Consequently, an unrelated caller can take the
reentrant branch and enter the protected operation while the original owner still holds the lock.

Reproduced on the local POSIX filesystem using real `owned()` and `recover()` calls, with no
mocked locking or filesystem operations:

1. Create a temporary results directory and `.staging_live/prepared.txt`, representing a running
   build's prepared output.
2. Hold `with owned(results)` in the main thread.
3. From a second thread, call `recover(results)` while the owner remains inside its block.
4. Repeat separately with a child created by `os.fork()` inside the ownership block.

In both cases recovery returned `removed 1 leftover(s) of an unfinished build` and deleted the
live staging directory. The forked caller had a different PID; the threaded caller had a different
thread identity. Neither raised `ResultsBusy`. Thus the same deletion that the new ownership
protocol prevents between separately launched commands remains possible through its reentrant path.

Make reentrancy specific to the owning process and thread. Reset inherited ownership state after
fork and close inherited lock descriptors appropriately, without explicitly unlocking the parent's
shared lock. Add regressions for a competing thread and a forked child, while retaining the existing
same-caller nesting test.

This finding requires threaded API calls or a fork while ownership is held. The current command-line
entry points do not themselves create those callers; their independent-process behavior passed.
The broader one-owner guarantee in `owned()` is what the reproductions disprove.

### 2. P2 — Reject an incomplete export command instead of rebuilding results

Location: [ahah_ingest/pipeline.py, lines 361–371](../../ahah_ingest/pipeline.py#L361).

The new export branch matches only exactly two arguments. Other argument lists fall through to
`build()`. Therefore either of these commands starts a rebuild instead of reporting a usage error:

```text
python -m ahah_ingest.pipeline --export
python -m ahah_ingest.pipeline --export one two
```

The first is a missing destination; the second has an extra argument. An accidental export typo
can consequently replace the current output generation and its manifest, while producing no export.

Reproduced by calling the real `main()` dispatcher with each argument list and replacing only
`build()` with a call recorder to avoid an unintended rebuild. Both called `build()`, never called
`export_csv()`, printed the build-success message and returned 0. The fallback was already permissive
for unknown arguments; adding an option with a required destination now exposes it on malformed
uses of the documented export command.

Parse and validate the command before executing it. Select the default build only for an empty
argument list; reject missing or extra export arguments with a nonzero usage result. Add tests
asserting that malformed commands invoke neither build nor export.

## Closure of the preceding findings

The changes address the specific independent-process failures in the
[journaled promotion review](AHAH_journaled_promotion_review_2026-10-31.md):

- A running build owns the directory before recovery, through preparation and publication.
  Competing recovery, verification and another build are refused at both the pre-journal and
  mid-swap pause points in the committed regression test.
- In additional reader-first probes, verification held ownership after hashing the Parquet.
  Separately launched recovery, promotion, build, verification and export were all refused.
- Export held ownership after copying the CSV and before copying the manifest. The same competing
  operations were refused. After the owner finished and a new generation was promoted, the exported
  CSV still matched its own old manifest, confirming that the snapshot remained usable.
- The site refused build evidence while a reader/exporter owned the results directory.
- The committed SIGKILL probe passed: a killed writer released its lock, the interrupted generation
  was refused, and recovery completed publication.

## Validation performed

| Check | Result |
| --- | --- |
| Full local suite, Python 3.12.11 | **77 passed** in 16.34 seconds |
| Fresh `git archive HEAD` checkout without ignored source/build data | **71 passed, 6 skipped** in 4.47 seconds; skips explicitly require those files |
| Full build into a temporary directory | **342 checks passed**, 35,296 rows × 90 columns; four outputs plus `.lock`, with no promotion leftovers |
| Rebuilt data verification | CSV and Parquet hashes match the committed manifest |
| Full-data snapshot export | Manifest agrees with the build; uncompressed CSV hash matches the manifest |
| Verification-first and export-first subprocess probes | Competing operations refused; promotion succeeds after ownership is released |
| Committed SIGKILL/recovery probe | Passed |
| Notebook generator from outside its temporary checkout | All 15 cells' source and notebook metadata match the shipped notebook; random cell IDs ignored |
| SQL shell runner with a fake Docker executable | Completed through the new `--export` path; copied CSV bytes and generated digest expectation match the exported manifest |
| Site generation and `mkdocs build --strict` | Passed: 90 columns, five editions, 12 sources, four documents, nine decisions, 327 cited checks |
| Bash syntax and Git whitespace checks | Passed |
| Thread/fork ownership and malformed-argument probes | Reproduced findings 1 and 2 |

The build reproduced compressed CSV SHA256
`505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574`, Parquet SHA256
`00561c1df048f3f19e0ffd369684b89e7a4d448386abe8dc4c92f32a1428ffc3`, and exported uncompressed CSV
SHA256 `11351af109e574017a8d00f493d044dd92942f42c72624fa0c4efe054da6d5d8`.
Its build identity correctly records the reviewed clean commit and package 0.2.0.

This review exercised the changed snapshot/export plumbing with real files and mocked Docker
responses. It did not rerun a live SQL Server import or the notebook in a kernel; the notebook's
execution cells and SQL query bodies are unchanged. Windows locking and filesystems shared across
hosts were not exercised.

The [CI run](https://github.com/mtinti/datazone-ahah/actions/runs/41193987254) and
[Pages workflow](https://github.com/mtinti/datazone-ahah/actions/runs/41193987280) for this commit
succeeded. The [live site](https://mtinti.github.io/datazone-ahah/) returned HTTP 200 and names
revision `1370934`.

All probes and generated artifacts were kept in the temporary review directory
`ahah-ownership-review-lp61er6o`. Threads were joined and child processes were reaped. This review
is the only repository file added by the reviewer; implementation files and earlier reviews were
preserved.

## Blocking assessment — clarification, 31 October 2026

Neither finding blocks the current documented workflow: independently launched, single-threaded
commands with valid arguments passed the checks above. The P2 ratings indicate follow-up work,
not a requirement to stop using that workflow.

- The ownership bypass requires threaded API calls or a fork while ownership is held. Harden
  that path before introducing those callers; the current CLI does not create them.
- Valid export commands work. Missing or extra export arguments can unexpectedly select a
  rebuild, so argument validation is the next fix to prioritize.
