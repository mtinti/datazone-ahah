# Build report: ahah_datazone, 2026-10-29T20:51:39Z

Schema `ahah_datazone_v1`. 35,296 rows by 90 columns.
CSV `ahah_datazone.csv.gz` SHA256 `505e71b6dc6dc02e37307e509b2ebea8538adc4f6d1d947f84b0bf6f76e74574`, digest total `1313739416145945439820`.

## Rows per edition

| Edition | Vintage | Rows |
| --- | --- | --- |
| 1 | 2011 | 6,976 |
| 2 | 2011 | 6,976 |
| 3 | 2011 | 6,976 |
| 4 | 2011 | 6,976 |
| 5.1 | 2022 | 7,392 |

## Checks

341 passed, 0 failed.

| Check | Result | Detail |
| --- | --- | --- |
| `source.geods_previous/ahah_v1_fulldata.csv` | pass | sha256 matches |
| `source.geods_previous/data_summary_ahah_v1_fulldata.csv` | pass | sha256 matches |
| `source.geods_previous/ahah_v2_fulldata.csv` | pass | sha256 matches |
| `source.geods_previous/data_summary_ahah_v2_fulldata.csv` | pass | sha256 matches |
| `source.geods_previous/ahah_v3_fulldata.csv` | pass | sha256 matches |
| `source.geods_previous/data_summary_ahah_v3_fulldata.csv` | pass | sha256 matches |
| `source.geods_previous/ahah_v4.csv` | pass | sha256 matches |
| `source.geods_previous/summary_ahah_v4.csv` | pass | sha256 matches |
| `source.geods/ahah_v5_1.csv` | pass | sha256 matches |
| `source.geods/data_summary_ahah_v5_4.csv` | pass | sha256 matches |
| `source.datazones/DataZone2011_lookup.csv` | pass | sha256 matches |
| `source.datazones/DataZone2022_lookup.csv` | pass | sha256 matches |
| `datazones_2011.count` | pass | 6976 |
| `datazones_2011.distinct` | pass | 6976 |
| `datazones_2022.count` | pass | 7392 |
| `datazones_2022.distinct` | pass | 7392 |
| `v1.header_is_mapped` | pass | 37 columns |
| `v1.header_unique` | pass | 37 |
| `v1.gb_rows` | pass | 41729 rows before the Scottish filter |
| `v1.row_width` | pass | {37} |
| `v1.scottish_codes_distinct` | pass | 6976 |
| `v1.scottish_code_shape` | pass | every code is S01 and six digits |
| `v1.no_empty_cells` | pass | {} |
| `v2.header_is_mapped` | pass | 49 columns |
| `v2.header_unique` | pass | 49 |
| `v2.gb_rows` | pass | 41729 rows before the Scottish filter |
| `v2.row_width` | pass | {49} |
| `v2.scottish_codes_distinct` | pass | 6976 |
| `v2.scottish_code_shape` | pass | every code is S01 and six digits |
| `v2.no_empty_cells` | pass | {} |
| `v3.header_is_mapped` | pass | 58 columns |
| `v3.header_unique` | pass | 58 |
| `v3.gb_rows` | pass | 41729 rows before the Scottish filter |
| `v3.row_width` | pass | {58} |
| `v3.scottish_codes_distinct` | pass | 6976 |
| `v3.scottish_code_shape` | pass | every code is S01 and six digits |
| `v3.no_empty_cells` | pass | {} |
| `v4.header_is_mapped` | pass | 58 columns |
| `v4.header_unique` | pass | 58 |
| `v4.gb_rows` | pass | 42648 rows before the Scottish filter |
| `v4.row_width` | pass | {58} |
| `v4.scottish_codes_distinct` | pass | 6976 |
| `v4.scottish_code_shape` | pass | every code is S01 and six digits |
| `v4.no_empty_cells` | pass | {} |
| `v5.1.header_is_mapped` | pass | 61 columns |
| `v5.1.header_unique` | pass | 61 |
| `v5.1.gb_rows` | pass | 43064 rows before the Scottish filter |
| `v5.1.row_width` | pass | {61} |
| `v5.1.scottish_codes_distinct` | pass | 7392 |
| `v5.1.scottish_code_shape` | pass | every code is S01 and six digits |
| `v5.1.no_empty_cells` | pass | {} |
| `table.key_unique` | pass | 0 |
| `table.required_nonnull` | pass | {} |
| `table.columns` | pass | ['ahah_version', 'datazone_vintage', 'datazone_code', 'GP', 'bluespace', 'dentist', 'fast_food', 'gambling', 'greenspace |
| `v1.scottish_rows` | pass | 6976 |
| `v1.every_zone_of_2011_present_once` | pass | 6976 zones of the pinned list, each once |
| `v1.vintage` | pass | {2011} |
| `v1.presence_matrix` | pass | 90 columns, NULL only where the edition has no column |
| `v1.GP.range` | pass | 6976 values in [0, 1E+18] |
| `v1.dentist.range` | pass | 6976 values in [0, 1E+18] |
| `v1.fast_food.range` | pass | 6976 values in [0, 1E+18] |
| `v1.gambling.range` | pass | 6976 values in [0, 1E+18] |
| `v1.hospital.range` | pass | 6976 values in [0, 1E+18] |
| `v1.leisure.range` | pass | 6976 values in [0, 1E+18] |
| `v1.pharmacy.range` | pass | 6976 values in [0, 1E+18] |
| `v1.pub_bar.range` | pass | 6976 values in [0, 1E+18] |
| `v1.tobacco.range` | pass | 6976 values in [0, 1E+18] |
| `v1.NO2.range` | pass | 6976 values in [0, 1E+18] |
| `v1.PM10.range` | pass | 6976 values in [0, 1E+18] |
| `v1.SO2.range` | pass | 6976 values in [0, 1E+18] |
| `v1.greenspace.range` | pass | 6976 values in [0, 1E+18] |
| `v1.off_licence.range` | pass | 6976 values in [0, 1E+18] |
| `v1.GP_dec.range` | pass | 6976 values in [1, 10] |
| `v1.dentist_dec.range` | pass | 6976 values in [1, 10] |
| `v1.fast_food_dec.range` | pass | 6976 values in [1, 10] |
| `v1.gambling_dec.range` | pass | 6976 values in [1, 10] |
| `v1.hospital_dec.range` | pass | 6976 values in [1, 10] |
| `v1.leisure_dec.range` | pass | 6976 values in [1, 10] |
| `v1.pharmacy_dec.range` | pass | 6976 values in [1, 10] |
| `v1.pub_bar_dec.range` | pass | 6976 values in [1, 10] |
| `v1.tobacco_dec.range` | pass | 6976 values in [1, 10] |
| `v1.NO2_dec.range` | pass | 6976 values in [1, 10] |
| `v1.PM10_dec.range` | pass | 6976 values in [1, 10] |
| `v1.SO2_dec.range` | pass | 6976 values in [1, 10] |
| `v1.greenspace_dec.range` | pass | 6976 values in [1, 10] |
| `v1.off_licence_dec.range` | pass | 6976 values in [1, 10] |
| `v1.domain_h_exp.range` | pass | 6976 values in [0, 100] |
| `v1.domain_e_exp.range` | pass | 6976 values in [0, 100] |
| `v1.domain_r_exp.range` | pass | 6976 values in [0, 100] |
| `v1.domain_h_dec.range` | pass | 6976 values in [1, 10] |
| `v1.domain_e_dec.range` | pass | 6976 values in [1, 10] |
| `v1.domain_r_dec.range` | pass | 6976 values in [1, 10] |
| `v1.ahah_dec.range` | pass | 6976 values in [1, 10] |
| `v1.no_minus_one_code` | pass | 0 |
| `v2.scottish_rows` | pass | 6976 |
| `v2.every_zone_of_2011_present_once` | pass | 6976 zones of the pinned list, each once |
| `v2.vintage` | pass | {2011} |
| `v2.presence_matrix` | pass | 90 columns, NULL only where the edition has no column |
| `v2.GP.range` | pass | 6974 values in [0, 1E+18] |
| `v2.bluespace.range` | pass | 6974 values in [0, 1E+18] |
| `v2.dentist.range` | pass | 6974 values in [0, 1E+18] |
| `v2.fast_food.range` | pass | 6974 values in [0, 1E+18] |
| `v2.gambling.range` | pass | 6974 values in [0, 1E+18] |
| `v2.greenspace_active.range` | pass | 6976 values in [0, 1E+18] |
| `v2.hospital.range` | pass | 6974 values in [0, 1E+18] |
| `v2.leisure.range` | pass | 6974 values in [0, 1E+18] |
| `v2.pharmacy.range` | pass | 6974 values in [0, 1E+18] |
| `v2.pub_bar.range` | pass | 6974 values in [0, 1E+18] |
| `v2.tobacco.range` | pass | 6974 values in [0, 1E+18] |
| `v2.NO2.range` | pass | 6976 values in [0, 1E+18] |
| `v2.PM10.range` | pass | 6976 values in [0, 1E+18] |
| `v2.SO2.range` | pass | 6976 values in [0, 1E+18] |
| `v2.greenspace.range` | pass | 6976 values in [0, 1E+18] |
| `v2.off_licence.range` | pass | 6974 values in [0, 1E+18] |
| `v2.ur.range` | pass | 6976 values in [0, 1] |
| `v2.GP_dec.range` | pass | 6974 values in [1, 10] |
| `v2.bluespace_dec.range` | pass | 6974 values in [1, 10] |
| `v2.dentist_dec.range` | pass | 6974 values in [1, 10] |
| `v2.fast_food_dec.range` | pass | 6974 values in [1, 10] |
| `v2.gambling_dec.range` | pass | 6974 values in [1, 10] |
| `v2.greenspace_active_dec.range` | pass | 6976 values in [1, 10] |
| `v2.hospital_dec.range` | pass | 6974 values in [1, 10] |
| `v2.leisure_dec.range` | pass | 6974 values in [1, 10] |
| `v2.pharmacy_dec.range` | pass | 6974 values in [1, 10] |
| `v2.pub_bar_dec.range` | pass | 6974 values in [1, 10] |
| `v2.tobacco_dec.range` | pass | 6974 values in [1, 10] |
| `v2.NO2_dec.range` | pass | 6976 values in [1, 10] |
| `v2.PM10_dec.range` | pass | 6976 values in [1, 10] |
| `v2.SO2_dec.range` | pass | 6976 values in [1, 10] |
| `v2.greenspace_dec.range` | pass | 6976 values in [1, 10] |
| `v2.off_licence_dec.range` | pass | 6974 values in [1, 10] |
| `v2.domain_h_exp.range` | pass | 6976 values in [0, 100] |
| `v2.domain_g_exp.range` | pass | 6976 values in [0, 100] |
| `v2.domain_e_exp.range` | pass | 6976 values in [0, 100] |
| `v2.domain_r_exp.range` | pass | 6976 values in [0, 100] |
| `v2.domain_h_rnk.range` | pass | 6976 values in [1, 41729] |
| `v2.domain_g_rnk.range` | pass | 6976 values in [1, 41729] |
| `v2.domain_e_rnk.range` | pass | 6976 values in [1, 41729] |
| `v2.domain_r_rnk.range` | pass | 6976 values in [1, 41729] |
| `v2.domain_h_dec.range` | pass | 6976 values in [1, 10] |
| `v2.domain_g_dec.range` | pass | 6976 values in [1, 10] |
| `v2.domain_e_dec.range` | pass | 6976 values in [1, 10] |
| `v2.domain_r_dec.range` | pass | 6976 values in [1, 10] |
| `v2.ahah_rnk.range` | pass | 6976 values in [1, 41729] |
| `v2.ahah_dec.range` | pass | 6976 values in [1, 10] |
| `v2.ahah_rnk_unique` | pass | 0 |
| `v2.no_route_code_zones` | pass | {'S01010226', 'S01010206'} |
| `v2.no_route_code_outside_routed` | pass | 0 |
| `v3.scottish_rows` | pass | 6976 |
| `v3.every_zone_of_2011_present_once` | pass | 6976 zones of the pinned list, each once |
| `v3.vintage` | pass | {2011} |
| `v3.presence_matrix` | pass | 90 columns, NULL only where the edition has no column |
| `v3.GP.range` | pass | 6976 values in [0, 1E+18] |
| `v3.bluespace.range` | pass | 6976 values in [0, 1E+18] |
| `v3.dentist.range` | pass | 6976 values in [0, 1E+18] |
| `v3.fast_food.range` | pass | 6976 values in [0, 1E+18] |
| `v3.gambling.range` | pass | 6976 values in [0, 1E+18] |
| `v3.hospital.range` | pass | 6976 values in [0, 1E+18] |
| `v3.leisure.range` | pass | 6976 values in [0, 1E+18] |
| `v3.pharmacy.range` | pass | 6976 values in [0, 1E+18] |
| `v3.pub_bar.range` | pass | 6976 values in [0, 1E+18] |
| `v3.tobacco.range` | pass | 6976 values in [0, 1E+18] |
| `v3.NO2.range` | pass | 6976 values in [0, 1E+18] |
| `v3.PM10.range` | pass | 6976 values in [0, 1E+18] |
| `v3.SO2.range` | pass | 6976 values in [0, 1E+18] |
| `v3.greenspace.range` | pass | 6976 values in [0, 1E+18] |
| `v3.GP_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.bluespace_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.dentist_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.fast_food_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.gambling_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.hospital_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.leisure_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.pharmacy_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.pub_bar_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.tobacco_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.NO2_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.PM10_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.SO2_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.greenspace_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.GP_pct.range` | pass | 6976 values in [0, 100] |
| `v3.bluespace_pct.range` | pass | 6976 values in [0, 100] |
| `v3.dentist_pct.range` | pass | 6976 values in [0, 100] |
| `v3.fast_food_pct.range` | pass | 6976 values in [0, 100] |
| `v3.gambling_pct.range` | pass | 6976 values in [0, 100] |
| `v3.hospital_pct.range` | pass | 6976 values in [0, 100] |
| `v3.leisure_pct.range` | pass | 6976 values in [0, 100] |
| `v3.pharmacy_pct.range` | pass | 6976 values in [0, 100] |
| `v3.pub_bar_pct.range` | pass | 6976 values in [0, 100] |
| `v3.tobacco_pct.range` | pass | 6976 values in [0, 100] |
| `v3.NO2_pct.range` | pass | 6976 values in [0, 100] |
| `v3.PM10_pct.range` | pass | 6976 values in [0, 100] |
| `v3.SO2_pct.range` | pass | 6976 values in [0, 100] |
| `v3.greenspace_pct.range` | pass | 6976 values in [0, 100] |
| `v3.domain_h_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.domain_g_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.domain_e_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.domain_r_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.domain_h_pct.range` | pass | 6976 values in [1, 100] |
| `v3.domain_g_pct.range` | pass | 6976 values in [1, 100] |
| `v3.domain_e_pct.range` | pass | 6976 values in [1, 100] |
| `v3.domain_r_pct.range` | pass | 6976 values in [1, 100] |
| `v3.ahah_rnk.range` | pass | 6976 values in [1, 41729] |
| `v3.ahah_pct.range` | pass | 6976 values in [1, 100] |
| `v3.ahah_rnk_unique` | pass | 0 |
| `v3.no_minus_one_code` | pass | 0 |
| `v4.scottish_rows` | pass | 6976 |
| `v4.every_zone_of_2011_present_once` | pass | 6976 zones of the pinned list, each once |
| `v4.vintage` | pass | {2011} |
| `v4.presence_matrix` | pass | 90 columns, NULL only where the edition has no column |
| `v4.GP.range` | pass | 6976 values in [0, 1E+18] |
| `v4.bluespace.range` | pass | 6976 values in [0, 1E+18] |
| `v4.dentist.range` | pass | 6976 values in [0, 1E+18] |
| `v4.fast_food.range` | pass | 6976 values in [0, 1E+18] |
| `v4.gambling.range` | pass | 6976 values in [0, 1E+18] |
| `v4.hospital.range` | pass | 6976 values in [0, 1E+18] |
| `v4.leisure.range` | pass | 6976 values in [0, 1E+18] |
| `v4.pharmacy.range` | pass | 6976 values in [0, 1E+18] |
| `v4.pub_bar.range` | pass | 6976 values in [0, 1E+18] |
| `v4.tobacco.range` | pass | 6976 values in [0, 1E+18] |
| `v4.NO2.range` | pass | 6976 values in [0, 1E+18] |
| `v4.PM10.range` | pass | 6976 values in [0, 1E+18] |
| `v4.SO2.range` | pass | 6976 values in [0, 1E+18] |
| `v4.greenspace.range` | pass | 6976 values in [0, 1E+18] |
| `v4.GP_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.bluespace_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.dentist_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.fast_food_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.gambling_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.hospital_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.leisure_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.pharmacy_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.pub_bar_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.tobacco_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.NO2_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.PM10_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.SO2_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.greenspace_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.GP_pct.range` | pass | 6976 values in [0, 100] |
| `v4.bluespace_pct.range` | pass | 6976 values in [0, 100] |
| `v4.dentist_pct.range` | pass | 6976 values in [0, 100] |
| `v4.fast_food_pct.range` | pass | 6976 values in [0, 100] |
| `v4.gambling_pct.range` | pass | 6976 values in [0, 100] |
| `v4.hospital_pct.range` | pass | 6976 values in [0, 100] |
| `v4.leisure_pct.range` | pass | 6976 values in [0, 100] |
| `v4.pharmacy_pct.range` | pass | 6976 values in [0, 100] |
| `v4.pub_bar_pct.range` | pass | 6976 values in [0, 100] |
| `v4.tobacco_pct.range` | pass | 6976 values in [0, 100] |
| `v4.NO2_pct.range` | pass | 6976 values in [0, 100] |
| `v4.PM10_pct.range` | pass | 6976 values in [0, 100] |
| `v4.SO2_pct.range` | pass | 6976 values in [0, 100] |
| `v4.greenspace_pct.range` | pass | 6976 values in [0, 100] |
| `v4.domain_h_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.domain_g_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.domain_e_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.domain_r_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.domain_h_pct.range` | pass | 6976 values in [1, 100] |
| `v4.domain_g_pct.range` | pass | 6976 values in [1, 100] |
| `v4.domain_e_pct.range` | pass | 6976 values in [1, 100] |
| `v4.domain_r_pct.range` | pass | 6976 values in [1, 100] |
| `v4.ahah_rnk.range` | pass | 6976 values in [1, 42648] |
| `v4.ahah_pct.range` | pass | 6976 values in [1, 100] |
| `v4.ahah_rnk_unique` | pass | 0 |
| `v4.no_minus_one_code` | pass | 0 |
| `v5.1.scottish_rows` | pass | 7392 |
| `v5.1.every_zone_of_2022_present_once` | pass | 7392 zones of the pinned list, each once |
| `v5.1.vintage` | pass | {2022} |
| `v5.1.presence_matrix` | pass | 90 columns, NULL only where the edition has no column |
| `v5.1.GP.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.bluespace.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.dentist.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.fast_food.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.gambling.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.greenspace_active.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.hospital.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.leisure.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.pharmacy.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.pub_bar.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.tobacco.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.NO2.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.PM10.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.SO2.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.greenspace.range` | pass | 7392 values in [0, 1E+18] |
| `v5.1.GP_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.bluespace_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.dentist_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.fast_food_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.gambling_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.greenspace_active_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.hospital_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.leisure_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.pharmacy_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.pub_bar_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.tobacco_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.NO2_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.PM10_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.SO2_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.greenspace_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.GP_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.bluespace_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.dentist_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.fast_food_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.gambling_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.greenspace_active_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.hospital_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.leisure_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.pharmacy_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.pub_bar_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.tobacco_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.NO2_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.PM10_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.SO2_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.greenspace_pct.range` | pass | 7392 values in [0, 100] |
| `v5.1.domain_h_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.domain_g_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.domain_e_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.domain_r_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.domain_h_pct.range` | pass | 7392 values in [1, 100] |
| `v5.1.domain_g_pct.range` | pass | 7392 values in [1, 100] |
| `v5.1.domain_e_pct.range` | pass | 7392 values in [1, 100] |
| `v5.1.domain_r_pct.range` | pass | 7392 values in [1, 100] |
| `v5.1.ahah_rnk.range` | pass | 7392 values in [1, 43064] |
| `v5.1.ahah_pct.range` | pass | 7392 values in [1, 100] |
| `v5.1.ahah_rnk_unique` | pass | 0 |
| `v5.1.no_minus_one_code` | pass | 0 |
| `readback.parquet.column_names` | pass | ['ahah_version', 'datazone_vintage', 'datazone_code', 'GP', 'bluespace', 'dentist', 'fast_food', 'gambling', 'greenspace |
| `readback.parquet.column_types` | pass | ['string', 'int16', 'string', 'decimal128(38, 20)', 'decimal128(38, 20)', 'decimal128(38, 20)', 'decimal128(38, 20)', 'd |
| `readback.parquet.nullability` | pass | [False, False, False, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, True, Tr |
| `readback.parquet.metadata.rank_convention` | pass | Every rank, percentile and decile reads 1 as the healthiest area, the opposite of SIMD. Ranks are over Great Britain, no |
| `readback.parquet.metadata.schema_version` | pass | ahah_datazone_v1 |
| `readback.parquet.metadata.key` | pass | ["ahah_version", "datazone_code"] |
| `readback.parquet.metadata.decisions_sha256` | pass | 7e991d0fae558e9713ecdf3ff603795234733d227f5a3316a2c7e769439c2aa9 |
| `readback.parquet.metadata.registry_sha256` | pass | 6b23d95ab11e9ceb27859f4310d6f44f1a61ea3ae5046b08c85d90ef78d446aa |
| `readback.parquet.metadata.sources` | pass | [{"version": "1", "file": "geods_previous/ahah_v1_fulldata.csv", "sha256": "3eb9345e7e5c6dd2ae20473eb95e7e68d3db62485115 |
| `readback.parquet.rows` | pass | 35296 |
| `readback.parquet.primary_key_unique` | pass | 0 |
| `readback.parquet.cells` | pass | 90 columns compared |
| `readback.csv.header` | pass | ['ahah_version', 'datazone_vintage', 'datazone_code', 'GP', 'bluespace', 'dentist', 'fast_food', 'gambling', 'greenspace |
| `readback.csv.rows` | pass | 35296 |
| `readback.csv.cells` | pass | 90 columns compared |
| `decimal_round_trip` | pass | every decimal cell: file text, Decimal, 20-place text, Decimal |

## Three zones, cell for cell against the source file

Version 4 (HEAL-Scot's edition) and version 5.1. The file value is the text in the pinned CSV; the table value is the CSV rendering.

### v4 S01006506

| File column | File value | Table column | Table value |
| --- | --- | --- | --- |
| `LSOA21CD` | `S01006506` | `datazone_code` | `S01006506` |
| `ah4blue` | `1.7074` | `bluespace` | `1.70740000000000000000` |
| `ah4dent` | `1.0778` | `dentist` | `1.07780000000000000000` |
| `ah4gp` | `2.3209` | `GP` | `2.32090000000000000000` |
| `ah4hosp` | `15.1849` | `hospital` | `15.18490000000000000000` |
| `ah4phar` | `1.1607` | `pharmacy` | `1.16070000000000000000` |
| `ah4leis` | `12.3101` | `leisure` | `12.31010000000000000000` |
| `ah4pubs` | `1.0778` | `pub_bar` | `1.07780000000000000000` |
| `ah4ffood` | `0.9459` | `fast_food` | `0.94590000000000000000` |
| `ah4gpas` | `0.5265` | `greenspace` | `0.52650000000000000000` |
| `ah4tob` | `16.7053` | `tobacco` | `16.70530000000000000000` |
| `ah4gamb` | `12.7826` | `gambling` | `12.78260000000000000000` |
| `ah4no2` | `3.0832` | `NO2` | `3.08320000000000000000` |
| `ah4so2` | `0.5331` | `SO2` | `0.53310000000000000000` |
| `ah4pm10` | `8.8811` | `PM10` | `8.88110000000000000000` |
| `ah4gp_rnk` | `22518` | `GP_rnk` | `22518` |
| `ah4dent_rnk` | `6556` | `dentist_rnk` | `6556` |
| `ah4phar_rnk` | `10008` | `pharmacy_rnk` | `10008` |
| `ah4hosp_rnk` | `41241` | `hospital_rnk` | `41241` |
| `ah4leis_rnk` | `38645` | `leisure_rnk` | `38645` |
| `ah4gpas_rnk` | `7556` | `greenspace_rnk` | `7556` |
| `ah4blue_rnk` | `8316` | `bluespace_rnk` | `8316` |
| `ah4no2_rnk` | `1980` | `NO2_rnk` | `1980` |
| `ah4so2_rnk` | `2015` | `SO2_rnk` | `2015` |
| `ah4pm10_rnk` | `6079` | `PM10_rnk` | `6079` |
| `ah4gamb_rnk` | `3844` | `gambling_rnk` | `3844` |
| `ah4pubs_rnk` | `33320` | `pub_bar_rnk` | `33320` |
| `ah4tob_rnk` | `3186` | `tobacco_rnk` | `3186` |
| `ah4ffood_rnk` | `33259` | `fast_food_rnk` | `33259` |
| `ah4gp_pct` | `52` | `GP_pct` | `52` |
| `ah4dent_pct` | `15` | `dentist_pct` | `15` |
| `ah4phar_pct` | `23` | `pharmacy_pct` | `23` |
| `ah4hosp_pct` | `96` | `hospital_pct` | `96` |
| `ah4leis_pct` | `90` | `leisure_pct` | `90` |
| `ah4gpas_pct` | `17` | `greenspace_pct` | `17` |
| `ah4blue_pct` | `19` | `bluespace_pct` | `19` |
| `ah4no2_pct` | `4` | `NO2_pct` | `4` |
| `ah4so2_pct` | `4` | `SO2_pct` | `4` |
| `ah4pm10_pct` | `14` | `PM10_pct` | `14` |
| `ah4gamb_pct` | `9` | `gambling_pct` | `9` |
| `ah4pubs_pct` | `78` | `pub_bar_pct` | `78` |
| `ah4tob_pct` | `7` | `tobacco_pct` | `7` |
| `ah4ffood_pct` | `77` | `fast_food_pct` | `77` |
| `ah4h` | `0.2963` | `domain_h` | `0.29630000000000000000` |
| `ah4g` | `-0.8930` | `domain_g` | `-0.89300000000000000000` |
| `ah4e` | `-1.4740` | `domain_e` | `-1.47400000000000000000` |
| `ah4r` | `-0.3084` | `domain_r` | `-0.30840000000000000000` |
| `ah4h_rnk` | `28015` | `domain_h_rnk` | `28015` |
| `ah4g_rnk` | `2637` | `domain_g_rnk` | `2637` |
| `ah4e_rnk` | `2674` | `domain_e_rnk` | `2674` |
| `ah4r_rnk` | `14794` | `domain_r_rnk` | `14794` |
| `ah4h_pct` | `66` | `domain_h_pct` | `66` |
| `ah4g_pct` | `7` | `domain_g_pct` | `7` |
| `ah4e_pct` | `7` | `domain_e_pct` | `7` |
| `ah4r_pct` | `35` | `domain_r_pct` | `35` |
| `ah4ahah` | `9.1497` | `ahah` | `9.14970000000000000000` |
| `ah4ahah_rnk` | `1001` | `ahah_rnk` | `1001` |
| `ah4ahah_pct` | `3` | `ahah_pct` | `3` |

### v4 S01008132

| File column | File value | Table column | Table value |
| --- | --- | --- | --- |
| `LSOA21CD` | `S01008132` | `datazone_code` | `S01008132` |
| `ah4blue` | `1.6157` | `bluespace` | `1.61570000000000000000` |
| `ah4dent` | `2.0224` | `dentist` | `2.02240000000000000000` |
| `ah4gp` | `1.8003` | `GP` | `1.80030000000000000000` |
| `ah4hosp` | `3.5895` | `hospital` | `3.58950000000000000000` |
| `ah4phar` | `1.9552` | `pharmacy` | `1.95520000000000000000` |
| `ah4leis` | `2.5551` | `leisure` | `2.55510000000000000000` |
| `ah4pubs` | `2.0224` | `pub_bar` | `2.02240000000000000000` |
| `ah4ffood` | `1.0109` | `fast_food` | `1.01090000000000000000` |
| `ah4gpas` | `0.4893` | `greenspace` | `0.48930000000000000000` |
| `ah4tob` | `1.9906` | `tobacco` | `1.99060000000000000000` |
| `ah4gamb` | `1.9552` | `gambling` | `1.95520000000000000000` |
| `ah4no2` | `6.4854` | `NO2` | `6.48540000000000000000` |
| `ah4so2` | `0.8528` | `SO2` | `0.85280000000000000000` |
| `ah4pm10` | `8.6181` | `PM10` | `8.61810000000000000000` |
| `ah4gp_rnk` | `16267` | `GP_rnk` | `16267` |
| `ah4dent_rnk` | `20093` | `dentist_rnk` | `20093` |
| `ah4phar_rnk` | `24157` | `pharmacy_rnk` | `24157` |
| `ah4hosp_rnk` | `30148` | `hospital_rnk` | `30148` |
| `ah4leis_rnk` | `17125` | `leisure_rnk` | `17125` |
| `ah4gpas_rnk` | `11827` | `greenspace_rnk` | `11827` |
| `ah4blue_rnk` | `7599` | `bluespace_rnk` | `7599` |
| `ah4no2_rnk` | `8559` | `NO2_rnk` | `8559` |
| `ah4so2_rnk` | `6841` | `SO2_rnk` | `6841` |
| `ah4pm10_rnk` | `5178` | `PM10_rnk` | `5178` |
| `ah4gamb_rnk` | `27033` | `gambling_rnk` | `27033` |
| `ah4pubs_rnk` | `18957` | `pub_bar_rnk` | `18957` |
| `ah4tob_rnk` | `32444` | `tobacco_rnk` | `32444` |
| `ah4ffood_rnk` | `31833` | `fast_food_rnk` | `31833` |
| `ah4gp_pct` | `38` | `GP_pct` | `38` |
| `ah4dent_pct` | `47` | `dentist_pct` | `47` |
| `ah4phar_pct` | `56` | `pharmacy_pct` | `56` |
| `ah4hosp_pct` | `70` | `hospital_pct` | `70` |
| `ah4leis_pct` | `40` | `leisure_pct` | `40` |
| `ah4gpas_pct` | `27` | `greenspace_pct` | `27` |
| `ah4blue_pct` | `17` | `bluespace_pct` | `17` |
| `ah4no2_pct` | `20` | `NO2_pct` | `20` |
| `ah4so2_pct` | `16` | `SO2_pct` | `16` |
| `ah4pm10_pct` | `12` | `PM10_pct` | `12` |
| `ah4gamb_pct` | `63` | `gambling_pct` | `63` |
| `ah4pubs_pct` | `44` | `pub_bar_pct` | `44` |
| `ah4tob_pct` | `76` | `tobacco_pct` | `76` |
| `ah4ffood_pct` | `74` | `fast_food_pct` | `74` |
| `ah4h` | `0.0176` | `domain_h` | `0.01760000000000000000` |
| `ah4g` | `-0.7566` | `domain_g` | `-0.75660000000000000000` |
| `ah4e` | `-1.0000` | `domain_e` | `-1.00000000000000000000` |
| `ah4r` | `0.3936` | `domain_r` | `0.39360000000000000000` |
| `ah4h_rnk` | `22157` | `domain_h_rnk` | `22157` |
| `ah4g_rnk` | `3990` | `domain_g_rnk` | `3990` |
| `ah4e_rnk` | `5702` | `domain_e_rnk` | `5702` |
| `ah4r_rnk` | `28802` | `domain_r_rnk` | `28802` |
| `ah4h_pct` | `52` | `domain_h_pct` | `52` |
| `ah4g_pct` | `10` | `domain_g_pct` | `10` |
| `ah4e_pct` | `14` | `domain_e_pct` | `14` |
| `ah4r_pct` | `68` | `domain_r_pct` | `68` |
| `ah4ahah` | `11.8218` | `ahah` | `11.82180000000000000000` |
| `ah4ahah_rnk` | `3561` | `ahah_rnk` | `3561` |
| `ah4ahah_pct` | `9` | `ahah_pct` | `9` |

### v5.1 S01013482

| File column | File value | Table column | Table value |
| --- | --- | --- | --- |
| `lsoa21cd` | `S01013482` | `datazone_code` | `S01013482` |
| `GP` | `2.221078431372549` | `GP` | `2.22107843137254900000` |
| `bluespace` | `0.5681372549019608` | `bluespace` | `0.56813725490196080000` |
| `dentist` | `1.3794117647058823` | `dentist` | `1.37941176470588230000` |
| `fast_food` | `0.9808823529411765` | `fast_food` | `0.98088235294117650000` |
| `gambling` | `8.511274509803922` | `gambling` | `8.51127450980392200000` |
| `greenspace_active` | `0.6857843137254902` | `greenspace_active` | `0.68578431372549020000` |
| `hospital` | `15.17156862745098` | `hospital` | `15.17156862745098000000` |
| `leisure` | `8.847058823529412` | `leisure` | `8.84705882352941200000` |
| `pharmacy` | `1.3970588235294117` | `pharmacy` | `1.39705882352941170000` |
| `pub_bar` | `1.0431372549019609` | `pub_bar` | `1.04313725490196090000` |
| `tobacco` | `12.401960784313726` | `tobacco` | `12.40196078431372600000` |
| `NO2` | `2.832116206581371` | `NO2` | `2.83211620658137100000` |
| `PM10` | `7.430482501954381` | `PM10` | `7.43048250195438100000` |
| `SO2` | `0.5304669052447176` | `SO2` | `0.53046690524471760000` |
| `greenspace` | `0.7519430777510036` | `greenspace` | `0.75194307775100360000` |
| `GP_rnk` | `24942` | `GP_rnk` | `24942` |
| `dentist_rnk` | `13589` | `dentist_rnk` | `13589` |
| `pharmacy_rnk` | `17611` | `pharmacy_rnk` | `17611` |
| `hospital_rnk` | `34398` | `hospital_rnk` | `34398` |
| `leisure_rnk` | `38529` | `leisure_rnk` | `38529` |
| `greenspace_active_rnk` | `30545` | `greenspace_active_rnk` | `30545` |
| `greenspace_rnk` | `3561` | `greenspace_rnk` | `3561` |
| `bluespace_rnk` | `4090` | `bluespace_rnk` | `4090` |
| `NO2_rnk` | `1749` | `NO2_rnk` | `1749` |
| `PM10_rnk` | `3433` | `PM10_rnk` | `3433` |
| `SO2_rnk` | `2208` | `SO2_rnk` | `2208` |
| `fast_food_rnk` | `27367` | `fast_food_rnk` | `27367` |
| `gambling_rnk` | `3605` | `gambling_rnk` | `3605` |
| `pub_bar_rnk` | `30918` | `pub_bar_rnk` | `30918` |
| `tobacco_rnk` | `1989` | `tobacco_rnk` | `1989` |
| `GP_pct` | `57` | `GP_pct` | `57` |
| `dentist_pct` | `31` | `dentist_pct` | `31` |
| `pharmacy_pct` | `40` | `pharmacy_pct` | `40` |
| `hospital_pct` | `79` | `hospital_pct` | `79` |
| `leisure_pct` | `89` | `leisure_pct` | `89` |
| `greenspace_pct` | `8` | `greenspace_pct` | `8` |
| `greenspace_active_pct` | `70` | `greenspace_active_pct` | `70` |
| `bluespace_pct` | `9` | `bluespace_pct` | `9` |
| `NO2_pct` | `4` | `NO2_pct` | `4` |
| `PM10_pct` | `7` | `PM10_pct` | `7` |
| `SO2_pct` | `5` | `SO2_pct` | `5` |
| `fast_food_pct` | `63` | `fast_food_pct` | `63` |
| `gambling_pct` | `8` | `gambling_pct` | `8` |
| `pub_bar_pct` | `71` | `pub_bar_pct` | `71` |
| `tobacco_pct` | `4` | `tobacco_pct` | `4` |
| `domain_h` | `0.3156562378723941` | `domain_h` | `0.31565623787239410000` |
| `domain_g` | `-0.7155940604227714` | `domain_g` | `-0.71559406042277140000` |
| `domain_e` | `-1.5945109152575732` | `domain_e` | `-1.59451091525757320000` |
| `domain_r` | `-0.5351421138597074` | `domain_r` | `-0.53514211385970740000` |
| `domain_h_rnk` | `29591` | `domain_h_rnk` | `29591` |
| `domain_h_pct` | `69` | `domain_h_pct` | `69` |
| `domain_g_rnk` | `4659` | `domain_g_rnk` | `4659` |
| `domain_g_pct` | `11` | `domain_g_pct` | `11` |
| `domain_e_rnk` | `1754` | `domain_e_rnk` | `1754` |
| `domain_e_pct` | `5` | `domain_e_pct` | `5` |
| `domain_r_rnk` | `10673` | `domain_r_rnk` | `10673` |
| `domain_r_pct` | `25` | `domain_r_pct` | `25` |
| `ahah` | `9.018908449993397` | `ahah` | `9.01890844999339700000` |
| `ahah_rnk` | `1454` | `ahah_rnk` | `1454` |
| `ahah_pct` | `4` | `ahah_pct` | `4` |
