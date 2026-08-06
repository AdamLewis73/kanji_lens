#!/usr/bin/env python3
"""Print representative samples of each raw source, so the schema can be written
against the real data instead of against documentation.

Deliberately does NOT parse XML. At this stage raw text is more informative —
it shows exactly what is in the file, including the parts a parser would quietly
normalise away. Parsing comes after the schema is settled.

Usage:
    python inspect_sources.py              # everything
    python inspect_sources.py jmdict       # one section (repeatable)
"""

from __future__ import annotations

import bz2
import gzip
import sys
from pathlib import Path

RAW = Path(__file__).parent / "data" / "raw"
RULE = "=" * 72

# Windows consoles default to cp1252, which cannot encode kana or kanji. Every
# script in this project prints Japanese, so force UTF-8 rather than working
# around it per-call.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def opener(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    if path.suffix == ".bz2":
        return bz2.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def head(path: Path, n: int, label: str) -> None:
    print(f"\n{RULE}\n{label}  —  first {n} lines\n{RULE}")
    with opener(path) as fh:
        for i, line in enumerate(fh):
            if i >= n:
                break
            print(line.rstrip())


def jmdict(path: Path, targets: list[str], label: str, max_lines: int = 55) -> None:
    """Stream <entry> blocks; print the first entry matching each target, and
    count how often the restriction elements actually appear."""
    print(f"\n{RULE}\n{label}  —  entry structure\n{RULE}")

    wanted = {t: None for t in targets}
    counts = {"entry": 0, "re_restr": 0, "stagk": 0, "stagr": 0,
              "ke_pri": 0, "re_pri": 0, "example": 0}
    block: list[str] = []
    inside = False

    with opener(path) as fh:
        for line in fh:
            for key in counts:
                if key != "entry" and f"<{key}>" in line:
                    counts[key] += line.count(f"<{key}>")
            if "<entry>" in line:
                inside, block = True, []
            if inside:
                block.append(line.rstrip())
            if "</entry>" in line:
                inside = False
                counts["entry"] += 1
                text = "\n".join(block)
                for t in wanted:
                    if wanted[t] is None and f"<keb>{t}</keb>" in text:
                        wanted[t] = text

    for t, text in wanted.items():
        print(f"\n--- {t} ---")
        if text is None:
            print("    (not found)")
            continue
        lines = text.splitlines()
        print("\n".join(lines[:max_lines]))
        if len(lines) > max_lines:
            print(f"    ... [{len(lines) - max_lines} more lines]")

    print(f"\n--- element counts across the whole file ---")
    for k, v in counts.items():
        print(f"    {k:10} {v:>8,}")


def kanjidic(path: Path, chars: list[str]) -> None:
    print(f"\n{RULE}\nKANJIDIC2  —  character entries\n{RULE}")
    wanted = {c: None for c in chars}
    block: list[str] = []
    inside = False

    with opener(path) as fh:
        for line in fh:
            if "<character>" in line:
                inside, block = True, []
            if inside:
                block.append(line.rstrip())
            if "</character>" in line:
                inside = False
                text = "\n".join(block)
                for c in wanted:
                    if wanted[c] is None and f"<literal>{c}</literal>" in text:
                        wanted[c] = text

    for c, text in wanted.items():
        print(f"\n--- {c} ---")
        print(text if text else "    (not found)")


def grep(path: Path, needles: list[str], label: str, limit: int = 3) -> None:
    print(f"\n{RULE}\n{label}\n{RULE}")
    found = {n: [] for n in needles}
    with opener(path) as fh:
        for line in fh:
            for n in needles:
                if len(found[n]) < limit and line.startswith(n + "|"):
                    found[n].append(line.rstrip())
    for n, lines in found.items():
        print(f"\n--- {n} ---")
        print("\n".join(lines) if lines else "    (not found)")


SECTIONS = {
    "jmdict": lambda: jmdict(RAW / "JMdict_e.gz", ["上手", "明日", "生"], "JMdict_e"),
    "kanjidic": lambda: kanjidic(RAW / "kanjidic2.xml.gz", ["生"]),
    "furigana": lambda: grep(RAW / "JmdictFurigana.txt",
                             ["先生", "明日", "学校", "花火", "一生"],
                             "JmdictFurigana  —  alignment format"),
    "kanjivg": lambda: head(RAW / "kanjivg-20250816.xml.gz", 30, "KanjiVG"),
    "tanaka": lambda: head(RAW / "examples.utf.gz", 12, "Tanaka Corpus (examples.utf)"),
    "examp": lambda: jmdict(RAW / "JMdict_e_examp.gz", ["生"], "JMdict_e_examp", 80),
    "tatoeba": lambda: head(RAW / "jpn_sentences.tsv.bz2", 6, "Tatoeba jpn_sentences"),
}


def main() -> int:
    wanted = sys.argv[1:] or list(SECTIONS)
    unknown = set(wanted) - set(SECTIONS)
    if unknown:
        print(f"unknown section(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        print(f"available: {', '.join(SECTIONS)}", file=sys.stderr)
        return 2
    for name in wanted:
        SECTIONS[name]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
