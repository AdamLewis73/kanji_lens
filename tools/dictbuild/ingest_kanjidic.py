"""Parse KANJIDIC2 into the `kanji` table.

First parser in the pipeline, and deliberately so: it is small, self-contained,
and it produces the on/kun reading lists that the JmdictFurigana alignment step
later matches surface readings against (D-52).

Four things in this file exist because inspection found them, not because the
documentation mentioned them:

  * <meaning> carries French, Spanish and Portuguese alongside English.
    English is the elements with NO m_lang attribute.
  * <stroke_count> may appear several times. The first is the accepted count;
    later ones are documented common miscounts, not alternatives (V-09).
  * <nanori> holds name-only readings. Mixing them into kun'yomi would teach
    readings that never appear in ordinary text.
  * grade, radical and jlpt are present and deliberately not ingested
    (D-50, D-42).
"""

from __future__ import annotations

import gzip
import json
import sqlite3
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import kana


def _dedupe(items: list[str]) -> list[str]:
    """Order-preserving. A character with several <rmgroup> elements can repeat
    a reading across them."""
    seen, out = set(), []
    for i in items:
        if i and i not in seen:
            seen.add(i)
            out.append(i)
    return out


def _character(el: ET.Element) -> dict:
    literal = el.findtext("literal")
    misc = el.find("misc")

    # findtext returns the FIRST match, which is exactly what V-09 requires.
    stroke_count = int(misc.findtext("stroke_count"))
    freq = misc.findtext("freq")

    on: list[str] = []
    kun: list[str] = []
    meanings: list[str] = []

    for group in el.findall("reading_meaning/rmgroup"):
        for r in group.findall("reading"):
            if r.get("r_type") == "ja_on":
                on.append(r.text)
            elif r.get("r_type") == "ja_kun":
                kun.append(r.text)
        for m in group.findall("meaning"):
            if m.get("m_lang") is None:      # no attribute == English
                meanings.append(m.text)

    # <nanori> sits outside <rmgroup> and is intentionally not read.

    return {
        "char": literal,
        "meanings": _dedupe(meanings),
        "on_readings": _dedupe(on),
        "kun_readings": _dedupe(kun),
        "stroke_count": stroke_count,
        "freq_rank": int(freq) if freq else None,
    }


def parse(path: Path):
    """Stream <character> elements. KANJIDIC2 is ~13k entries, but streaming
    keeps the shape identical to the much larger JMdict parser that follows."""
    with gzip.open(path, "rb") as fh:
        for _, el in ET.iterparse(fh, events=("end",)):
            if el.tag != "character":
                continue
            yield _character(el)
            el.clear()


def ingest(db: sqlite3.Connection, path: Path) -> Counter:
    stats = Counter()
    rows = []

    for k in parse(path):
        stats["kanji"] += 1
        if not k["meanings"]:
            stats["no_english_meaning"] += 1
        if k["freq_rank"]:
            stats["ranked"] += 1

        # D-37's premise is that KANJIDIC2 already stores on'yomi in katakana and
        # kun'yomi in hiragana. Assert it rather than trust it — a silent flip
        # would put every reading group header in the wrong script.
        #
        # on'yomi: expected to be 100% katakana. Any violation is a real problem.
        for r in k["on_readings"]:
            if not kana.is_katakana(r):
                stats["on_not_katakana"] += 1

        # kun'yomi: expected hiragana, with ~60 legitimate exceptions. Japanese
        # writes LOANWORDS in katakana, and KANJIDIC2 correctly preserves that
        # for kanji whose word-level reading is a loanword — Meiji-era unit ateji
        # (粁 キロメートル, 吋 インチ, 瓩 キログラム) and chemical elements
        # (鋁 アルミニウム, 鉑 プラチナ).
        #
        # These are NOT errors and must NOT be converted: 志 (freq 823) reads
        # シリング, and rendering that as しりんぐ would be wrong. See V-24.
        for r in k["kun_readings"]:
            if not kana.is_hiragana(r):
                stats["kun_katakana_loanword"] += 1

        rows.append((
            k["char"],
            json.dumps(k["meanings"], ensure_ascii=False),
            json.dumps(k["on_readings"], ensure_ascii=False),
            json.dumps(k["kun_readings"], ensure_ascii=False),
            k["stroke_count"],
            k["freq_rank"],
        ))

    db.executemany(
        "INSERT INTO kanji (char, meanings, on_readings, kun_readings,"
        " stroke_count, freq_rank) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    return stats
