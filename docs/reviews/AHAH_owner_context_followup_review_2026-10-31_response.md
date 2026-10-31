# Response to the owner-context follow-up review — 31 October 2026

Review: [AHAH_owner_context_followup_review_2026-10-31.md](AHAH_owner_context_followup_review_2026-10-31.md).
The finding reproduced: a forked child inherited the owner's lock descriptor, so it kept the lock
alive after the owner was killed, and leaving the inherited `owned` block in the child raised
`KeyError` on the record the fork callback had cleared.

## The finding: closed

- The fork callback (`_forget_inherited_ownership` in `ahah_ingest/pipeline.py`) now closes every
  inherited lock descriptor before clearing the records. Closing the child's copy releases nothing
  while the parent keeps its own, which is why it was left alone before; what was missed is that
  once the parent dies, the child's copy was the only thing keeping the lock alive.
- An inherited context unwinding in a child checks that the current process is the owner recorded
  in its key before deleting the record, unlocking or closing. The reentrant branch checks that its
  record still exists. A child that leaves the block normally does nothing.

Regression `test_a_forked_child_neither_keeps_a_dead_owners_lock_nor_fails_leaving_the_inherited_block`:
a fresh interpreter takes ownership, forks, the child leaves the inherited block (asserted clean)
and outlives its parent; the test is refused while the owner lives, kills the owner with SIGKILL,
confirms the child is still alive, and then takes ownership. With the previous callback the test
fails at that last step with `ResultsBusy`, as the review described; with the fix it passes.

## What the test does not cover

- A fork taken by a non-owning thread while another thread owns: the callback closes the
  descriptors in that case too, but the test forks from the owning thread.
- Windows (no `fork`) and shared filesystems across hosts, as before.
- A child that forks again: the grandchild runs the same callback; not exercised.

## Validation

| Check | Result |
| --- | --- |
| `python3 -m pytest tests/` | 80 passed, no warnings |
| New regression against the previous callback | Fails with `ResultsBusy` after the owner's death, as the review reproduced |
| `docs/reviews/probes/promotion_kill_probe.py` | PROBE PASSED |
| `python3 -m ahah_ingest.pipeline --verify` | results complete, 35,296 rows |

Outputs unchanged; no rebuild.
