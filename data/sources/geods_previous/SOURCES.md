# AHAH versions 1 to 4, downloaded from GeoDS

Downloaded by Michele Tinti on 29 October 2026 from
https://data.geods.ac.uk/dataset/access-to-healthy-assets-hazards-ahah-previous-versions with a
personal GeoDS account. Licence on the record: UK Open Government Licence.

| File | SHA256 | Bytes | What it is |
| --- | --- | --- | --- |
| `ahah_v1_fulldata.csv` | `3eb9345e7e5c6dd2ae20473eb95e7e68d3db62485115bdc1069f352488e454c7` | 10,551,174 | Version 1 (2016): 41,729 areas, 37 columns, deciles only, key `lsoa11` |
| `ahah_v2_fulldata.csv` | `e34c0ca0ee59ef646f47d9be188f3d4b6ca6251055784876bd9b8129f940ae84` | 13,265,937 | Version 2 (2017): 41,729 areas, 49 columns, ranks and deciles, key `lsoa11` |
| `ahah_v3_fulldata.csv` | `38e02a3f88efc4e681777cc090632fb515309a31439d01841655231df83d2d37` | 15,812,346 | Version 3 (2022): 41,729 areas, 58 columns, ranks and percentiles, key `lsoa11` |
| `ahah_v4.csv` | `55fefee78a13bd69f4ecb3c17818206d723b862cacd0ab3e0dae8153171a7a4e` | 13,318,377 | Version 4 (2024): 42,648 areas, 58 columns prefixed `ah4`, key `LSOA21CD` |
| `data_summary_ahah_v1_fulldata.csv` | `557cca989be8b848bf133b8e441f0b6bf6be875108dda71d768e547b27931a36` | 3,539 | Column summary, version 1 |
| `data_summary_ahah_v2_fulldata.csv` | `d465566575a372a7fe86ff76691c7a7118267d7f5a372c51772fe6f23d189d7c` | 4,589 | Column summary, version 2 |
| `data_summary_ahah_v3_fulldata.csv` | `e8b0b5e104ee6b0379086b8bd6d6278650a5798d3c1dd8c5a87440cad6ed6c15` | 5,595 | Column summary, version 3 |
| `summary_ahah_v4.csv` | `21f0affb958eec555365054fa5bf27210b320711690c47f137da435bc53c8b23` | 5,780 | Column summary, version 4 |
| `ahah_datasources.pdf` | `5200e682e11c3ef654db57d25b5f261dee54d91e5db1a1d6ccba3cb2247636f8` | 109,199 | Version 4 data sources table, one page |

Checked on download: every version has 6,976 Scottish codes, none duplicated, all starting `S01`.
Those are the 2011 data zones. Version 4 keys by `LSOA21CD` for England and Wales but still
carries 2011 data zones for Scotland, as the GeoDS page says.

Version 2 publishes `-1` in eleven indicators and their deciles in two rows, the only two in
Great Britain: `S01010206` (Petershill 04) and `S01010226` (Sighthill 02), both Glasgow City,
both with a 2017 population of 0. The eleven are the routed drive-distance indicators; the
raster indicators (green space, air) of the same rows have values. The likely reading, from
the v2 build code (`create_index_version2.R` in GDSL-UL/AHAH, which has no handling for it),
is that these zones had no residential postcode to route from and the input carried `-1` for
"no route", which the script then ranked as a real value. Their v2 domain ranks and index are
therefore not meaningful. No v2 documentation states this. The build keeps the values as
published and the dictionary says all of the above.

Version 2 also carries `ur`, a 0 or 1 flag the v2 build code does not use. 4,687 of the 6,976
Scottish zones have 1. Zones with 1 have a median SIMD 2020 access rank of 4,054 against
1,695 for 0, so 1 is very likely "urban" of a two-fold urban-rural classification. Unconfirmed
by any documentation; the dictionary says "flag, probably urban = 1, not documented". Version 4 ranks the five health indicators with dense ranking, the other
versions and columns with minimum ranking, so a version 4 health rank can be below the number
of areas.

Percentiles since version 3 use two definitions; see `docs/PERCENTILES.md`.
