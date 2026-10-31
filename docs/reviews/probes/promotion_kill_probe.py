"""Kill the build process between two promotion renames, then show that results/ is refused
until recovery finishes the promotion forward. Run: python3 docs/reviews/probes/promotion_kill_probe.py

A child process runs promote() with os.replace slowed after the first swap; the parent sends
SIGKILL (no Python handler can run). Expected: a mixture plus the journal on disk, nothing
deleted, verify_results refuses, recover completes, verify_results passes with the new files.
"""
import json, os, signal, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from ahah_ingest.pipeline import JOURNAL, OUTPUTS, ResultsIncomplete, recover, verify_results

CHILD = r'''
import os, sys, time
sys.path.insert(0, sys.argv[1])
from ahah_ingest.pipeline import OUTPUTS, promote
real = os.replace
swapped = []
def slow(src, dst):
    real(src, dst)
    if str(src).endswith(".new"):
        swapped.append(dst)
        if len(swapped) == 1:
            open(sys.argv[3], "w").write("first swap done")
            time.sleep(60)
os.replace = slow
from pathlib import Path
promote(Path(sys.argv[2]) / ".staging_1", Path(sys.argv[2]), OUTPUTS)
'''
with tempfile.TemporaryDirectory() as d:
    results, staging = Path(d) / "results", Path(d) / "results" / ".staging_1"
    staging.mkdir(parents=True)
    for n in OUTPUTS:
        (results / n).write_text(f"old {n}"); (staging / n).write_text(f"new {n}")
    flag = Path(d) / "flag"
    child = subprocess.Popen([sys.executable, "-c", CHILD, str(ROOT), str(results), str(flag)])
    for _ in range(100):
        if flag.exists(): break
        time.sleep(0.1)
    assert flag.exists(), "child never reached the first swap"
    os.kill(child.pid, signal.SIGKILL); child.wait()
    print("child killed with", -child.returncode)
    on_disk = {p.name: p.read_text() for p in results.iterdir() if p.is_file()}
    assert on_disk[OUTPUTS[0]] == f"new {OUTPUTS[0]}" and on_disk[OUTPUTS[1]] == f"old {OUTPUTS[1]}", on_disk
    assert (results / JOURNAL).exists() and all((results / f"{n}.new").exists() for n in OUTPUTS[1:])
    print("on disk after the kill: a mixture, the journal, and every remaining .new file; nothing deleted")
    try:
        verify_results(results, files=False); raise SystemExit("verify_results accepted a mixture")
    except ResultsIncomplete as e:
        print("verify_results refused:", e)
    print("recover:", recover(results))
    assert {p.name: p.read_text() for p in results.iterdir() if p.is_file()} == {n: f"new {n}" for n in OUTPUTS}
    (results / "manifest.json").write_text(json.dumps({"parquet": {"sha256": "x"}, "csv": {"file": OUTPUTS[1], "sha256": "y", "rows": 0}, "built_at": "t"}))
    print("after recovery: the new generation only;", verify_results(results, files=False)["csv"]["rows"], "rows per manifest")
    print("PROBE PASSED")
