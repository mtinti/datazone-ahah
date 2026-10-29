# Draft issue for GeographicDataService/ahah

**Title:** Indicator percentiles run 0 to 100, domain and index percentiles 1 to 100

Hello, and thank you for publishing AHAH and its code.

I am loading AHAH into the trusted research environment at HIC, University of Dundee, so that
research projects there can use it. While checking the files I found that the percentiles use
two different scales from version 3 onward.

- The fifteen indicator percentiles (`GP_pct`, `NO2_pct` and so on) take 101 values, 0 to 100.
- The four domain percentiles and `ahah_pct` take 100 values, 1 to 100.

The difference comes from two formulas in the build code:

```python
# indicators
idx[f"{col}_pct"] = (idx[f"{col}_rnk"] / idx[f"{col}_rnk"].max() * 100).astype(int)
# domains and index
idx[f"domain_{d}_pct"] = pd.qcut(idx[f"domain_{d}_rnk"], 100, labels=False) + 1
```

The first truncates, so rank 1 becomes percentile 0, and only the largest rank reaches 100. The
second gives a hundred equal bins labelled 1 to 100. Both formulas appear in
[`ahah/create_index.py` at v4](https://github.com/GeographicDataService/ahah/blob/722fe5f/ahah/create_index.py#L62-L97)
(and at the v3 tag), and in the "Create Index" cell of
[`AHAH_Build_Indicator.ipynb` at v5](https://github.com/GeographicDataService/ahah/blob/v5/AHAH_Build_Indicator.ipynb).
Applying them to the published ranks reproduces every percentile in the v3, v4 and v5.1 files.

The v5 technical methodology, section 7 "Output Variables", describes `[indicator]_pct` as
"National percentile for each indicator (1-100)". The published indicator percentiles include 0,
so the files and the report disagree.

Could you confirm which is intended? If 1 to 100 is meant, the indicator percentiles could use
the same `qcut` formula as the domains. If the current values are intended, a note in the
methodology and the variable dictionary would help users, since a user who joins an indicator
percentile and a domain percentile is comparing two scales.

Two smaller things noticed on the way:

- The GeoDS dataset page links the code as `AHAH_V5`, which returns 404. This repository seems
  to be the right one.
- In the v5.1 file the code column is named `lsoa21cd` for Scotland too, and the variable
  dictionary describes it as "(2011)", while the Scottish rows are the 7,392 data zones of 2022
  as the methodology says.

Thanks again.
