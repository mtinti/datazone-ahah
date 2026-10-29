# AHAH briefing for the HEAL-Scot meeting, 29 October 2026

Own notes. Sources: GeoDS dataset page (read 29 October 2026), the version 1 paper (Scientific Data,
2019), the version 2 build code on GitHub, the HIC data request v1.0 and the DataLoch data selection
form. The version 5.1 methodology report has not been read: GeoDS was unreachable this afternoon.

## What AHAH is

- Access to Healthy Assets and Hazards. Published by the Geographic Data Science Lab, University of
  Liverpool, hosted by the Geographic Data Service. Open Government Licence, but every download
  needs a GeoDS login.
- One row per small area of Great Britain: LSOA in England and Wales, data zone in Scotland. No
  postcode product, no person-level data.
- Four domains, fifteen indicators. Retail: fast food, pubs, tobacconists, gambling, off-licences.
  Health services: GP, hospital, pharmacy, dentist, leisure centre. Physical environment: blue
  space, active and passive green space (satellite vegetation index). Air: NO2, PM10, SO2.
- Each indicator is a travel time, a vegetation index or a pollutant concentration. Accessibility
  is measured from every residential postcode and averaged into the area. Indicators are
  rank-normalised, averaged into domain scores, the domains are ranked, transformed, and averaged
  with equal weight into the overall index. Lower is healthier.
- Each indicator, each domain and the index carry a score, a rank and a percentile (and in later
  versions deciles). Ranks are over all of Great Britain, about 42,000 areas, not over Scotland.

## Editions

| Version | Date | Scottish geography |
| --- | --- | --- |
| 1 | 2016 | 2011 data zones, original method, not comparable with later |
| 2 | 2017 | 2011 data zones, revised method kept since |
| 3 | 2022 | 2011 data zones |
| 4 | late 2024 | 2011 data zones |
| 5 | February 2026 | 2022 data zones, first on them |
| 5.1 | May 2026 | 2022 data zones, hospital definition refined |

Editions are snapshots. There is no PHS-style guidance on which edition fits which year.
Editions are not comparable as a time series: inputs and method changed between them.

## Where HEAL-Scot stands

- HIC data request v1.0 (May 2026): AHAH version 4, pseudo data-zone IDs built on 2011 data zones.
- DataLoch data selection form: AHAH version 5.1, 2022 data zones, variables "HEAL-Scot data team
  to decide", provided by the project as a public download.
- These are incompatible. Version 4 lives on 2011 zones, 5.1 on 2022 zones, and the two zone sets
  cannot be converted: 2022 zones split, merge and redraw 2011 ones. 6,976 zones against 7,392.
- SIMD 2020v2 must stay on 2011 zones. So if AHAH 5.1 is chosen, every site needs two pseudo
  data-zone mappings, 2011 for SIMD and 2022 for AHAH, both from the same patient address.
- No postcode is released and no data zone is released, so AHAH joins on the pseudo data-zone ID
  at the data zone level only. That is simple once the vintage is settled.

## Decisions to get from the meeting

1. Version: 4, 5.1 or both. Recommendation: 5.1 for current conditions, unless the analysis year
   sits before 2024, in which case 4. Both is cheap to carry, each on its own vintage.
2. Vintage of the pseudo data-zone mapping: 2011 only (data request), or 2011 and 2022. 5.1
   forces 2022.
3. Which variables: overall index only, the four domains, or all fifteen indicators. And which form:
   score, GB rank, GB percentile, decile.
4. Who downloads from GeoDS, with which login, and whether the files may be archived on Zenodo for
   reproducibility. The licence is OGL but the login page may add terms.
5. Whether DataLoch and HIC take the same file and the same version, so both sites' releases match.

## Implications to raise

- Disclosure. AHAH values and ranks are public per data zone. A released score or GB rank
  identifies the zone exactly, which defeats the pseudo ID. Percentiles or deciles reduce this but
  with fifteen indicators the combination will still be unique for most zones. For SIMD 2020v2 the
  seven domain quintiles alone single out 1,923 of 6,976 zones. Fewer, coarser AHAH variables, or
  the overall decile only, is the safe default. Run the uniqueness count before extraction.
- Scotland position. GB ranks say where a zone sits in Britain, not in Scotland. A within-Scotland
  rank or decile would be our derivation, documented as such. Decide whether anyone wants it.
- Rurality interaction. Access domains are travel times, so rural zones score badly on health
  services and well on green space by construction. Results split by urban-rural will show this.
- Address periods. DataLoch links SIMD per address period. AHAH would follow the same periods, on
  the 2022 zone of the postcode at that period. Postcodes retired before 2022 have no 2022 zone.
- Build. The table is small: 7,392 rows per edition. The build copies the postcode-simd pattern:
  pinned source hashes, checks, CSV plus manifest, generated SQL Server import and check scripts.
  Nothing is built yet. First step after the meeting is the download and reading the variable
  dictionary; the rest is two or three sessions.

## Things I could not confirm today

- The 5.1 column names, whether deciles are published, and whether 5.1 recomputed everything or
  only the hospital indicator.
- Whether GeoDS download terms allow redistribution.
- The exact Scottish row count in the 5.1 file.
