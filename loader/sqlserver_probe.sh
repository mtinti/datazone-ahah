#!/usr/bin/env bash
# Run the generated import and check scripts against a throwaway SQL Server 2022 container, then
# probe the two things the Python tests cannot: that SQL Server renders a decimal(38,20) and an
# int exactly as Python did, and that the left join returns every cohort row once with the right
# status. Usage: bash loader/sqlserver_probe.sh   (needs docker; starts the container if absent).
# Bash, not sh: the script uses `set -o pipefail`.
set -euo pipefail
# pipefail: a failing sqlcmd anywhere in a pipeline fails the run. Each sqlcmd result is first
# written raw, so its exit status is its own, and only then filtered; the filtered file is
# re-read and its line count asserted before it is trusted.
cd "$(dirname "$0")/.."
PW='Ahah_test_Pw0rd!'
C=ahah_mssql
if ! docker ps --format '{{.Names}}' | grep -qx $C; then
  docker run --platform linux/amd64 -d --name $C -e ACCEPT_EULA=Y -e "MSSQL_SA_PASSWORD=$PW" -e MSSQL_PID=Developer \
    mcr.microsoft.com/mssql/server:2022-latest >/dev/null
fi
SQL="docker exec -i $C /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P $PW -C -b"
for i in $(seq 1 60); do $SQL -Q "SELECT 1" >/dev/null 2>&1 && break; sleep 2; done
$SQL -Q "IF DB_ID('ahah') IS NULL CREATE DATABASE ahah"
W=$(mktemp -d)
# Verify results/ and copy the manifest and the uncompressed CSV out while owning the folder, so
# everything below reads one verified generation from $W and never results/ itself.
python3 -m ahah_ingest.pipeline --export "$W"
ROWS=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['csv']['rows'])" "$W/manifest.json")
TOTAL=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['csv']['digest']['total'])" "$W/manifest.json")
sed "s#/path/to/ahah_datazone.csv#/tmp/ahah/ahah_datazone.csv#" docs/sql/import_csv.sql > "$W/import.sql"
sed "s#(N'ahah_datazone', 0, 0, 1)#(N'ahah_datazone', $ROWS, $TOTAL, 1)#" docs/sql/check_loaded_digest.sql > "$W/check.sql"
docker exec $C mkdir -p /tmp/ahah
docker cp "$W/ahah_datazone.csv" $C:/tmp/ahah/ahah_datazone.csv
docker cp "$W/import.sql" $C:/tmp/ahah/import.sql
docker cp "$W/check.sql" $C:/tmp/ahah/check.sql
echo "== import"
$SQL -d ahah -i /tmp/ahah/import.sql
echo "== check_loaded_digest (expected rows $ROWS, total $TOTAL)"
$SQL -d ahah -i /tmp/ahah/check.sql -W -s '|'
echo "== probe: SQL rendering of chosen cells against the CSV text"
python3 - "$W/ahah_datazone.csv" > "$W/probe_expected.txt" <<'PY'
import csv, sys
rows = {}
with open(sys.argv[1], newline="", encoding="utf-8") as fh:
    r = csv.DictReader(fh)
    for row in r:
        key = (row["ahah_version"], row["datazone_code"])
        if key in {("3", "S01006506"), ("4", "S01008132"), ("2", "S01010206"), ("5.1", "S01013482"), ("1", "S01006506")}:
            rows[key] = row
for (v, code), row in sorted(rows.items()):
    for col in ("GP", "domain_e", "ahah", "ahah_rnk", "GP_dec", "ur", "domain_h_exp", "SO2"):
        print(f"{v}|{code}|{col}|{row[col]}")
PY
$SQL -d ahah -W -h -1 -s '|' -Q "SET NOCOUNT ON; SELECT ahah_version, datazone_code, c.col, ISNULL(c.val, '') FROM ahah_datazone a CROSS APPLY (VALUES ('GP', CONVERT(varchar(40), GP)), ('domain_e', CONVERT(varchar(40), domain_e)), ('ahah', CONVERT(varchar(40), ahah)), ('ahah_rnk', CONVERT(varchar(11), ahah_rnk)), ('GP_dec', CONVERT(varchar(11), GP_dec)), ('ur', CONVERT(varchar(11), ur)), ('domain_h_exp', CONVERT(varchar(40), domain_h_exp)), ('SO2', CONVERT(varchar(40), SO2))) c(col, val) WHERE (ahah_version='3' AND datazone_code='S01006506') OR (ahah_version='4' AND datazone_code='S01008132') OR (ahah_version='2' AND datazone_code='S01010206') OR (ahah_version='5.1' AND datazone_code='S01013482') OR (ahah_version='1' AND datazone_code='S01006506') ORDER BY ahah_version, datazone_code, c.col" > "$W/probe_raw.txt"
sed 's/ *|/|/g; s/ *$//' "$W/probe_raw.txt" | { grep -v '^$' || true; } > "$W/probe_actual.txt"
[ "$(wc -l < "$W/probe_actual.txt")" -eq "$(wc -l < "$W/probe_expected.txt")" ] || { echo "rendering: expected $(wc -l < "$W/probe_expected.txt") lines, got $(wc -l < "$W/probe_actual.txt")"; exit 1; }
sort "$W/probe_expected.txt" > "$W/e.txt"; sort "$W/probe_actual.txt" > "$W/a.txt"
if diff "$W/e.txt" "$W/a.txt"; then echo "rendering: SQL Server text equals the CSV text for $(wc -l < "$W/e.txt") cells"; else echo "rendering: DIFFERENCES"; exit 1; fi
echo "== probe: the left join statuses, asserted"
$SQL -d ahah -W -h -1 -s '|' -Q "
SET NOCOUNT ON;
DECLARE @cohort TABLE (pseudo_id int, DataZone2011Code nvarchar(20));
INSERT INTO @cohort VALUES (1, 'S01006506'), (2, NULL), (3, ''), (4, 'S01013482'), (5, 'X99'), (6, ' s01008132 '), (7, 'S01006506'), (8, '   ');
SELECT c.pseudo_id, ISNULL(CONVERT(varchar(11), a.ahah_rnk), 'NULL'),
       CASE WHEN c.DataZone2011Code IS NULL OR LTRIM(RTRIM(c.DataZone2011Code)) = N'' THEN N'no_code'
            WHEN a.datazone_code IS NOT NULL THEN N'matched'
            WHEN v.datazone_code IS NOT NULL THEN N'other_vintage'
            ELSE N'not_a_datazone' END AS ahah_status
FROM @cohort AS c
LEFT JOIN ahah_datazone AS a ON a.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND a.ahah_version = N'4'
LEFT JOIN ahah_datazone AS v ON v.datazone_code = UPPER(LTRIM(RTRIM(c.DataZone2011Code))) AND v.ahah_version = N'5.1'
ORDER BY c.pseudo_id;" > "$W/join_raw.txt"
sed 's/ *|/|/g; s/ *$//' "$W/join_raw.txt" | { grep -v '^$' || true; } > "$W/join_actual.txt"
[ "$(wc -l < "$W/join_actual.txt")" -eq 8 ] || { echo "join: expected 8 lines, got $(wc -l < "$W/join_actual.txt")"; exit 1; }
printf '1|1001|matched\n2|NULL|no_code\n3|NULL|no_code\n4|NULL|other_vintage\n5|NULL|not_a_datazone\n6|3561|matched\n7|1001|matched\n8|NULL|no_code\n' > "$W/join_expected.txt"
if diff "$W/join_expected.txt" "$W/join_actual.txt"; then echo "join: 8 cohort rows returned once each with the expected status"; else echo "join: DIFFERENCES"; exit 1; fi
echo "== done; probe files in $W"
