#!/usr/bin/env python3
"""Build kanjilens.db from the raw sources.

The output is read-only, disposable, and rebuilt from scratch every run (D-09,
D-38). There is no migration path and none is wanted: if the schema changes,
edit schema.sql and run this again.

Usage:
    python build.py                    # full build
    python build.py --only kanjidic    # one stage (repeatable)
    python build.py --out path/to.db
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ingest_furigana
import ingest_jmdict
import ingest_kanjidic
import ingest_kanjivg

HERE = Path(__file__).parent
SCHEMA = HERE / "schema.sql"
LOCK = HERE / "sources.lock.json"
RAW = HERE / "data" / "raw"
DEFAULT_OUT = HERE / "data" / "build" / "kanjilens.db"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_lock() -> dict:
    if not LOCK.exists():
        sys.exit("sources.lock.json missing — run fetch.py first")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return {s["name"]: s for s in lock["sources"]}


def build_id(sources: dict) -> str:
    """Deterministic: identical sources produce an identical id, so a rebuild
    that changes nothing is visibly a rebuild that changed nothing."""
    digest = hashlib.sha256(
        "".join(s["sha256"] for s in sorted(sources.values(), key=lambda x: x["name"]))
        .encode()
    ).hexdigest()[:8]
    return f"{datetime.now(timezone.utc):%Y%m%d}-{digest}"


def create(out: Path) -> sqlite3.Connection:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)          # disposable — never migrated
    db = sqlite3.connect(out)
    db.executescript(SCHEMA.read_text(encoding="utf-8"))
    return db


def write_meta(db: sqlite3.Connection, sources: dict, bid: str) -> None:
    versions = {
        name: {"header_date": s.get("header_date"), "version": s.get("version"),
               "sha256": s["sha256"]}
        for name, s in sources.items()
    }
    db.execute(
        "INSERT OR REPLACE INTO meta (build_id, built_at, source_versions)"
        " VALUES (?, ?, ?)",
        (bid, datetime.now(timezone.utc).isoformat(timespec="seconds"),
         json.dumps(versions, ensure_ascii=False, sort_keys=True)),
    )


STAGES = {
    "kanjidic": (ingest_kanjidic.ingest, "kanjidic2"),
    "jmdict": (ingest_jmdict.ingest, "jmdict"),
    "furigana": (ingest_furigana.ingest, "jmdictfurigana"),
    "kanjivg": (ingest_kanjivg.ingest, "kanjivg"),
}

# Counters that mean something is wrong, with the bound at which to say so.
# A stat with a known non-zero expected value belongs here with its ceiling,
# not in the code as a silent tolerance.
BOUNDS = {
    "on_not_katakana": 0,            # D-37: on'yomi are katakana, no exceptions
    "kun_katakana_loanword": 100,    # ~60 expected — loanword ateji, see V-24
    "unmatched_pct": 4,              # D-52 measured 2.25%; V-22 fails above ~4%
    "stroke_count_mismatch": 150,    # ~109 expected — KanjiVG and KANJIDIC2 genuinely
                                     #   disagree on 辶 forms etc. Bound, not equality (V-09)
}


def _flag(key: str, value: int) -> str:
    limit = BOUNDS.get(key)
    return "   <-- OVER LIMIT" if limit is not None and value > limit else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--only", action="append", metavar="STAGE",
                    help=f"run one stage: {', '.join(STAGES)}")
    args = ap.parse_args()

    stages = args.only or list(STAGES)
    unknown = set(stages) - set(STAGES)
    if unknown:
        sys.exit(f"unknown stage(s): {', '.join(sorted(unknown))}")

    sources = load_lock()
    bid = build_id(sources)
    print(f"build {bid}\noutput {args.out}\n")

    db = create(args.out)
    write_meta(db, sources, bid)

    for name in stages:
        fn, source_name = STAGES[name]
        path = RAW / sources[source_name]["filename"]
        started = time.monotonic()
        print(f"{name}")
        stats = fn(db, path)
        db.commit()
        for k, v in stats.items():
            print(f"    {k:<26} {v:>9,}{_flag(k, v)}")
        print(f"    {'elapsed':<24} {time.monotonic() - started:>9.1f}s")

    # Bulk inserts leave free pages scattered through the file. The dictionary
    # ships in an APK, so a few megabytes for one command is worth taking.
    before = args.out.stat().st_size
    db.execute("VACUUM")
    db.close()
    after = args.out.stat().st_size
    print(f"\n{args.out.name}  {after / 1024 / 1024:.1f} MB"
          f"  (VACUUM reclaimed {(before - after) / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
