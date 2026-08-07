"""Parse JmdictFurigana into `kanji_in_word`, matching surface readings back to
dictionary readings.

The hardest correctness problem in Phase 1 (V-17, D-52), and the one with the
least forgiving failure mode: both ways of getting it wrong are silent.

JmdictFurigana records the kana a kanji carries AS IT APPEARS in a word:

    先生|せんせい|0:せん;1:せい
    学校|がっこう|0:がっ;1:こう      <- 学 is がく; gemination
    花火|はなび|0:はな;1:び          <- 火 is ひ;   rendaku
    明日|あした|0-1:あした           <- RANGE: jukujikun, no per-character reading

Matching that back to KANJIDIC2 decides which reading group a word joins, and
therefore what the kanji Examples tab shows (D-04). Match too strictly and
common words silently vanish from their group; too loosely and they file under
the wrong reading.

Spans that still do not match are written with canonical_reading and
reading_type NULL. They join no reading group and never surface — but they
remain COUNTABLE, which is what turns a silent failure into V-22's build check.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

import kana


def _load_readings(db: sqlite3.Connection) -> dict[str, dict]:
    """Per kanji: on readings (katakana), and kun readings indexed both by stem
    and by full form, since a surface reading may correspond to either."""
    out = {}
    for char, on_json, kun_json in db.execute(
        "SELECT char, on_readings, kun_readings FROM kanji"
    ):
        kun = json.loads(kun_json)
        by_stem: dict[str, list[str]] = {}
        by_full: dict[str, str] = {}
        for r in kun:
            by_stem.setdefault(kana.strip_okurigana(r), []).append(r)
            by_full[kana.full_reading(r)] = r
        out[char] = {"on": set(json.loads(on_json)), "stem": by_stem, "full": by_full}
    return out


def _following_kana(text: str, pos: int) -> str:
    """The okurigana trailing a kanji: everything kana from pos+1 up to the next
    non-kana character. 生きる at 0 -> きる;  生き物 at 0 -> き."""
    out = []
    for c in text[pos + 1:]:
        if kana.HIRAGANA[0] <= c <= kana.HIRAGANA[1]:
            out.append(c)
        else:
            break
    return "".join(out)


def match(surface: str, okurigana: str, readings: dict) -> tuple[str | None, str | None]:
    """Resolve a surface reading to (canonical_reading, 'on' | 'kun'), or
    (None, None) when nothing matches.

    Order matters. on'yomi is tried first because it accounts for ~69% of spans.
    The full kun form is tried before the bare stem so that 生きる resolves to
    い.きる rather than the ambiguous い, which 生 shares across い.きる,
    い.かす and い.ける.
    """
    candidates = kana.variants(surface)

    for c in candidates:
        k = kana.to_katakana(c)
        if k in readings["on"]:
            return k, "on"

    # A kun reading including its okurigana, either because the word supplies it
    # (生きる at position 0 -> い + きる) or because JmdictFurigana attributed the
    # whole inflected form to the kanji.
    for c in candidates:
        h = kana.to_hiragana(c)
        for full in ((h + okurigana) if okurigana else h, h):
            if full in readings["full"]:
                return readings["full"][full], "kun"

    for c in candidates:
        h = kana.to_hiragana(c)
        if h in readings["stem"]:
            forms = readings["stem"][h]
            # Unambiguous stem -> store the specific reading; otherwise the stem
            # itself, which is genuinely what the kanji carries.
            return (forms[0] if len(forms) == 1 else h), "kun"

    return None, None


def ingest(db: sqlite3.Connection, path: Path) -> Counter:
    stats = Counter()
    readings = _load_readings(db)

    words = {
        (t, r): wid
        for wid, t, r in db.execute("SELECT id, text, reading FROM word")
    }

    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("|")
            if len(parts) != 3:
                continue
            text, reading, spans = parts
            stats["lines"] += 1

            word_id = words.get((text, reading))
            if word_id is None:
                # JmdictFurigana is generated from JMdict but not in lockstep
                # with it; a handful of keys will not exist on our side.
                stats["no_matching_word"] += 1
                continue

            for span in spans.split(";"):
                index, _, surface = span.partition(":")
                if "-" in index:
                    # Jukujikun. The reading belongs to the whole word and splits
                    # across no character — inventing an alignment here would
                    # teach a false reading (V-03, D-06).
                    stats["jukujikun_skipped"] += 1
                    continue
                if not index.isdigit():
                    stats["malformed_span"] += 1
                    continue

                pos = int(index)
                if pos >= len(text):
                    stats["span_out_of_range"] += 1
                    continue
                char = text[pos]
                if char not in readings:
                    stats["char_not_in_kanjidic"] += 1
                    continue

                canonical, rtype = match(surface, _following_kana(text, pos),
                                         readings[char])
                stats["spans"] += 1
                stats[f"matched_{rtype}" if rtype else "UNMATCHED"] += 1
                if rtype and kana.to_hiragana(surface) != kana.to_hiragana(canonical):
                    stats["matched_after_normalization"] += 1

                # What D-04 groups by. on'yomi have no okurigana; kun readings
                # reduce to the part the kanji itself carries, so 生 in 生きる
                # (い.きる) and in 生き残り (い) land in the same group.
                group = None
                if rtype == "on":
                    group = canonical
                elif rtype == "kun":
                    group = kana.strip_okurigana(canonical)

                rows.append((char, word_id, pos, surface, canonical, group, rtype))

    db.executemany(
        "INSERT OR IGNORE INTO kanji_in_word (kanji_char, word_id, position,"
        " surface_reading, canonical_reading, reading_group, reading_type)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    stats["rows"] = db.execute("SELECT count(*) FROM kanji_in_word").fetchone()[0]
    if stats["spans"]:
        stats["unmatched_pct"] = round(100 * stats["UNMATCHED"] / stats["spans"], 2)
    return stats
