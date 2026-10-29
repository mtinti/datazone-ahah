"""The source registry: what is pinned, where it comes from, and how to verify it."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

from .checks import Report

PACKAGE = Path(__file__).resolve().parent.parent
ROOT = PACKAGE.parent
REGISTRY = PACKAGE / "sources.yaml"
SOURCE_ROOT = ROOT / "data" / "sources"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class Registry:
    path: Path
    sha256: str
    root: Path
    licence: str
    attribution: list
    publisher_pages: dict
    editions: tuple
    datazone_lists: dict

    def edition(self, version: str) -> dict:
        for ed in self.editions:
            if ed["version"] == version:
                return ed
        raise KeyError(version)


def load_registry(path: Path = REGISTRY, root: Path = SOURCE_ROOT) -> Registry:
    raw = yaml.safe_load(Path(path).read_text())
    if raw.get("version") != 1:
        raise ValueError(f"Unsupported registry version {raw.get('version')!r}")
    versions = [e["version"] for e in raw["editions"]]
    if len(set(versions)) != len(versions):
        raise ValueError("duplicate edition in the registry")
    return Registry(Path(path), sha256(path), Path(root), raw["licence"], list(raw["attribution"]),
                    dict(raw["publisher_pages"]), tuple(raw["editions"]), dict(raw.get("datazone_lists") or {}))


def verify(registry: Registry, report: Report) -> None:
    """Every pinned file is present with its pinned hash. A changed byte stops the build."""
    pins = []
    for ed in registry.editions:
        pins += [(ed["file"], ed["sha256"]), (ed["summary"], ed["summary_sha256"])]
    for vintage, spec in registry.datazone_lists.items():
        pins.append((spec["file"], spec["sha256"]))
    for rel, expected in pins:
        path = registry.root / rel
        if not path.is_file():
            report.add(f"source.{rel}", False, "missing")
            continue
        actual = sha256(path)
        report.equal(f"source.{rel}", actual, expected, detail="sha256 matches" if actual == expected else f"sha256 {actual[:16]} differs from pin")
    report.require()
