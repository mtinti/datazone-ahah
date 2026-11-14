"""tools/restore_sources.py: a pinned file comes back from Zenodo only with its pinned hash, a file
already in place is never overwritten, and --check writes nothing. No test touches the network:
the downloads are replaced by local bytes."""

import hashlib
import importlib.util
import io
import shutil
import subprocess
import sys
import urllib.error
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("restore_sources", ROOT / "tools" / "restore_sources.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

GOOD, OTHER = b"the pinned bytes\n", b"other bytes\n"
sha = lambda b: hashlib.sha256(b).hexdigest()


@pytest.fixture
def remote(monkeypatch):
    """What Zenodo would serve, by URL, and a record of every download asked for."""
    served, asked = {}, []

    def download(url, target, token=None):
        asked.append((url, token))
        Path(target).write_bytes(served[url])

    monkeypatch.setattr(tool, "download", download)
    return served, asked


def tree(root: Path) -> dict:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def item(dest="a/file.csv", content=GOOD, **how):
    return dict({"dest": dest, "hash": sha(content), "algorithm": "sha256", "source": "the test record", "url": "u1"}, **how)


def test_a_missing_file_is_restored_when_its_hash_is_the_pinned_one(tmp_path, remote):
    served, asked = remote
    served["u1"] = GOOD
    counts = tool.restore([item()], tmp_path, check=False, token=None, log=lambda *a: None)
    assert counts == {"present": 0, "restored": 1, "would restore": 0}
    assert tree(tmp_path) == {"a/file.csv": GOOD}


def test_bytes_that_are_not_the_pinned_ones_are_refused_and_nothing_is_left(tmp_path, remote):
    served, _ = remote
    served["u1"] = OTHER
    with pytest.raises(tool.Stop, match="is not the pinned file"):
        tool.restore([item()], tmp_path, check=False, token=None, log=lambda *a: None)
    assert tree(tmp_path) == {}, "no file and no partial file under the source folder"


def test_a_file_in_place_with_another_hash_stops_the_run_and_is_not_touched(tmp_path, remote):
    served, asked = remote
    served["u1"] = GOOD
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "file.csv").write_bytes(OTHER)
    with pytest.raises(tool.Stop, match="exists and is not the pinned file"):
        tool.restore([item()], tmp_path, check=False, token=None, log=lambda *a: None)
    assert tree(tmp_path) == {"a/file.csv": OTHER} and asked == [], "left as it was, and nothing was downloaded over it"


def test_a_file_in_place_with_the_pinned_hash_is_not_downloaded_again(tmp_path, remote):
    served, asked = remote
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "file.csv").write_bytes(GOOD)
    counts = tool.restore([item()], tmp_path, check=False, token=None, log=lambda *a: None)
    assert counts["present"] == 1 and asked == []


def test_check_writes_nothing_under_the_source_folder(tmp_path, remote):
    served, asked = remote
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as z:
        z.writestr("folder/inside/list.dbf", GOOD)
    served.update(u1=GOOD, z1=packed.getvalue())
    (tmp_path / "kept.txt").write_bytes(b"already here")
    before = tree(tmp_path)
    items = [item(), {"dest": "lists/list.dbf", "hash": sha(GOOD), "algorithm": "sha256", "source": "a zip", "zip_url": "z1", "member": "list.dbf"}]
    counts = tool.restore(items, tmp_path, check=True, token=None, log=lambda *a: None)
    assert counts == {"present": 0, "restored": 0, "would restore": 2} and len(asked) == 2
    assert tree(tmp_path) == before and sorted(p.name for p in tmp_path.iterdir()) == ["kept.txt"], "not even an empty folder"
    # The same items without --check do write, so the check exercised the real path.
    tool.restore(items, tmp_path, check=False, token=None, log=lambda *a: None)
    assert tree(tmp_path) == dict(before, **{"a/file.csv": GOOD, "lists/list.dbf": GOOD})


def test_check_stops_on_a_wrong_hash_too(tmp_path, remote):
    served, _ = remote
    served["u1"] = OTHER
    with pytest.raises(tool.Stop):
        tool.restore([item()], tmp_path, check=True, token=None, log=lambda *a: None)
    assert tree(tmp_path) == {}


def test_a_zip_member_is_found_by_name_and_two_of_the_same_name_are_refused(tmp_path, remote):
    served, _ = remote
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, "w") as z:
        z.writestr("one/list.dbf", GOOD)
        z.writestr("two/list.dbf", OTHER)
    served["z1"] = packed.getvalue()
    with pytest.raises(tool.Stop, match="holds 2 members named list.dbf"):
        tool.restore([{"dest": "list.dbf", "hash": sha(GOOD), "algorithm": "sha256", "source": "a zip", "zip_url": "z1", "member": "list.dbf"}],
                     tmp_path, check=False, token=None, log=lambda *a: None)
    assert tree(tmp_path) == {}


@pytest.mark.skipif(shutil.which("bsdtar") is None, reason="bsdtar is needed to make and read a 7z archive")
def test_members_of_a_restored_archive_are_extracted_and_checked(tmp_path, remote):
    served, asked = remote
    work = tmp_path / "work"
    work.mkdir()
    (work / "2008.csv").write_bytes(GOOD)
    (work / "note.pdf").write_bytes(OTHER)
    subprocess.run(["bsdtar", "-a", "-cf", "release.7z", "2008.csv", "note.pdf"], cwd=work, check=True)
    archive = (work / "release.7z").read_bytes()
    served["u1"] = archive
    root = tmp_path / "sources"
    items = [item(dest="rel/release.7z", content=archive, auth=True),
             {"dest": "rel/note.pdf", "hash": sha(OTHER), "algorithm": "sha256", "source": "release.7z", "archive": "rel/release.7z", "member": "note.pdf"},
             {"dest": "rel/extracted/2008.csv", "hash": sha(GOOD), "algorithm": "sha256", "source": "release.7z", "archive": "rel/release.7z", "member": "2008.csv"}]
    # With --check the archive is never put in place, and its members are still verified.
    assert tool.restore(items, root, check=True, token="secret-token", log=lambda *a: None)["would restore"] == 3
    assert not root.exists()
    assert tool.restore(items, root, check=False, token="secret-token", log=lambda *a: None)["restored"] == 3
    assert tree(root) == {"rel/release.7z": archive, "rel/note.pdf": OTHER, "rel/extracted/2008.csv": GOOD}
    # The token goes only to the item that needs it.
    assert asked == [("u1", "secret-token"), ("u1", "secret-token")]
    # A member whose bytes are not the pinned ones stops the run and leaves the member out.
    shutil.rmtree(root)
    items[2]["hash"] = sha(b"not these")
    with pytest.raises(tool.Stop, match="rel/extracted/2008.csv"):
        tool.restore(items, root, check=False, token="secret-token", log=lambda *a: None)
    assert "rel/extracted/2008.csv" not in tree(root)


def test_a_refused_record_is_reported_without_the_token(monkeypatch, capsys, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("a-very-secret-token\n")

    def refused(token=None):
        assert token == "a-very-secret-token"
        raise urllib.error.HTTPError("https://zenodo.org/api/deposit/depositions/1?access_token=x", 403, "Forbidden", None, None)

    monkeypatch.setattr(tool, "plan", refused)
    assert tool.main(["--token-file", str(token_file), "--root", str(tmp_path / "sources")]) == 1
    out = capsys.readouterr()
    assert "Zenodo answered 403" in out.err and "a-very-secret-token" not in out.err + out.out and "access_token" not in out.err
    assert not (tmp_path / "sources").exists()


def test_the_plan_pins_by_sha256_and_takes_the_md5_of_zenodo_for_the_rest(monkeypatch):
    import yaml
    registry = yaml.safe_load(tool.REGISTRY.read_text())
    pins = tool.pinned(registry)
    assert len(pins) == 12 and all(len(v) == 64 for v in pins.values())
    files = [{"key": p.replace("/", "__"), "checksum": "md5:" + "0" * 32, "links": {"self": "https://zenodo.example/" + p}} for p in pins]
    files.append({"key": "geods__a_document.pdf", "checksum": "md5:" + "a" * 32, "links": {"self": "https://zenodo.example/doc"}})
    monkeypatch.setattr(tool, "zenodo_json", lambda url, token=None: {"files": files})
    items = {i["dest"]: i for i in tool.plan()}
    assert len(items) == 13
    for path, pin in pins.items():
        assert items[path]["algorithm"] == "sha256" and items[path]["hash"] == pin
    assert items["geods/a_document.pdf"]["algorithm"] == "md5" and items["geods/a_document.pdf"]["hash"] == "a" * 32
    # A record that lacks a pinned file is refused before anything is fetched.
    monkeypatch.setattr(tool, "zenodo_json", lambda url, token=None: {"files": files[1:]})
    with pytest.raises(tool.Stop, match="does not hold"):
        tool.plan()
