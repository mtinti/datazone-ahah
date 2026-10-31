# Response to the provenance site implementation review of 31 October 2026

Review: [AHAH_provenance_site_implementation_review_2026-10-31.md](AHAH_provenance_site_implementation_review_2026-10-31.md).
Every finding was reproduced before it was fixed; the regression tests named below are in
`tests/test_provenance.py` (69 tests in the suite, all passing; `mkdocs build --strict` passes).

| # | Finding | Reproduced | Fix | Test |
| --- | --- | --- | --- | --- |
| 1 | P1: Pages not enabled; the publish step polls 404 for ten minutes | yes: `has_pages: false`, run 41180010715 failed after the wait | `pages_publish.sh` now checks `GET /repos/.../pages` before requesting a build and fails at once with the enabling command when Pages is not configured or serves another branch. Enabling Pages is a repository setting the automation is not permitted to change; it is Michele's step (Settings, Pages, branch `gh-pages`, folder `/`), after which a re-run publishes | `bash -n`; the message is exercised by the next run until Pages is enabled |
| 2 | P2: absent editions cite no presence check | yes: `off_licence` cited `v1` and `v2` only; an injected `v3.presence_matrix` failure was invisible on its page | the lineage cites `v<ed>.presence_matrix` for every edition, including those where the column must be NULL, with no other check of that edition | `test_absent_editions_cite_the_presence_check_that_makes_the_column_null`; the injected failure now shows `v3.presence_matrix: FAIL` on `off_licence` in `test_a_clean_build_shows_results_and_a_failure_is_shown_as_such` |
| 3 | P2: the edition page dropped corrections and later qualifications | yes: the v5.1 page defined `lsoa21cd` by the uncorrected quotation | `_edition_definition` renders every entry that applies to the edition: quotation marked and attributed, then its correction, then our qualifications | `test_the_edition_page_keeps_the_quotation_with_its_correction` |
| 4 | P2: edition-1 definitions wrong against the paper | yes, read from the pinned PDF: page 3 selects A&E hospitals only; page 4 defines green space per postcode within the 900 m buffer; pages 3 to 5 define a physical environment domain of green space plus NO2, PM10 and SO2 | `hospital` edition 1 says A&E hospitals; editions 3 and 4 say the selection is unconfirmed rather than "5.1 only"; `greenspace` edition 1 is per postcode; `domain_e_exp` and `domain_e_dec` edition 1 are the physical environment domain with green space, edition 2 unconfirmed, and `domain_e` from edition 3 is air quality; the plan's section 3 and test list, the data dictionary's version 5.1 note, and the routed-distance wording (postcode centroid, averaged) were corrected together | `test_edition_1_definitions_follow_the_paper` |
| 5 | P2: check explanations overstate the checks | yes: a two-row CSV with header `gp,lsoa11` and an empty English cell passes `header_is_mapped` and `no_empty_cells` | `header_is_mapped` is described as a set comparison with order not checked; `no_empty_cells` as Scottish rows only; the readback checks are described and cited one by one (column names, types, nullability, rows, key, cells; CSV header, rows, cells) | `test_check_descriptions_state_the_real_scope` runs that CSV through `read_edition`; `test_readback_checks_are_cited_one_by_one` |
| 6 | P2: changed configuration shown on the home page only | yes: a changed `registry_sha256` was named on the home page and not on `columns/GP` | every column page that shows results ends its check table with "Changed since that build" naming the files | `test_a_changed_configuration_is_shown_on_the_column_page_with_the_results` |
| P3 | no conventions page; `docs/PERCENTILES.md` as plain text | yes | `conventions.md` is generated from `docs/PERCENTILES.md` with the rank convention and decision links, in the navigation; every mention of the document on a column page is a link | `test_the_conventions_page_exists_and_is_linked_from_percentile_pages` |
| P3 | "1 (or 0) is the healthiest" on domain and index percentiles | yes | the lowest value is stated per scale: 0 for indicator percentiles, 1 for domain and index percentiles | in `test_edition_1_definitions_follow_the_paper` |

The manifest was not rebuilt: nothing in the pipeline changed, so the site cites build `c31db5a`
with no configuration difference. The number of distinct cited checks rose from 319 to 326 (the
readback checks now cited one by one).

My findings on the review are closed. One item stays open and is not mine to close: enabling
GitHub Pages on the repository.
