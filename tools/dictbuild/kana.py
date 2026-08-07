"""Kana script helpers.

Japanese has two phonetic scripts covering the same sounds — hiragana (ひらがな)
and katakana (カタカナ) — laid out identically in Unicode, 0x60 apart. That makes
conversion a codepoint shift rather than a lookup table.

Script carries meaning in this project: on'yomi are written in katakana and
kun'yomi in hiragana (D-37), so converting between them is how a reading from
one source gets compared against a reading from another.
"""

from __future__ import annotations

HIRAGANA = ("ぁ", "ゖ")   # ぁ … ゖ
KATAKANA = ("ァ", "ヶ")   # ァ … ヶ
_SHIFT = 0x60


def to_katakana(s: str) -> str:
    """Hiragana → katakana. Anything else passes through untouched."""
    return "".join(
        chr(ord(c) + _SHIFT) if HIRAGANA[0] <= c <= HIRAGANA[1] else c for c in s
    )


def to_hiragana(s: str) -> str:
    """Katakana → hiragana. Anything else passes through untouched."""
    return "".join(
        chr(ord(c) - _SHIFT) if KATAKANA[0] <= c <= KATAKANA[1] else c for c in s
    )


def is_katakana(s: str) -> bool:
    """True if every kana character is katakana. Ignores non-kana (ー, ・, -)."""
    kana = [c for c in s if HIRAGANA[0] <= c <= HIRAGANA[1]
            or KATAKANA[0] <= c <= KATAKANA[1]]
    return bool(kana) and all(KATAKANA[0] <= c <= KATAKANA[1] for c in kana)


def is_hiragana(s: str) -> bool:
    """True if every kana character is hiragana. Ignores non-kana."""
    kana = [c for c in s if HIRAGANA[0] <= c <= HIRAGANA[1]
            or KATAKANA[0] <= c <= KATAKANA[1]]
    return bool(kana) and all(HIRAGANA[0] <= c <= HIRAGANA[1] for c in kana)


def strip_okurigana(reading: str) -> str:
    """KANJIDIC2 kun readings carry positional markers. Reduce to the part the
    kanji itself carries.

        い.きる  → い     '.' separates the okurigana that follows the kanji
        なま-    → なま   trailing '-' marks a prefix
        -う      → う     leading '-' marks a suffix
    """
    return reading.split(".")[0].strip("-")


def full_reading(reading: str) -> str:
    """The same reading with markers removed but okurigana kept: い.きる → いきる.

    JmdictFurigana sometimes attributes the whole inflected form to the kanji,
    so both this and strip_okurigana() are needed when matching (D-52).
    """
    return reading.replace(".", "").strip("-")
