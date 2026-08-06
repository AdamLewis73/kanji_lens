# dictbuild

Builds `kanjilens.db`, the read-only dictionary shipped as an Android asset (D-10).

Desktop Python, stdlib only, no install step. Contains no Android code and needs no emulator — the point is to de-risk the whole data layer before any Android work starts.

## Usage

```bash
python fetch.py            # download sources listed in sources.json
python fetch.py --list     # show the manifest without downloading
python fetch.py --force    # re-download even if already present
```

Downloads land in `data/raw/`, which is gitignored for now. What was actually fetched is recorded in `sources.lock.json`.

## Why the lock file exists

Three of the five sources — JMdict, KANJIDIC2, and the Tanaka Corpus — are published at fixed URLs and regenerated continuously. JMdict is rebuilt daily. **A past version cannot be requested**, so the URL alone identifies nothing.

Each of those files carries its generation date in its own header, and that is the real version identifier. `fetch.py` extracts it and records it alongside the SHA-256.

Note the checksum changes every day whether or not any content did, because the generation date is written into the file. A checksum proves two files differ; it cannot tell you whether anything meaningful changed.

The remaining two sources (KanjiVG, JmdictFurigana) are immutable GitHub release assets, pinned by tag and verified against the publisher's own SHA-256.

## Refresh policy (D-41)

At defined events only: phase start, before first release, and once per release. Never mid-phase.

The cost of refreshing rises sharply after launch — before release nothing can break, afterwards a refresh can orphan a user's saved words (D-39, D-40).

## Open

`sources.json` lists **three candidates** for example sentences. Which one wins should be settled by looking at the real files, not from documentation. See `docs/data-model.md`.
