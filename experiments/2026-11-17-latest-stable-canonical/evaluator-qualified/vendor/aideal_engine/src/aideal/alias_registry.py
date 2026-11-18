"""Alias registry: tracks proposed AND added aliases, plus the agreed metrics.

aliases.json record:
  {"alias", "canonical", "model", "count", "status", "run_id", "added_at"}

status lifecycle: "proposed" (mined from errors or model usage)
               -> "added" (actually implemented in the codebase)

Metrics:
  histogram() - distinct aliases per canonical function
  overlap(a, b) - Jaccard overlap between two models' alias sets
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from .error_log import new_run_id


class AliasRegistry:
    def __init__(self, path: Path):
        self.path = path
        self.records: list[dict] = []
        if path.exists():
            self.records = json.loads(path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def _find(self, alias: str, canonical: str, model: str | None = None) -> dict | None:
        for r in self.records:
            if r["alias"] == alias and r["canonical"] == canonical and (model is None or r["model"] == model):
                return r
        return None

    def record_use(self, alias: str, canonical: str, model: str) -> dict:
        """A model used/proposed `alias` for `canonical` (status stays proposed)."""
        r = self._find(alias, canonical, model)
        if r:
            r["count"] += 1
        else:
            r = {"alias": alias, "canonical": canonical, "model": model,
                 "count": 1, "status": "proposed", "run_id": new_run_id(), "added_at": ""}
            self.records.append(r)
        self.save()
        return r

    def mark_added(self, alias: str, canonical: str) -> dict:
        """Track that this alias was actually ADDED to the codebase."""
        r = self._find(alias, canonical)
        if r is None:
            r = {"alias": alias, "canonical": canonical, "model": "manual",
                 "count": 0, "status": "proposed", "run_id": new_run_id(), "added_at": ""}
            self.records.append(r)
        r["status"] = "added"
        r["added_at"] = time.strftime("%Y%m%d-%H%M%SZ", time.gmtime())
        self.save()
        return r

    # -- metrics ------------------------------------------------------------

    def histogram(self) -> dict[str, int]:
        per_fn: dict[str, set[str]] = defaultdict(set)
        for r in self.records:
            per_fn[r["canonical"]].add(r["alias"])
        return {fn: len(a) for fn, a in sorted(per_fn.items())}

    def overlap(self, model_a: str, model_b: str) -> dict:
        a = {(r["alias"], r["canonical"]) for r in self.records if r["model"] == model_a}
        b = {(r["alias"], r["canonical"]) for r in self.records if r["model"] == model_b}
        inter, union = a & b, a | b
        return {
            "model_a": model_a, "model_b": model_b,
            "a_size": len(a), "b_size": len(b),
            "intersection": len(inter),
            "jaccard": round(len(inter) / len(union), 3) if union else 0.0,
            "shared": sorted(f"{al} -> {cn}" for al, cn in inter),
        }

    def report(self) -> dict:
        usage = Counter()
        for r in self.records:
            usage[r["alias"]] += r["count"]
        return {
            "total_records": len(self.records),
            "added": [r for r in self.records if r["status"] == "added"],
            "proposed": [r for r in self.records if r["status"] == "proposed"],
            "models": sorted({r["model"] for r in self.records}),
            "alias_histogram_per_function": self.histogram(),
            "top_aliases_by_use": usage.most_common(20),
        }
