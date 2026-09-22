"""Deterministic hosted-document snapshots driven entirely by configuration."""

from __future__ import annotations

import hashlib
import io
import json
import re
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path

from .config import AidealConfig


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.skip += 1
        elif not self.skip and tag in {"p", "div", "section", "article", "li",
                                       "h1", "h2", "h3", "h4", "pre", "br", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1
        elif not self.skip and tag in {"p", "div", "section", "article", "li",
                                       "h1", "h2", "h3", "h4", "pre", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self) -> str:
        text = "".join(self.parts).replace("\r", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare_original_docs(cfg: AidealConfig) -> dict:
    """Download configured ZIP archives, extract text, and freeze one bundle.

    Configuration lives at ``files.original_doc_archives``. This function has
    no project/domain branches; each item declares only URL, label and optional
    expected archive SHA-256.
    """
    files_cfg = cfg.raw.get("files", {}) or {}
    archives = files_cfg.get("original_doc_archives", []) or []
    if not archives:
        raise ValueError("files.original_doc_archives is empty")
    output = (cfg.root / files_cfg.get(
        "original_doc_snapshot", ".aideal_original_docs/hosted_docs.md")).resolve()
    chunks: list[str] = []
    manifest = {"archives": [], "output": str(output.relative_to(cfg.root))}
    for index, item in enumerate(archives):
        if not isinstance(item, dict) or not item.get("url"):
            raise ValueError("each original_doc_archives item requires a url")
        url = str(item["url"])
        label = str(item.get("label") or f"archive-{index + 1}")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "AIDEAL-document-snapshot/1.0 (+reproducible research)"},
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            payload = response.read()
        archive_sha = _sha(payload)
        expected = str(item.get("sha256") or "")
        if expected and archive_sha != expected:
            raise ValueError(f"{label} SHA-256 mismatch: {archive_sha} != {expected}")
        converted = []
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            names = sorted(n for n in zf.namelist()
                           if n.lower().endswith((".html", ".htm", ".md", ".rst", ".txt"))
                           and not n.endswith("/"))
            for name in names:
                raw = zf.read(name).decode("utf-8", "ignore")
                if name.lower().endswith((".html", ".htm")):
                    parser = _Text(); parser.feed(raw); text = parser.text()
                else:
                    text = raw.strip()
                if text:
                    converted.append((name, text))
                    chunks.append(f"===== {label}: {name} =====\n{text}")
        manifest["archives"].append({
            "label": label, "url": url, "sha256": archive_sha,
            "text_files": len(converted),
        })
    bundle = ("\n\n".join(chunks) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bundle)
    manifest["bundle_sha256"] = _sha(bundle)
    manifest["bundle_bytes"] = len(bundle)
    mpath = (cfg.root / files_cfg.get(
        "original_doc_manifest", "docs/original_docs_snapshot.json")).resolve()
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {**manifest, "manifest": str(mpath)}
