"""Hash-bound original documentation, with exact defining-API retrieval.

Manifest locators resolve against the config root. Every payload locator resolves
against the manifest directory, so relocating a config never changes its corpus.
Legacy projects without a manifest keep their historical ingestion protocol.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate original-document manifest key: {key}")
        result[key] = value
    return result


def load_original_documents(root, files):
    """Return a verified bundle or None; never skip, guess, or truncate inputs."""
    locator = files.get("original_doc_manifest")
    if not locator:
        return None
    path = (Path(root) / locator).resolve()
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != files.get("original_doc_manifest_sha256"):
        raise ValueError(f"Original-document manifest checksum mismatch: {path}")
    data = json.loads(content, object_pairs_hook=_unique_object)
    if data.get("schema") != "aideal.original-documents/v1":
        raise ValueError("Unsupported original-document manifest schema")
    for field in ("library", "source_version", "source_commit", "source_tree", "scope"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"Original-document manifest requires {field}")
    documents, targets = data.get("documents"), data.get("targets")
    if not isinstance(documents, list) or not documents or not isinstance(targets, dict):
        raise ValueError("Original-document manifest requires documents and targets")
    paths = [path]
    texts = {}

    def payload(row):
        if not isinstance(row, dict) or not row.get("path") or not row.get("sha256"):
            raise ValueError("Original-document payload requires path and sha256")
        source = (path.parent / row["path"]).resolve()
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Original-document payload checksum mismatch: {source}")
        text = raw.decode("utf-8")
        if not text.strip():
            raise ValueError(f"Original-document payload is empty: {source}")
        paths.append(source)
        return text

    for row in documents:
        key = row.get("id")
        if not isinstance(key, str) or not key or key in texts:
            raise ValueError("Original-document IDs must be nonempty and unique")
        if row.get("kind") not in ("rendered_api", "original_markdown", "original_rst", "api_reference"):
            raise ValueError(f"Unreviewed original-document kind: {row.get('kind')}")
        texts[key] = payload(row)
    shared_ids = data.get("shared_document_ids", [])
    if (not isinstance(shared_ids, list) or not all(isinstance(key, str) for key in shared_ids)
            or len(shared_ids) != len(set(shared_ids)) or any(key not in texts for key in shared_ids)):
        raise ValueError("shared_document_ids must list unique declared original-document IDs")
    shared_text = "\n\n".join(f"===== Shared original document: {key} =====\n{texts[key]}"
                               for key in shared_ids)
    target_texts = {}
    for api, row in targets.items():
        if not isinstance(api, str) or ":" not in api or not isinstance(row, dict):
            raise ValueError("Original-document targets require qualified API IDs")
        status = row.get("status")
        excerpts = row.get("excerpts", [])
        if status not in ("documented", "undocumented", "unresolved") or not isinstance(excerpts, list):
            raise ValueError(f"Invalid documentation disposition for {api}")
        if status == "documented" and not excerpts:
            raise ValueError(f"Documented target has no excerpts: {api}")
        if status != "documented" and (not row.get("reason") or excerpts):
            raise ValueError(f"{api}: {status} needs a reason and no attributed excerpts")
        chunks = []
        for excerpt in excerpts:
            if excerpt.get("document_id") not in texts:
                raise ValueError(f"Unknown excerpt document_id for {api}")
            body = payload(excerpt)
            # Only exact whole-document equality permits deduplication. A
            # substring or a name mention is never a coverage/matching claim.
            if excerpt["document_id"] in shared_ids and body == texts[excerpt["document_id"]]:
                continue
            label = excerpt.get("origin_url") or excerpt["document_id"]
            anchor = excerpt.get("anchor") or ""
            chunks.append(f"===== {label}{'#' + anchor if anchor else ''} =====\n{body}")
        target_texts[api] = "\n\n".join(chunks)
    corpus = "\n\n".join(f"===== {row['id']} =====\n{texts[row['id']]}" for row in documents)
    return {"manifest": data, "path": path, "sha256": digest,
            "documents": [(path.parent / row["path"]).resolve() for row in documents],
            "paths": list(dict.fromkeys(paths)), "text": corpus, "target_texts": target_texts,
            "shared_document_ids": shared_ids, "shared_text": shared_text}


def original_documents(cfg):
    bundle = load_original_documents(cfg.root, (cfg.raw or {}).get("files", {}))
    codebase = (cfg.raw or {}).get("codebase", {})
    if bundle is not None and codebase.get("api_inventory"):
        raw = (Path(cfg.root) / codebase["api_inventory"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != codebase.get("api_inventory_sha256"):
            raise ValueError("Original documentation requires an unchanged API inventory")
        inventory = json.loads(raw)
        for field in ("source_commit", "source_tree", "source_version"):
            if inventory.get(field) != bundle["manifest"][field]:
                raise ValueError(f"Original documentation/API inventory mismatch: {field}")
    return bundle


def original_document_paths(cfg):
    bundle = original_documents(cfg)
    return bundle["paths"] if bundle else list(cfg.original_readme_files)


def original_target_texts(cfg, names, limit=None):
    """Exact reviewed excerpts; unresolved/missing mappings block model input."""
    bundle = original_documents(cfg)
    if bundle is None:
        raise ValueError("Qualified documentation requires files.original_doc_manifest")
    result = {}
    for api in names:
        row = bundle["manifest"]["targets"].get(api)
        if row is None or row.get("status") == "unresolved":
            raise ValueError(f"Original documentation mapping unresolved for {api}")
        text = bundle["target_texts"][api] if row["status"] == "documented" else (
            f"No documented original API excerpt for `{api}` in the reviewed corpus. "
            f"Disposition: undocumented. {row['reason']}")
        if bundle["shared_text"]:
            text = "\n\n".join(part for part in (bundle["shared_text"], text) if part)
        if limit and len(text) > limit:
            raise ValueError(f"Original documentation for {api} exceeds explicit budget: "
                             f"{len(text)} > {limit}; revise the reviewed retrieval scope or budget")
        result[api] = text
    return result
