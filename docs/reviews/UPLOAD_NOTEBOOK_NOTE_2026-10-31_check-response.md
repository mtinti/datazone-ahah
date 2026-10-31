# Response to the check of the upload notebook note, 31 October 2026

Check: `UPLOAD_NOTEBOOK_NOTE_2026-10-31_check.md`. Items 2 to 8 are accepted as found; the
alternatives chosen are sound. Item 1's verdict, "premise does not hold as stated", was probed
rather than argued, and the premise holds, though the note's wording of the mechanism was wrong.

## Item 1: the with-block does not protect

The check reasons that every connection is a `with` block, pyodbc commits on exit, so no
transaction is left open for the pool to hand on. The uprn-epc notebook that hung used `with`
blocks in the same way (its step 1 was `with pyodbc.connect(CONN, timeout=10) as cn:`), so the
reasoning was tested in uprn-epc's client container against its SQL Server container
(`uprn-epc/loader/notebook_probe/pooling_diag.py`, 31 October 2026):

- A: `with pyodbc.connect(CONN)` (autocommit False), one SELECT, block exits (pyodbc commits),
  connection deleted (pyodbc rolls back). Then C: `pyodbc.connect(CONN, autocommit=True)`.
- Pooling on: C is handed A's session (same spid). After a SELECT and after a CREATE TABLE,
  `@@TRANCOUNT` on C is 1 while `c.autocommit` reads True, and a third session sees one open
  transaction on C's session.
- Pooling off: `@@TRANCOUNT` on C is 0 and no transaction is open.

So what the pool hands on is not an uncommitted transaction; A's commit and rollback did happen.
It is the physical connection in manual-commit mode at the server, which pyodbc's new handle does
not reset while recording `autocommit=True`. Every statement C runs opens a transaction that
nothing commits, which is what held the schema locks in the EPC run. The with-block is beside
the point; `pyodbc.pooling = False` before the first connect is the fix that matters, and it is
in. The note's sentence "a pooled connection can carry an open transaction" is corrected to
"a pooled connection comes back in manual-commit mode whatever the new handle declares".

## Item 2

Agreed: with every byte of the released CSV below 128, the `csv.ascii` build check makes the code
page irrelevant for this table and fails the build the day that changes, which is better than a
clause the Linux probe cannot run. uprn-epc needs the clause because its data carry non-ASCII;
its Linux probe converts the file to UTF-16LE and loads with `DATAFILETYPE = 'widechar'`.

## Item 5

Agreed: "silently" overstated it. An empty result fails the diff, and an empty `grep -v` aborts
the runner. What was live is narrower: a partial result that still diffs equal, which the diff
excludes, and the status of `sqlcmd` itself, which `pipefail` now carries. Hygiene, now done.

## Not covered

The probe ran on Linux containers with ODBC Driver 18; the Windows driver on the HIC server was
not tested, and pooling there is the Windows driver manager's. My findings are closed.
