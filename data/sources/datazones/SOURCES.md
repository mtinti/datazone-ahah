# Scottish data zone reference lists, downloaded from data.gov.scot

Downloaded on 29 October 2026 (by a Claude Code session on Michele Tinti's behalf) from the
Scottish Government's open data site. Licence on each page: UK Open Government Licence v3.0.
Publisher: Scottish Government, contact statistics.opendata@gov.scot. The build reads only the
first column of each file, the data zone code, to check that every zone of a vintage appears
exactly once in every AHAH edition on that vintage.

| File | SHA256 | Bytes | Page | Direct URL |
| --- | --- | --- | --- | --- |
| `DataZone2011_lookup.csv` | `688416b875733f62d5ceede1ac2b73c9db021e816ea8a9c6c58da0f105b601b6` | 3,287,962 | https://data.gov.scot/dataset/2011_data_zone_lookup | https://data.gov.scot/dataset/2011_data_zone_lookup/resource/20ad5f65-c5c2-407e-8355-7c25bf579e87/download |
| `DataZone2022_lookup.csv` | `41f51a4c0e6edbd30f81c3d8d79c37f3f557a3c1d887a10b75c07f0bc01e0891` | 3,333,484 | https://data.gov.scot/dataset/2022_data_zone_lookup | https://data.gov.scot/dataset/2022_data_zone_lookup/resource/81b010f5-0207-4ee5-bd2d-e7821aa6a3dc/download |

Checked on download: 2011 file has 6,976 rows, 6,976 distinct `DZ2011_Code`, S01006506 to
S01013481; 2022 file has 7,392 rows, 7,392 distinct `DZ22_Code`, S01013482 to S01020873. All
codes start `S01` and are nine characters.

Notes:

- The files are **cp1252**, not UTF-8: 80 and 78 non-ASCII bytes, all a non-breaking space
  (0xA0) after some area names such as "Annandale and Eskdale". The build decodes as cp1252.
- The direct URLs answer a GET with a redirect to a short-lived signed S3 URL; a HEAD returns
  404. The lookups are refreshed by the publisher (higher geographies change), so the pin is
  the hash; a refreshed file is a new pin.
- Alternatives checked and not used: the NRS `oa22_dz22_iz22.zip` (7,392 zones, same codes)
  and the spatialdata.gov.scot boundary shapefiles (19 MB and 26 MB).
