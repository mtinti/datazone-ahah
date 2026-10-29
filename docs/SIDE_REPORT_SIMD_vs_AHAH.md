# Side report: SIMD 2020v2 and AHAH on Scotland's data zones

This note compares the Scottish Index of Multiple Deprivation (SIMD) with the Access to Healthy
Assets and Hazards index (AHAH) for a study that wants both. The main analysis is AHAH version 4
against SIMD 2020v2 on the 6,976 data zones of 2011. Every number comes from the scripts in
section 6.

## 1. What each index measures

SIMD measures the deprivation of the people who live in an area. SIMD 2020v2 ranks the 6,976
data zones of 2011 from rank 1, the most deprived, to 6,976, the least deprived. It combines
seven domains from 32 indicators: income, employment, health, education, geographic access to
services, crime and housing. The Scottish Government cuts the rank into bands with 20% of the
zones in each quintile. Public Health Scotland (PHS) cuts it with about 20% of the population in
each, and says not to mix the two cuts.

AHAH measures the physical environment around an area: how near its residents are to things
that help or harm health. Four domains from 14 indicators in v4 (15 in v5.1): health services
(drive time to the nearest GP, dentist, pharmacy, hospital and leisure centre), green and blue
space, air quality (NO2, PM10 and SO2) and retail hazards (drive time to the nearest fast-food
outlet, gambling outlet, pub and tobacconist). Travel times are computed per postcode and
averaged over the area. Each indicator, each domain and the index carry a score, a rank over
Great Britain and a percentile. AHAH knows nothing about the residents.

| | SIMD 2020v2 | AHAH v4 |
| --- | --- | --- |
| Measures | deprivation of the residents | the surrounding environment |
| Rank 1 means | most deprived | healthiest environment |
| Ranked over | 6,976 zones of Scotland | 42,648 areas of Great Britain |
| Geography | 2011 data zones | 2011 data zones (v5.1: 2022 data zones) |
| Published bands | quintile, decile and vigintile, unweighted (Government) and population-weighted (PHS) | percentiles over Great Britain, no Scottish band |

The scales point opposite ways, so a negative correlation between an AHAH rank and a SIMD rank
means that the more deprived zones have the less healthy environment, and a positive one the
reverse.

## 2. Overlap of inputs

| SIMD access domain (10 indicators) | AHAH health services domain (5 indicators) |
| --- | --- |
| drive time to a GP surgery | drive time to the nearest GP practice |
| drive time to a post office, a primary school, a secondary school, a retail centre and a petrol station | drive time to the nearest dentist, pharmacy, hospital with A&E and leisure centre |
| public transport time to a GP, a post office and a retail centre | |
| share of premises without superfast broadband | |

The one shared input is the drive time to a GP. The two measures agree in order, not in level,
because road networks, routing engines, years and averaging rules differ. So does the direction:
SIMD access rank 1 is the longest travel, AHAH health-services rank 1 the shortest.

| GP drive time, 6,976 zones | AHAH v4 | SIMD 2020v2 |
| --- | --- | --- |
| median, minutes | 2.6 | 2.9 |
| 90th percentile, minutes | 8.5 | 6.2 |
| Spearman between the two | 0.75 | |

Neither index contains the other. SIMD has no air, green space or retail hazard indicator. AHAH
has no indicator about residents. One naming trap: SIMD's health domain is the residents'
illness, mortality and prescribing, not health services.

## 3. Empirical comparison: AHAH v4 against SIMD 2020v2

All 6,976 zones join on their code. Spearman correlation of the published ranks:

| AHAH v4 rank (1 = healthiest) | SIMD overall (1 = most deprived) | income | employment | health | education | access | crime | housing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| overall | 0.00 | 0.05 | 0.06 | 0.07 | −0.01 | −0.08 | −0.03 | −0.08 |
| health services | 0.21 | 0.29 | 0.28 | 0.31 | 0.22 | −0.77 | 0.47 | 0.46 |
| green and blue space | 0.01 | 0.00 | 0.00 | −0.03 | −0.07 | 0.17 | −0.10 | −0.03 |
| air quality | −0.10 | −0.13 | −0.12 | −0.18 | −0.15 | 0.35 | −0.29 | −0.36 |
| retail | −0.26 | −0.32 | −0.31 | −0.35 | −0.27 | 0.67 | −0.48 | −0.49 |

The overall indexes are unrelated (−0.004). The domains cancel: deprived zones have better
access to health services but sit nearer retail hazards and in worse air. The strongest links
are with SIMD's access domain, a rurality axis: remote zones are far from services and far from
hazards.

Cross-tabulation. The AHAH quintile is derived, not published: rank the Scottish zones by their
Great Britain rank and cut with the Government's rule, ceil(rank × 5 / 6,976), which gives 1,395
or 1,396 zones per band. The SIMD quintile is the Government's unweighted one.

| SIMD quintile (1 = most deprived) | AHAH 1 (healthiest) | AHAH 2 | AHAH 3 | AHAH 4 | AHAH 5 (least healthy) |
| --- | --- | --- | --- | --- | --- |
| 1 | 307 | 320 | 293 | 243 | 232 |
| 2 | 260 | 290 | 261 | 294 | 290 |
| 3 | 267 | 215 | 251 | 309 | 353 |
| 4 | 250 | 223 | 298 | 329 | 295 |
| 5 | 311 | 347 | 292 | 220 | 226 |

| Agreement | Zones | Share | Expected if independent |
| --- | --- | --- | --- |
| same fifth on the good-to-bad axis (SIMD q with AHAH 6 − q) | 1,311 | 18.8% | 20.0% |
| opposite extremes (most deprived and healthiest, least deprived and least healthy) | 533 | 7.6% | 8.0% |
| concordant extremes (most deprived and least healthy, least deprived and healthiest) | 543 | 7.8% | 8.0% |
| same tenth, with deciles | 650 | 9.3% | 10.0% |
| same fifth, with the PHS population-weighted SIMD quintile | 1,329 | 19.1% | 20.0% |

The health-services domain alone has a clear pattern: 55 of the 1,395 most deprived zones are in
the worst-access fifth, against 508 of SIMD quintile 4.

| SIMD quintile | AHAH health services 1 (best access) | 2 | 3 | 4 | 5 (worst access) |
| --- | --- | --- | --- | --- | --- |
| 1 | 390 | 396 | 337 | 217 | 55 |
| 2 | 328 | 318 | 331 | 277 | 141 |
| 3 | 238 | 232 | 215 | 248 | 462 |
| 4 | 180 | 190 | 230 | 287 | 508 |
| 5 | 259 | 259 | 282 | 366 | 230 |

Urban and rural. The pinned SIMD files carry no urban/rural flag, so the split uses a derived
one: the majority Urban Rural Classification 2016 class of each zone's current small-user
postcodes, from the postcode-simd history table. Rural is class 5 and 6, the rest class 1 to 4,
and 9 zones have a tie or no current postcode. The overall correlation stays near zero in both
groups.

| Rural flag, derived | Rural, 1,284 zones | Rest of Scotland, 5,683 zones | All, 6,976 zones |
| --- | --- | --- | --- |
| Spearman, AHAH overall vs SIMD overall | −0.06 | −0.03 | 0.00 |
| Spearman, AHAH health services vs SIMD access | −0.78 | −0.69 | −0.77 |
| Spearman, AHAH health services vs SIMD overall | −0.06 | 0.17 | 0.21 |
| Spearman, AHAH retail vs SIMD overall | 0.11 | −0.24 | −0.26 |
| Spearman, AHAH air quality vs SIMD overall | 0.14 | −0.06 | −0.10 |
| zones in the worst fifth for health services | 79% | 7% | 20% |
| zones in SIMD quintile 1 | 4% | 24% | 20% |

AHAH v5.1, postcode-weighted. Version 5.1 is on 2022 data zones and cannot join SIMD by zone.
Each of the 157,282 current small-user postcodes in the history table carries its 2011 zone,
which gives SIMD, and its 2022 zone, which gives v5.1. Each postcode counts once. AHAH v4 on the
same postcodes shows that the weighting changes little.

| Spearman across 157,282 postcodes | AHAH v5.1 | AHAH v4 |
| --- | --- | --- |
| overall vs SIMD overall | −0.05 | −0.04 |
| health services vs SIMD access | −0.81 | −0.82 |
| retail vs SIMD overall | −0.29 | −0.27 |
| air quality vs SIMD overall | −0.18 | −0.11 |

## 4. Differences and cautions

Vintage. The zones of 2011 and 2022 do not nest, so never convert one to the other. Join each
index on the zone of its own vintage.

| Seen through current small-user postcodes | Count |
| --- | --- |
| zones of 2022 whose postcodes come from two or more 2011 zones | 2,684 of 7,392 |
| zones of 2011 whose postcodes spread over two or more 2022 zones | 2,466 of 6,974 |
| postcodes in a 2022 zone that straddles 2011 zones | 43% |

Rank population. AHAH ranks and percentiles are over Great Britain. A Great Britain band is not
a Scottish band, and any within-Scotland band is a derivation to be named as such.

| Scottish zones on the Great Britain scale, AHAH v4 | |
| --- | --- |
| median percentile, overall | 29 |
| median percentile, health services | 64 |
| median percentile, air quality | 13 |
| zones in the healthiest fifth of Great Britain | 39% |
| zones in the least healthy fifth | 8% |
| derived Scottish fifths, in Great Britain percentiles | 1 to 9, 9 to 21, 21 to 39, 39 to 63, 63 to 100 |

Direction. SIMD rank 1 is the most deprived zone, AHAH rank 1 the healthiest. The ten most
deprived zones of Scotland have a median AHAH percentile of 11.5, on the healthy side. A sign
error flips every conclusion.

Population weighting. AHAH ranks are unweighted. SIMD bands come in both cuts: 231 zones change
quintile and 481 change decile between the Government's cut and the PHS cut. The derived AHAH
fifths hold 19.7% to 20.6% of the 2017 population, a small imbalance. Say which cut each band
uses and do not mix cuts.

Two percentile scales. AHAH indicator percentiles run 0 to 100 and domain and index percentiles
1 to 100 (`PERCENTILES.md`). They are not one scale.

Editions. AHAH is not a deprivation measure and has no PHS guidance on which edition fits which
year. Use one edition per study and never compare editions. SIMD 2020v2 uses 2017 population
weights, AHAH v4 inputs date from 2022 to 2024, and v5.1 inputs from 2024 and 2025.

| Spearman between editions | Overall | Health services | Green and blue space | Air quality | Retail |
| --- | --- | --- | --- | --- | --- |
| v3 vs v4, 6,976 zones of 2011 | 0.76 | 0.93 | 0.77 | 0.96 | 0.92 |
| v4 vs v5.1, across 157,282 postcodes, two vintages mixed | 0.62 | 0.89 | 0.23 | 0.92 | 0.94 |

Between v3 and v4 the GP drive time correlates at 0.92, yet its median fell from 3.9 to 2.6
minutes. Ties: the v4 air quality domain has 5,682 distinct ranks among the 6,976 Scottish
zones, so tied zones share a derived band.

Disclosure. Both indexes are public per zone, so a released combination of bands can name the
zone. One overall band of each index is safe on its own. Domain bands and published percentiles
are not, and each added band multiplies the risk.

| Released bands, zones singled out of 6,976 | Unique zones | Share | Smallest group |
| --- | --- | --- | --- |
| SIMD overall quintile (Government cut) + AHAH overall quintile (derived) | 0 | 0.0% | 215 |
| SIMD overall quintile (PHS cut) + AHAH overall quintile (derived) | 0 | 0.0% | 210 |
| SIMD overall decile (Government cut) + AHAH overall decile (derived) | 0 | 0.0% | 42 |
| SIMD overall decile (PHS cut) + AHAH overall decile (derived) | 0 | 0.0% | 41 |
| AHAH overall Great Britain percentile alone (published) | 0 | 0.0% | 7 |
| SIMD overall decile + AHAH overall Great Britain percentile | 57 | 0.8% | 1 |
| SIMD overall quintile + AHAH four domain quintiles | 524 | 7.5% | 1 |
| SIMD seven domain quintiles | 1,923 | 27.6% | 1 |
| SIMD seven domain quintiles + AHAH overall quintile | 3,716 | 53.3% | 1 |
| SIMD overall decile + AHAH four domain deciles | 4,847 | 69.5% | 1 |
| SIMD seven domain quintiles + AHAH four domain quintiles | 6,107 | 87.5% | 1 |
| AHAH overall + four domain Great Britain percentiles (published) | 6,864 | 98.4% | 1 |

## 5. Uncertainty

The correlations describe all 6,976 zones, not a sample, so no interval is given. The
urban/rural flag is a postcode majority, not the published zone flag. The v5.1 figures weight by
postcode and mix two vintages, so they are not the zone-level quantity.

## 6. How this was computed

Scripts, all run with `python3 -I` (Python 3.12.11, pandas 3.0.3, scipy 1.18.0, pyarrow 24.0.0,
dbfread 2.0.7), in `/private/tmp/claude-502/-Users-mtinti-git-projects-AHAH/fd89cb56-bfc2-405f-872a-e5f6f97aea6c/scratchpad/simd_ahah/`:

| Script | What it computes | Output |
| --- | --- | --- |
| `compare_v4_simd2020v2.py` | the join, the Spearman table, the GP drive-time comparison, the derived bands, the cross-tabulations, population shares, the urban/rural split, the disclosure counts and the v3 to v4 comparison | `results_v4_simd2020v2.json`, `tables_v4_simd2020v2.md`, `run_v4.log` |
| `compare_v51_postcode_weighted.py` | the postcode-weighted v5.1 and v4 correlations and the vintage nesting counts | `results_v51_postcode_weighted.json`, `tables_v51_postcode_weighted.md`, `run_v51.log` |
| `crosscheck.py` | the headline numbers again by a second route (pandas' own Spearman, qcut bands, direct counts) and the ten most deprived zones | `crosscheck.log` |
| `extract_pdf_text.py` | text of the three PDFs read for sections 1 and 2 | `ahah_v5_methodology.txt`, `ahah_v4_datasources.txt`, `phs_guidance_v35.txt` |

Source files, under `/Users/mtinti/git_projects/`, and their SHA256:

| File | SHA256 | Used for |
| --- | --- | --- |
| `AHAH/data/sources/geods_previous/ahah_v4.csv` | `55fefee78a13bd69f4ecb3c17818206d723b862cacd0ab3e0dae8153171a7a4e` | AHAH v4 ranks, percentiles and GP minutes, rows starting `S01` |
| `AHAH/data/sources/geods_previous/ahah_v3_fulldata.csv` | `38e02a3f88efc4e681777cc090632fb515309a31439d01841655231df83d2d37` | v3 to v4 comparison |
| `AHAH/data/sources/geods/ahah_v5_1.csv` | `3067fef8ca5f718220359fc60af817fb557ecf7f798c095142d8d7f6f5f22c22` | AHAH v5.1 ranks, postcode-weighted route |
| `SIMD/manual_data/data.gov.uk/SG_SIMD_2020/SG_SIMD_2020.dbf` | `3eb0f27aa4aa2e2eaf94a06201e9dfb4597cd3ab5dffb375ee4917f9b37eee5a` | SIMD 2020v2 overall and seven domain ranks, Government quintile and decile, 2017 population, GP drive times. The easiest reliable source: one row per zone, every rank in one table |
| `SIMD/manual_data/PHS/simd2020v2_22062020.csv` | `686bc9aa38b61891f701e10d8a3970397c7be7f3819798dc43584ae42cb3a391` | PHS population-weighted quintile and decile. The copy in `~/Downloads` has the same SHA256 and was not used |
| `SIMD/manual_data/statistics.gov.scot/simd_2020.csv` | `25fea7ddaf54659ac24c6d9e9c6af73d3da18ef2a8477c30b61a7c937f3dabbf` | the published seven domain quintiles and deciles, for the disclosure counts |
| `SIMD/results/postcode_simd_history.parquet` | `70c226e71843c483bca8bcc326e24e1b133a039499603cc65568e5eabe9b2572` | current small-user postcodes with both zone codes, SIMD ranks and the Urban Rural Classification 2016 class |
| `AHAH/data/sources/geods/ahah_v5_technical_methodology.pdf` | `8a23d522a8b1d0f64426251c54f314eb57871c3621ebc27cbbbce25fb3a999cb` | what AHAH measures, its domains and ranking direction |
| `AHAH/data/sources/geods_previous/ahah_datasources.pdf` | `5200e682e11c3ef654db57d25b5f261dee54d91e5db1a1d6ccba3cb2247636f8` | v4 input dates |
| `SIMD/manual_data/data.gov.uk/SG_SIMD_2020/SIMD2020v2 - GIS files - glossary.xlsx` | `2e4896cc5ed192353ffc47c17f37f55a98a9b15a6ce2c08221a44d0dc4f6a20c` | the SIMD access domain indicators |
| `SIMD/manual_data/2023-12-phs-deprivation-guidance-v35.pdf` | `b952685972b22692c0edb0e4bdea579cfd07dbed69437aab87c5527940fa7b45` | SIMD domains, direction, the two band cuts |

Checks the scripts enforce before any number is written: 6,976 Scottish rows in v4 and v3 and
7,392 in v5.1, all codes unique, every zone matched on the join, the PHS rank equal to the
Government rank on every zone, the Government cut reproducing the published quintile and decile
on every zone, and the statistics.gov.scot overall bands equal to the shapefile's.
