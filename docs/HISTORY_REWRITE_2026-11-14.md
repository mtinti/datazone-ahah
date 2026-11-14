# The history rewrite of 14 November 2026

On 14 November 2026 the history of this repository was rewritten, and the repository was created
again on GitHub under the same name. The server name, the database name and the connection options
of one site had been committed in the upload notebook and its generator. Every commit that held them
now holds a placeholder in their place: `<SERVER>`, `<DATABASE>` and `<CONNECTION OPTIONS>`. No
other file and no other line changed, and no commit was added, removed or reordered.

## What this changes for a reader

- **Commit hashes.** Every commit from the one that added the notebook onward has a new hash,
  and so do the tags `v0.1.0` and `v0.2.0`. Documents, reviews, build reports and commit messages
  written before 14 November 2026 cite the old hashes. The table below gives the new one for each.
- **Old notebooks.** The notebook of a commit before version 0.2.1 holds the placeholders and does
  not connect as committed. From version 0.2.1 the notebook is committed with an empty connection
  string, which the analyst fills in at step 1 (`README.md`).
- **The code archives on Zenodo.** The archives of versions 0.1.0 and 0.2.0 were withdrawn the
  same day. Their DOIs, and the DOI that stood for every release, 10.5281/zenodo.23783415, now lead to
  a notice. The code is archived again from version 0.2.1: 10.5281/zenodo.24226615 for every release,
  10.5281/zenodo.24226616 for 0.2.1.
- **Nothing else.** The source pins, the built table, its hashes and its digest are the same.

## Old and new hashes of the commits on `main`

Newest first, up to the last commit before the rewrite. A row whose two hashes are equal was not
touched. Later commits, from version 0.2.1, have only ever had one hash.

| Before | Now | Date | Commit |
| --- | --- | --- | --- |
| `85c9241` | `fa3e758` | 2026-10-31 | A forked child closes its inherited lock descriptors and never unwinds the owner's record (review of 31 October, owner-context follow-up) |
| `028e78d` | `26f74f4` | 2026-10-31 | Fork regression runs in a fresh interpreter: forking the threaded test process is deprecated |
| `15f58bd` | `49fbb6f` | 2026-10-31 | Ownership is reentrant for the owning thread only; malformed commands are a usage error, not a build (review of 31 October, findings 1 and 2) |
| `1370934` | `70beb08` | 2026-10-31 | One owner of results/ at a time: build, recovery and verification take an OS lock (review of 31 October, findings 1 and 2) |
| `7b10be7` | `b37ad2f` | 2026-10-31 | v0.2.0: Version 0.2.0; notebook generator runs as a script again |
| `05a8e2b` | `26001aa` | 2026-10-31 | Rebuild on bcf48da through the journaled promotion: 342 checks, CSV hash unchanged |
| `1b6263b` | `bcf48da` | 2026-10-31 | Journaled forward-only promotion with recovery; every consumer verifies results/ (review of 31 October, findings 1 to 3) |
| `521f2e4` | `b9d4dba` | 2026-10-31 | Rebuild on 9f0cb8e through the staged path: 342 checks, csv.ascii recorded, CSV hash unchanged; docs updated |
| `072fdfd` | `9f0cb8e` | 2026-10-31 | Loader and build hardening after the upload notebook note: no pooling and autocommit on read-only cells, lock timeouts, probe runner with pipefail and asserted captures, csv.ascii check, staged build promoted as one generation |
| `e7baaca` | `eeda080` | 2026-10-31 | Upload notebook note and its check |
| `1c0240e` | `d234d39` | 2026-10-31 | Provenance site: fixes after implementation review (presence checks for absent editions, corrections on edition pages, edition-1 definitions per the paper, check scopes, changed-configuration notice, conventions page, Pages preflight) |
| `d735009` | `895eebc` | 2026-10-31 | pyproject: name the package so the editable install works in CI |
| `43aedcd` | `b7a3d3f` | 2026-10-31 | Rebuild on f150e0f: manifest records the build identity (clean tree); CSV hash unchanged |
| `c31db5a` | `f150e0f` | 2026-10-31 | Column provenance site: lineage, edition-scoped descriptions, document registry, generator, Pages workflow, build identity |
| `69d05eb` | `a41334c` | 2026-10-31 | Provenance site plan: cite range checks only where the build emits them (review round 2) |
| `40cb69a` | `4183c6c` | 2026-10-31 | Provenance site plan: revise after review (build identity, edition-scoped descriptions, document registry, presence check) |
| `9bb0402` | `83c2bdf` | 2026-10-31 | Plan: column provenance site on GitHub Pages |
| `f25d46c` | `f08dc15` | 2026-10-29 | README: title, DOI and CI badges |
| `36dd4f9` | `f2b6cb7` | 2026-10-29 | Software DOI 10.5281/zenodo.23783415 in README and CITATION.cff; Zenodo title names the repository |
| `407df8e` | `1058528` | 2026-10-29 | v0.1.0: Zenodo record of the pinned sources: 10.5281/zenodo.23783247 |
| `209004a` | `0f3c250` | 2026-10-29 | Name the repository datazone-ahah |
| `15312de` | `c8c8f87` | 2026-10-29 | Tests: notebook guard tests run from a source-only checkout |
| `48643ef` | `c0577cc` | 2026-10-29 | Notebook: fail before dropping, drop and create in one transaction; comparison reports repeated keys |
| `2d22338` | `ff708b9` | 2026-10-29 | Compare every loaded cell with the original GeoDS files, independently of the build |
| `49f4c91` | `3bfb3db` | 2026-10-29 | Upload notebook: load the CSV through pyodbc from a client machine, then the digest check |
| `14131d7` | `14131d7` | 2026-10-29 | AHAH for SQL Server: pinned sources, one table of every edition, digest-checked load |
