# Phase 1 — Dictionary Builder

**Status:** not started (design settled, no code)
**Updated:** 2026-08-05

## Current state

Nothing built. Repo contains documentation only.

The goal of this phase is a desktop Python script that parses the source datasets into a single SQLite file (`kanjilens.db`) that ships as an Android asset. No Android work happens in this phase.

A long design session on 2026-08-05 settled the source-acquisition strategy, the change-tracking mechanism, and several dataset facts that were previously assumed. It produced D-38 through D-46 and V-17 through V-20. Nothing below should be re-litigated without reading those.

### Confirmed by research, not yet by inspection

URLs, formats, licensing and versioning are confirmed (`data-model.md`). **Internal element structure is not.** That's the next task and the reason no parser exists yet.

Two findings that changed the plan:

- **KanjiVG ships one combined XML** (~3.6 MB gzipped), not ~11,000 individual SVGs.
- **Three of five sources have no version history** — JMdict is regenerated daily at a fixed URL, and a past version cannot be requested. Their generation date is baked into the file header, so checksums change daily even when content doesn't.

## Next action

1. Create `tools/dictbuild/` with a fetch script and a pinned manifest (D-41).
2. Download all sources, **including all three example-sentence candidates**.
3. Measure the compressed sizes — this settles the open git question below.
4. Inspect real structure; write findings into this file before any parsing code.

## Done

- [ ] `tools/dictbuild/` skeleton and fetch script with pinned manifest (D-41)
- [ ] Source datasets downloaded and inspected; findings recorded here
- [ ] Example-sentence source chosen from the three candidates
- [ ] Schema finalized
- [ ] JMdict parser — entry expansion honouring `re_restr` / `stagk` / `stagr` (V-18)
- [ ] Frequency derivation rule stated and applied (V-04)
- [ ] KANJIDIC2 parser (meanings, on/kun, stroke count, grade, radical, freq rank; **no JLPT**, D-42)
- [ ] JmdictFurigana ingest → `kanji_in_word`
- [ ] Kana script normalization tolerant of rendaku and gemination (D-37, V-17)
- [ ] KanjiVG ingest → stroke paths
- [ ] Example sentences ingested, capped and ranked
- [ ] `meta` table with build id and per-source header dates (D-41)
- [ ] `changes` table + key-set diff against previous build (D-39, V-19)
- [ ] Indexes for lookup patterns (exact word, prefix/longest-match, kanji → words)
- [ ] Output size measured and recorded below
- [ ] Attribution text collected for the in-app licenses screen
- [ ] Verification cases V-01 – V-05 and V-17 – V-19 pass

## Open questions

- **Do the compressed source files go into git?** Leaning yes; deferred until the real sizes are known. Confirmed so far: KanjiVG 3.6 MB, JmdictFurigana 5.2 MB. If the full set lands under ~40 MB, committing them makes a fresh clone self-contained and keeps shipped builds reproducible — which matters because three sources have no version history. Raw data is gitignored **provisionally** until this is decided. Note the asymmetry: adding files to git later is trivial, removing them is not.
- **Which example-sentence source** — raw Tatoeba, Tanaka Corpus, or `JMdict_e_examp`. Decide by inspection.
- **Example volume.** Cap per word (3–5?) and select by sentence length and vocabulary simplicity rather than taking the first N.
- **Final DB size.** Needs measuring. Combined with Kuromoji's IPADIC this drives APK size — and ML Kit OCR is bundled by preference (D-46), which adds to it. If it's a problem, consider trimming rare JMdict entries or dropping low-frequency examples.
- **FTS5 or plain indexes?** Longest-match prefix lookup (D-07) may be served fine by a plain index on word text. Measure before adding FTS complexity.
- **Does the frequency derivation rule survive contact with the data?** `data-model.md` proposes best `nf##` across writing and reading elements, falling back to `ichi1`/`news1`/`spec1`. Confirm against real entries.

*Resolved since last update:* dictionary versioning (now the `meta` table); JLPT handling (D-42); refresh cadence (D-41); merge/removal handling (D-39, D-40, D-43).

## Notes

- The dictionary DB is **read-only and disposable** (D-09, D-38). It never needs a migration — regenerate and replace the file. Do not add migration machinery here. Stable dictionary-owned IDs were considered and rejected; D-38 records why, so it doesn't get re-proposed.
- **Never expose row IDs to user data** (D-11). User data references words by text + reading.
- `kanji_in_word` (from JmdictFurigana) is an **internal index only** (D-13). It powers "words grouped by reading" and the Examples tab; per-character readings are never rendered (D-06).
- Frequency ranking is not optional — unranked example lists surface obscure words and feel broken.
- **Kana script matters (D-37).** The hard part isn't the script conversion, it's deciding *which* readings are on'yomi when the surface kana has been altered by rendaku or gemination. 学校 = がっこう, not がくこう. See V-17 for the two silent failure modes.
- **A JMdict entry is not a word.** Expanding one into `(text, reading)` rows by cross-product invents words that don't exist. See V-18.
- This script is the most portable asset in the project. It produces a plain SQLite file usable on Android, iOS, or anywhere else.
