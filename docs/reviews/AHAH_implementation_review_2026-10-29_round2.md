# AHAH implementation review, round 2

Date: 29 October 2026. Reviewer: Codex.

Scope: changes since the [first implementation review](AHAH_implementation_review_2026-10-29.md),
checked against its [response](AHAH_implementation_review_2026-10-29_response.md).
Reviewed the changed loader, SQL generator and generated check, v2 validation,
schema description, generated dictionary and regression tests. Earlier reviews
are preserved. No implementation files or supplied outputs were edited.

**All five previous findings are resolved. No new P1 or P2 findings in these changes.**
The documented loading workflow now passes a real SQL Server run through the
loader itself, including schema-qualified names and propagation of a failed check.

| Previous finding | Resolution and verification |
| --- | --- |
| P1: loader crashes with its default settings | `local/load_ahah_to_sqlserver.py:141` now iterates a one-element sequence of pairs. The new tests call the real loader functions. A configured copy of the actual loader completed hash verification, decompression, import and all five SQL checks with `MAIN_TABLE = "ahah_datazone"`. `--print-sql` also exited successfully and wrote both scripts. |
| P2: schema-qualified names corrupt a SQL variable | `ahah_ingest/sql_check.py:79` now uses the fixed variable `@declared`, which table-name replacement does not touch. Full loader runs for `dbo.ahah_datazone` and `geo.ahah_v1` each imported 35,296 rows and passed all five checks. |
| P2: another schema's columns can satisfy the structure check | Both metadata queries now use `sys.columns` bound to the target's `OBJECT_ID`. With an empty `shadow.ahah_datazone` present, changing `dbo.ahah_datazone.GP` to `NOT NULL` produced one structural difference. The real loader's `--check-only` exited 1 after SQL Server threw. Restoring target nullability restored the pass, even after adding an unrelated extra column to the shadow table. This verifies that both metadata queries stay within the target object. |
| P2: v2 non-routed deciles accept `-1` | `ahah_ingest/checks.py:61` restricts the exception to routed deciles. Lines 87–93 additionally reject the sentinel in non-routed indicators and deciles. The new regression test exercises all five affected deciles and two raw indicators in both an ordinary zone and an allowed no-route zone; each invalid case fails. The published v2 frame still passes. |
| P2: the overall index definition is wrong | `ahah_ingest/columns.py:111` now describes the mean of exponentially transformed domain ranks and distinguishes the later published probit domain intermediates. The generated schema and dictionary carry the corrected wording. This agrees with the publisher-code evidence recorded in the previous review. |

Verification completed:

- **37 tests passed** with `python -m pytest -q -p no:cacheprovider`, using Python
  3.12.11 and the pinned dependencies. This includes the five loader test cases
  and the additional v2 sentinel regression test.
- A fresh build in a temporary directory produced **35,296 rows, 90 columns and
  341 passing blocking checks**, with no failures. The extra check is
  `v2.no_route_code_outside_routed`.
- The rebuilt CSV and Parquet match the supplied files and the previous reviewed
  files byte for byte. CSV digest remains `1313739416145945439820`. The updated
  schema SHA256 is recorded correctly in the manifest.
- Both generated SQL scripts and the data dictionary match regeneration. The
  loader's embedded compressed and uncompressed CSV hashes and digest match the
  rebuilt manifest.
- Ran the actual standalone loader in an isolated SQL Server 2022 Developer
  container, server version `16.0.4305.5`, using its `sqlcmd` fallback. Each copy
  changed only its EDIT-block configuration for the local test database, directory
  and table name. Exercised normal loading for `ahah_datazone`,
  `dbo.ahah_datazone` and `geo.ahah_v1`, successful `--print-sql`, and both passing
  and failing `--check-only` runs.
- Repeated the cross-schema reproduction from the first review and confirmed
  rejection of wrong target nullability, followed by successful validation after
  restoration. A different schema's extra column no longer affects the target check.
- Confirmed that the reader, pipeline, mapping, source registry, export contract,
  output writers, decision log, README join and shell probe are unchanged. The
  previous independent comparison of 1,860,064 source cells and 1,245,984 expected
  NULL cells was not repeated: the same output hashes preserve that evidence.

The SQL tests used Linux, Python 3.10.12 inside the container and SQL authentication
through `sqlcmd`; `pyodbc` was not installed there. Windows integrated
authentication, server-visible Windows paths and the `pyodbc` branch remain
untested. The unchanged shell probe still prints its join results rather than
asserting them; the previous review's separate assertion-based join test remains
the evidence for the unchanged query. These limits do not leave any of the five
review findings open.

SHA256 values identifying the principal changed files reviewed:

| File | SHA256 |
| --- | --- |
| `local/load_ahah_to_sqlserver.py` | `3c97cf30ff7b3a968ba4f45a56ca9642085d4d07068f4f048a2e3f7291e07098` |
| `ahah_ingest/sql_check.py` | `25e854eef674511ff4df8ef13e697082136c77b70d3cec549e45c7f6c1fdbe0e` |
| `ahah_ingest/checks.py` | `f3cabbeeb9d17c813535681bce61a3f4b2c98b9169f450de182904ff64969364` |
| `ahah_ingest/columns.py` | `6df2b0c3d7f08a23980f01944394a45a64e99d11d20308a142e4e7d2a85fb1d7` |
| `ahah_ingest/output_schema.yaml` | `0636a35a674170123e652f564c66887241fbd6bfc01425440949cde4af6964d5` |
| `docs/sql/check_loaded_digest.sql` | `2cc3fd55532e280ea1e261a92bbdebba10f2600f26b932f632e54ed1c141d205` |
| `tests/test_loader.py` | `69e436025c4c09bd7e42fc0519961a3fa69cca0aea7a6dd6c7259ff9b954b7c1` |
| `tests/test_build_rules.py` | `a12999687c9c4e18742b02e810a1176abc18fd1c635cfc819492c2f54a33122b` |
