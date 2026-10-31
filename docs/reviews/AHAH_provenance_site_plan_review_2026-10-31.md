# AHAH provenance site plan review

Date: 31 October 2026. Reviewer: Codex.

Scope: [AHAH_Provenance_Site_Plan.md](../AHAH_Provenance_Site_Plan.md), checked against the
current AHAH schemas, mappings, readers, checks, manifest, source records and dictionary, and
the existing SIMD publishing workflow. Supporting files are evidence, not additional review
targets. The plan and implementation were not edited.

Reviewed commit: `9bb04021877e4aba25c984589f6703b5c796344d`.
Plan SHA256: `35c2cd348ec9b6cd125a60c46b2e088e3c55f90c70647e0fe745da38dbc42b3f`.

The design can reuse the existing mapping and export contract, but needs the following five
P2 corrections before implementation. No P1 finding.

## Findings

### 1. P2 — Correct the blue/green-space edition expectations

Location: plan lines 92–94.

The proposed hand-stated test says `bluespace` and `greenspace_active` have inputs for 5.1
only. That contradicts the presence matrix, generated schema, mapping and pinned CSV headers:

| Column | Editions with an input | Source fields, in edition order |
| --- | --- | --- |
| `bluespace` | 2, 3, 4, 5.1 | `blue`, `blue`, `ah4blue`, `bluespace` |
| `greenspace_active` | 2, 5.1 | `gact`, `greenspace_active` |

Implementing the stated expectation would reject correct lineage or omit real earlier-edition
inputs from the site. Update the test requirements to these sets. Keep separate expectations
for rank, percentile and decile variants, whose presence also depends on the edition's column
group. Evidence: [columns.py](../../ahah_ingest/columns.py), lines 40–59 and 69–84, and
[mapping.yaml](../../ahah_ingest/mapping.yaml); the source headers were independently checked.

### 2. P2 — Define a real build identity before displaying pass evidence

Location: plan lines 71–78.

The recommendation binds “passed in build `<commit>`” to the manifest's build commit, but
[manifest.json](../../results/manifest.json) has no build commit, package version or release
identifier. [pipeline.py](../../ahah_ingest/pipeline.py), lines 79–90, does not record these.
Its timestamp and artifact/configuration hashes identify recorded outputs and inputs; they do
not establish which code revision ran the checks. A commit that merely contains the manifest
is not necessarily the commit that built the data.

There is already a case requiring an explicit compatibility policy: the manifest's
`registry_sha256` is `6b23d95ab11e9ceb27859f4310d6f44f1a61ea3ae5046b08c85d90ef78d446aa`,
whereas current `sources.yaml` hashes to
`42e9f0bb34ded1012067f0d0579da610d3c9e9f963c0ea98eef173d4e335aaba`. The subsequent change
adds Zenodo metadata; this is not evidence of changed source data or failed checks. It does
show why the site must distinguish current documentation from historical build evidence.

Add an explicit task to record the actual build revision and relevant version information
when the pipeline runs, including how an uncommitted build is represented. For existing
manifests, show the recorded timestamp/artifact identity with the code revision marked unknown,
or show check definitions only. Test missing identity and changed configuration: neither may
silently acquire the site's current commit or an unqualified current-build pass label.

### 3. P2 — Scope description text and attribution by edition

Location: plan lines 38–42 and 59–62.

One text/source entry per column, preferring the v5 dictionary wherever it defines the
variable, is insufficient for columns whose definitions change. The existing
[dictionary.py](../../ahah_ingest/dictionary.py), lines 19–24, already distinguishes v1
accessibility distances in kilometres from later drive times in minutes, v1 green-space area
from later NDVI, and the v5.1 hospital-with-A&E definition. It also preserves uncertainty about
v2 units. A shared v5 description would misdescribe earlier inputs even if their field names
and hashes were correct.

Allow edition-specific text, units, references and qualifications within each column entry,
and render those distinctions on the column page. Distinguish quotations from project-authored
explanations. Include reviewed corrections where a publisher definition is misleading: the
v5 dictionary labels the code “(2011)”, while the existing source record documents 2022
Scottish zones. Test at least `GP`, `greenspace`, `hospital` and `datazone_code`, including
preservation of the unconfirmed v2 wording. Generic suffix descriptions can still be shared
when their meaning is identical.

### 4. P2 — Add resolvable document references and an authored-description exception

Location: plan lines 59–62 and 86–87.

The proposed test requires every description source to name a pinned file in the registry.
The registry currently consumed by [load_registry](../../ahah_ingest/core/sources.py) contains
five edition CSVs, five summaries and two geography lists. It has no entries for the v5
dictionary, methodology PDF or 2019 paper. The first two do have hashes in the committed
[GeoDS SOURCES.md](../../data/sources/geods/SOURCES.md); the paper is committed under
`docs/references/`, but none is a document reference exposed by the current registry API.
Furthermore, descriptions explicitly marked “ours” cannot satisfy the universal external-file
requirement.

Specify how the site resolves documentation references: extend the machine-readable registry,
or add a documentation registry/adapter that uses the existing recorded pins and identifies
the committed paper. Record a stable reference, hash, attribution and location within the
document. Give project-authored descriptions their own reference kind, with a repository or
decision reference where appropriate, and exempt them from the external-file rule. These
checks should work from committed metadata without requiring the ignored downloads in Pages
CI. Otherwise the new coverage test either fails on the intended descriptions or must be
weakened enough to lose the attribution guarantee.

### 5. P2 — Cite the presence checks the build actually emits

Location: plan line 21; related lineage and validation requirements at lines 51–55 and 90–91.

The build does not emit `v<ed>.<column>.absent` or `.present`. It checks all 90 columns together
and emits `v<ed>.presence_matrix`: five such records occur in the committed manifest, with
zero per-column `.absent`/`.present` records. Evidence:
[checks.py](../../ahah_ingest/checks.py), lines 40–47, and the manifest's complete check-name set.

Map each column's presence guarantee to the edition-wide check and explain its scope. Reserve
per-column check names for checks that actually exist, such as applicable `.range` checks.
Require exact cited-name membership in the manifest, together with expectations that each
column includes the checks relevant to it; matching a naming pattern alone cannot establish
that the claimed check ran. This avoids broken references or invented per-column pass evidence.

## Smaller planning correction

The phase-2 statistics proposal at lines 81–82 assumes per-column null counts and observed
min/max values are available in the manifest. Currently `observations` contains only
`rows_per_version`; range-check bounds are not observed minima/maxima. Add generating those
statistics to phase 2's prerequisites if that feature is retained.

## Verification and limits

- Read the complete proposed plan and the relevant AHAH implementation and metadata. Compared
  its publishing proposal with the local SIMD `pages.yml`, `pages_publish.sh` and `mkdocs.yml`.
- Ran `python -m pytest tests/test_build_rules.py -q -rs` using the installed Miniforge Python
  environment: **10 passed in 5.87 seconds**, including the generated schema/mapping and
  edition-rule tests. The default shell Python lacked pytest and PyYAML, so the initial probes
  were rerun in that environment.
- Independently compared all five pinned CSV headers with the mappings and inspected the
  blue/green-space inputs. All mapped headers matched their source files.
- Inspected all 341 committed check names and compared the five recorded configuration
  hashes with current files. Schema, mapping, export contract and decision hashes match;
  the registry difference is described above. This inspected historical evidence; it did not
  rerun the complete data build.
- The provenance generator, description file, site tests and AHAH Pages workflow are proposed
  files, so no generated-site build, link test or deployment was run. No publishing action was
  taken. The original notebook/SQL implementation was outside this review's scope.
