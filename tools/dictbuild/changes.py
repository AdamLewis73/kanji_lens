"""Build the `changes` table by diffing key sets between builds (D-39).

A saved study item references the dictionary by its natural key, (text, reading)
— never by row id (D-11). That key is far more stable than a row number but not
immutable: JMdict editors merge, split and correct entries, and when a key
retires, a user's saved word stops resolving.

D-40 says that card must still render. This is what lets it say *"merged into
上手 (じょうず)"* rather than *"no longer in the dictionary"*.

The table is DERIVED, not accumulated. Each build compares its own keys against
the previous SHIPPED build's, so nothing carries forward except a key list —
about a megabyte compressed — and the dictionary stays disposable (D-38).

Promoting a build to shipped:

    cp data/build/keys.tsv.gz baseline/keys.tsv.gz   # then commit it
"""

from __future__ import annotations

import gzip
import sqlite3
from collections import Counter
from pathlib import Path


def write_keys(db: sqlite3.Connection, path: Path) -> int:
    """Emit this build's key list. ent_seq travels with it because it is how a
    retired key's successor gets found — see _successor()."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        for text, reading, ent_seq in db.execute(
            "SELECT text, reading, ent_seq FROM word ORDER BY text, reading"
        ):
            fh.write(f"{text}\t{reading}\t{ent_seq}\n")
            n += 1
    return n


def _read_keys(path: Path) -> dict[tuple[str, str], int]:
    out = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            text, reading, ent_seq = line.rstrip("\n").split("\t")
            out[(text, reading)] = int(ent_seq)
    return out


def _successor(key: tuple[str, str], ent_seq: int,
               by_seq: dict[int, list[tuple[str, str]]]) -> tuple[str, str] | None:
    """Where a retired key most plausibly went.

    JMdict does not record merges, so this is a heuristic on the entry id the key
    used to belong to. If that entry still produces keys, prefer one sharing the
    written form (a reading was corrected), then one sharing the reading (a
    spelling was corrected), then anything from that entry.

    Returning None is a normal outcome — the entry itself may be gone — and the
    UI says "no longer in the dictionary" for those (D-40).
    """
    candidates = by_seq.get(ent_seq)
    if not candidates:
        return None
    return (
        next((c for c in candidates if c[0] == key[0]), None)
        or next((c for c in candidates if c[1] == key[1]), None)
        or candidates[0]
    )


def diff(db: sqlite3.Connection, baseline: Path, build_id: str) -> Counter:
    stats = Counter()

    if not baseline.exists():
        # Expected on a first build, and on any clone that has not shipped yet.
        # An empty changes table is correct here, not a failure.
        stats["baseline_absent"] = 1
        return stats

    old = _read_keys(baseline)
    new: dict[tuple[str, str], int] = {}
    by_seq: dict[int, list[tuple[str, str]]] = {}
    for text, reading, ent_seq in db.execute("SELECT text, reading, ent_seq FROM word"):
        new[(text, reading)] = ent_seq
        by_seq.setdefault(ent_seq, []).append((text, reading))

    stats["baseline_keys"] = len(old)
    stats["current_keys"] = len(new)
    stats["added"] = len(new.keys() - old.keys())

    rows = []
    for key, ent_seq in old.items():
        if key in new:
            continue
        stats["retired"] += 1
        succ = _successor(key, ent_seq, by_seq)
        if succ:
            stats["with_successor"] += 1
        rows.append((key[0], key[1], succ[0] if succ else None,
                     succ[1] if succ else None, build_id))

    db.executemany(
        "INSERT OR REPLACE INTO changes (old_text, old_reading, new_text,"
        " new_reading, build_id) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    return stats
