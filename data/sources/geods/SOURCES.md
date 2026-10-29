# AHAH version 5.1 sources, downloaded from GeoDS

Downloaded by Michele Tinti on 29 October 2026 from
https://data.geods.ac.uk/dataset/access-to-healthy-assets-hazards-ahah with a personal GeoDS
account. Licence on the record: UK Open Government Licence v3.0, access tier "Open". No further terms
were shown at registration or download (Michele Tinti, 29 October 2026). Attribution asked for:
Daras K, Green MA, Davies A, Barr B, Singleton A (2019) Scientific Data 6, 107,
doi:10.1038/s41597-019-0114-6, and "data provided by the Geographic Data Service, a Smart Data
Research UK investment, ES/Z504464/1".

| File | SHA256 | Bytes | What it is |
| --- | --- | --- | --- |
| `ahah_v5_1.csv` | `3067fef8ca5f718220359fc60af817fb557ecf7f798c095142d8d7f6f5f22c22` | 23,768,558 | The index: 43,064 areas, 61 columns. 7,392 rows are Scottish 2022 data zones |
| `dictionary_ahah_v5.csv` | `94ae1ca291a95146ffaf2840a2aa8030f8844cb9e56d31cf1ba8c3300035e118` | 1,130 | Variable dictionary, 23 rows |
| `data_summary_ahah_v5_4.csv` | `f3da90c6ce5dc75a7f39bc0071646e773921445000ab790cb5192bfa0328e738` | 6,515 | Per-column summary: counts, nulls, min, max, mean |
| `ahah_v5_technical_methodology.pdf` | `8a23d522a8b1d0f64426251c54f314eb57871c3621ebc27cbbbce25fb3a999cb` | 105,278 | Technical methodology report, 9 pages |
| `ahah-2026-web-new.pdf` | `d8b43b351e6d7252112fd10bdb4841ae56005dbe9859b17b6d9e956fbcd0701b` | 1,071,053 | Two-page leaflet |
| `ahah_v5_geo_1.parquet` | `d1e7b36e85c67fdae88b69355c5a2e9480379393a12908c672324d748bb05e5c` | 85,871,425 | The same with boundaries. Not read by the build |

Checked on download: 7,392 Scottish codes, none duplicated, every one starting `S01`. The header
names the code column `lsoa21cd` for Scotland too, and the dictionary calls it "(2011)"; the
methodology report, section 2.2, says 2022 data zones, and the count 7,392 agrees.
