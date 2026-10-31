# Response to the review of results ownership — 31 October 2026

Review: [AHAH_results_ownership_review_2026-10-31.md](AHAH_results_ownership_review_2026-10-31.md).
Both findings reproduced from the code before the fix: the reentrancy cache was keyed by folder
alone, and the command dispatcher treated any argument list it did not recognise as a build.

## Finding 1, reentrancy must identify the owner: closed

`_HELD` in `ahah_ingest/pipeline.py` is now keyed by `(pid, thread ident, folder)`, so only the
owning thread of the owning process takes the reentrant branch. Any other thread, and a forked
child (whose `_HELD` is cleared by `os.register_at_fork`), opens its own descriptor and asks the
kernel for the lock, which refuses it while the owner holds it. Inherited descriptors are left
alone, as the review asked: closing them in the child would not release the parent's lock, and
unlocking them would.

Regression `test_another_thread_or_a_forked_child_is_not_the_owner`: with ownership held in the
owner and a live staging folder on disk, a forked child calling `recover` exits refused
(`ResultsBusy`; the fork runs in a fresh single-threaded interpreter, since forking a threaded
process is deprecated), a second thread calling `recover` is refused, and the staging folder survives.
The same-thread nesting test is unchanged and still passes.

## Finding 2, malformed export selected a build: closed

`main` accepts exactly `[]`, `--recover`, `--verify` and `--export DIR`. Anything else prints a
usage line to stderr and returns 2 before any operation runs. Regression
`test_malformed_commands_neither_build_nor_export` replaces build, export and recover with
failing stubs and asserts the exit code and usage message for five malformed argument lists.

## What the tests do not cover

- A thread that forks while another thread holds ownership: `register_at_fork` clears the cache,
  so the child takes the OS path, but the test forks from a single-threaded owner only.
- Windows: no `fork`, and `msvcrt.locking` is still unexercised.
- Shared filesystems across hosts, as before.

## Validation

| Check | Result |
| --- | --- |
| `python3 -m pytest tests/` | 79 passed (77 before), no warnings |
| `python3 -m ahah_ingest.pipeline --export` (no destination) | usage message, exit 2, no build |
| `python3 -m ahah_ingest.pipeline --verify` | results complete, 35,296 rows |
| `docs/reviews/probes/promotion_kill_probe.py` | PROBE PASSED |

Outputs unchanged; no rebuild.
