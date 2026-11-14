"""Restore the pinned source files of datazone-ahah from its Zenodo record.

    python tools/restore_sources.py            # put every missing file under data/sources/
    python tools/restore_sources.py --check    # write nothing there: show that each file can be restored

The record (the DOI is `zenodo_sources_doi` in ahah_ingest/sources.yaml) holds every file the
build reads, named <folder>__<file>. Each file the registry pins is checked against its SHA256.
The other files of the record, the publisher's documents and the SOURCES.md notes, are checked
against the MD5 that Zenodo records. The record is public, so no token is needed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "ahah_ingest" / "sources.yaml"
SOURCE_ROOT = ROOT / "data" / "sources"
ZENODO = "https://zenodo.org/api"


def pinned(registry: dict) -> dict:
    """{path under data/sources: sha256} for every file the registry pins."""
    pins = {}

    def walk(node):
        if isinstance(node, dict):
            if "file" in node and "sha256" in node:
                pins[node["file"]] = node["sha256"]
            for key, value in node.items():
                if isinstance(key, str) and key.endswith("_sha256") and key[:-7] in node:
                    pins[node[key[:-7]]] = value
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(registry)
    return pins


def plan(token=None) -> list:
    registry = yaml.safe_load(REGISTRY.read_text())
    record_id = registry["zenodo_sources_doi"].rsplit("zenodo.", 1)[1]
    record = zenodo_json(f"{ZENODO}/records/{record_id}", token)
    pins = pinned(registry)
    files = {f["key"]: f for f in record["files"]}
    missing = sorted(p for p in pins if p.replace("/", "__") not in files)
    if missing:
        raise Stop(f"Zenodo record {record_id} does not hold {', '.join(missing)}")
    items = []
    for key, f in sorted(files.items()):
        dest = key.replace("__", "/", 1)
        source = f"Zenodo record {record_id}"
        if dest in pins:
            items.append({"dest": dest, "hash": pins[dest], "algorithm": "sha256", "url": f["links"]["self"], "source": source})
        else:
            items.append({"dest": dest, "hash": f["checksum"].split(":", 1)[1], "algorithm": "md5", "url": f["links"]["self"], "source": source})
    return items


# --------------------------------------------------------------------------------------------
# Everything below is the same in datazone-ahah, uprn-epc and uprn-epc-nondomestic.
# --------------------------------------------------------------------------------------------

USER_AGENT = "restore-sources/1 (pinned source restore)"
CLOCKLESS_TIMEOUT = 300


class Stop(Exception):
    """The restore cannot go on. The message says which file and what to do."""


def digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_token(token_file) -> str | None:
    """The Zenodo token, from --token-file or the environment variable ZENODO_TOKEN. It is never
    printed and never written."""
    if token_file:
        return Path(token_file).expanduser().read_text().strip()
    return os.environ.get("ZENODO_TOKEN") or None


def open_url(url: str, token: str | None = None):
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=CLOCKLESS_TIMEOUT)


def download(url: str, target: Path, token: str | None = None) -> None:
    with open_url(url, token) as response, open(target, "wb") as fh:
        shutil.copyfileobj(response, fh, 1 << 20)


def zenodo_json(url: str, token: str | None = None) -> dict:
    with open_url(url, token) as response:
        return json.load(response)


def extract_zip_member(archive: Path, member: str, target: Path) -> None:
    """One member of a zip, found by its file name whatever folder it is in."""
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.rsplit("/", 1)[-1] == member]
        if len(names) != 1:
            raise Stop(f"{archive.name} holds {len(names)} members named {member}, expected one")
        with z.open(names[0]) as src, open(target, "wb") as fh:
            shutil.copyfileobj(src, fh, 1 << 20)


def extract_7z_member(archive: Path, member: str, target: Path) -> None:
    """One member of a 7z archive, with bsdtar (libarchive) or 7z, whichever is installed."""
    for command in (["bsdtar", "-xOf", str(archive), member], ["7z", "x", "-so", str(archive), member]):
        if shutil.which(command[0]) is None:
            continue
        with open(target, "wb") as fh:
            done = subprocess.run(command, stdout=fh, stderr=subprocess.PIPE)
        if done.returncode != 0:
            raise Stop(f"{command[0]} could not extract {member} from {archive.name}: {done.stderr.decode(errors='replace')[:200]}")
        return
    raise Stop("neither bsdtar nor 7z is installed. Install one (bsdtar comes with libarchive) and run again.")


def restore(items: list, root: Path, check: bool, token: str | None, log=print) -> dict:
    """Bring every item to its place under `root`, or, with `check`, only show that it could be.

    An item is a dict: `dest` (path under root), `hash` and `algorithm`, `source` (words for the
    messages), and one way to get the bytes: `url` (with `auth` when the token is needed),
    `zip_url` with `member`, or `archive` (the `dest` of an earlier item) with `member`.

    A file already in place with the pinned hash is left alone. A file in place with another hash
    stops the run and is not touched. New bytes are written to a temporary folder outside `root`,
    hashed there, and moved into place only when the hash is the pinned one. With `check` nothing
    is written under `root` at all.
    """
    counts = {"present": 0, "restored": 0, "would restore": 0}
    available = {}                      # dest -> where its verified bytes are, for archive members
    with tempfile.TemporaryDirectory(prefix="restore_sources_") as tmp:
        tmp = Path(tmp)
        for n, item in enumerate(items):
            dest = root / item["dest"]
            if dest.is_file():
                if digest(dest, item["algorithm"]) != item["hash"]:
                    raise Stop(f"{dest} exists and is not the pinned file ({item['algorithm']} differs). It was left as it is. "
                               "Move it away and run again.")
                available[item["dest"]] = dest
                counts["present"] += 1
                log(f"  present        {item['dest']}")
                continue
            staged = tmp / f"{n:03d}_{Path(item['dest']).name}"
            if "url" in item:
                download(item["url"], staged, token if item.get("auth") else None)
            elif "zip_url" in item:
                packed = tmp / f"{n:03d}_packed.zip"
                download(item["zip_url"], packed, token if item.get("auth") else None)
                extract_zip_member(packed, item["member"], staged)
                packed.unlink()
            else:
                if item["archive"] not in available:
                    raise Stop(f"{item['dest']} comes from {item['archive']}, which is not available")
                extract_7z_member(available[item["archive"]], item["member"], staged)
            got = digest(staged, item["algorithm"])
            if got != item["hash"]:
                staged.unlink()
                raise Stop(f"{item['dest']}: the copy from {item['source']} is not the pinned file "
                           f"({item['algorithm']} {got[:16]}, pinned {item['hash'][:16]}). Nothing was put in its place.")
            if check:
                available[item["dest"]] = staged          # kept until the end, for the members of an archive
                counts["would restore"] += 1
                log(f"  would restore  {item['dest']}  ({staged.stat().st_size:,} bytes, {item['algorithm']} matches, from {item['source']})")
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(staged), str(dest))
                available[item["dest"]] = dest
                counts["restored"] += 1
                log(f"  restored       {item['dest']}  ({dest.stat().st_size:,} bytes, from {item['source']})")
    return counts


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="write nothing under data/sources: fetch each missing file to a temporary folder, verify it, report")
    parser.add_argument("--root", type=Path, default=SOURCE_ROOT, help="the folder to restore into (default: data/sources)")
    parser.add_argument("--token-file", help="a file holding a Zenodo token, for a record whose files are not public")
    args = parser.parse_args(argv)
    try:
        token = read_token(args.token_file)
        items = plan(token)
        counts = restore(items, args.root, args.check, token)
    except Stop as stop:
        print(f"stopped: {stop}", file=sys.stderr)
        return 1
    except urllib.error.HTTPError as e:
        print(f"stopped: Zenodo answered {e.code} for {e.url.split('?')[0]}. A record whose files are not public needs "
              "--token-file or ZENODO_TOKEN, from an account that may read it.", file=sys.stderr)
        return 1
    print(", ".join(f"{v} {k}" for k, v in counts.items() if v) or "nothing to do")
    if args.check:
        print("check only: nothing was written under", args.root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
