"""Parse KanjiVG into the `strokes` table.

Mechanically the simplest parser here. Each <kanji> holds <path> elements in
drawing order, nested inside <g> groups that describe the character's component
structure — we want the paths flattened, in document order, and nothing else.

Stroke-order animation is then rendering those paths sequentially with an
animated dash offset. No video, no sprite sheet.

Two things to get right:

  * Variant ids (kvg:kanji_04e00-Kaisho and friends) are calligraphic
    alternates. Only the base form is ingested.
  * The path count MUST equal KANJIDIC2's stroke count (V-09). A mismatch means
    the SVG was read wrongly, and the animation would still play and still look
    like handwriting — which is exactly why this needs an assertion rather than
    an eyeball.
"""

from __future__ import annotations

import gzip
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# kvg:kanji_0751f          -> base form, wanted
# kvg:kanji_04e00-Kaisho   -> calligraphic variant, skipped
_KANJI_ID = re.compile(r"^kvg:kanji_([0-9a-f]+)$")

# KanjiVG stores coordinates to two decimals on a 109-unit canvas. The second
# decimal is 0.009% of the canvas — well under a tenth of a pixel at any size a
# phone renders — so it is precision nobody can see, costing 19% of the path data.
_DECIMAL = re.compile(r"\d+\.\d+")


def _round_coords(d: str) -> str:
    return _DECIMAL.sub(
        lambda m: f"{float(m.group()):.1f}".rstrip("0").rstrip("."), d)


def parse(path: Path):
    """Yield (character, [path data strings in stroke order])."""
    with gzip.open(path, "rb") as fh:
        for _, el in ET.iterparse(fh, events=("end",)):
            if el.tag != "kanji":
                continue
            m = _KANJI_ID.match(el.get("id", ""))
            if m:
                # iter() walks the whole subtree in document order, which
                # flattens the component <g> nesting back into stroke order.
                paths = [_round_coords(p.get("d"))
                         for p in el.iter("path") if p.get("d")]
                yield chr(int(m.group(1), 16)), paths
            el.clear()


def ingest(db: sqlite3.Connection, path: Path) -> Counter:
    stats = Counter()
    expected = dict(db.execute("SELECT char, stroke_count FROM kanji"))

    rows = []
    for char, paths in parse(path):
        stats["kanjivg_entries"] += 1
        if char not in expected:
            # KanjiVG covers punctuation and characters KANJIDIC2 does not.
            stats["not_in_kanjidic"] += 1
            continue
        if not paths:
            stats["no_paths"] += 1
            continue

        stats["ingested"] += 1
        if len(paths) != expected[char]:
            # V-09. Recorded rather than raised so one bad character does not
            # stop a build, but the count is bounded in build.py.
            stats["stroke_count_mismatch"] += 1

        rows.append((char, json.dumps(paths, ensure_ascii=False)))

    db.executemany(
        "INSERT OR REPLACE INTO strokes (kanji_char, svg_paths) VALUES (?, ?)", rows
    )
    stats["kanji_without_strokes"] = len(expected) - stats["ingested"]
    return stats
