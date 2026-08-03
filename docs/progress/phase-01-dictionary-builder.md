# Phase 1 — Dictionary Builder

**Status:** not started
**Updated:** 2026-08-03

## Current state

Nothing built. Repo contains documentation only.

The goal of this phase is a desktop Python script that parses the source datasets into a single SQLite file (`kanjilens.db`) that ships as an Android asset. No Android work happens in this phase.

## Next action

Decide and write down the dictionary schema concretely (draft shape is in `docs/data-model.md`), then download the source datasets and inspect their actual structure before writing any parsing code.

## Done

- [ ] Source datasets downloaded and inspected
- [ ] Schema finalized
- [ ] JMdict parser (words, senses, part of speech, priority tags)
- [ ] KANJIDIC2 parser (meanings, on/kun, stroke count, JLPT, grade, radical)
- [ ] JmdictFurigana ingest → `kanji_in_word` table
- [ ] Kana script normalization: on'yomi → katakana, kun'yomi → hiragana (D-37)
- [ ] KanjiVG ingest → stroke paths
- [ ] Tatoeba ingest → example sentences
- [ ] Frequency ranking derived from JMdict priority tags
- [ ] Indexes for lookup patterns (exact word, prefix/longest-match, kanji → words)
- [ ] Output size measured and recorded below
- [ ] Attribution text collected for the in-app licenses screen
- [ ] Verification cases V-01 – V-05 pass (`docs/verification.md`)

## Open questions

- **Tatoeba volume.** The full corpus is large. Cap examples per word (3–5?) and select by sentence length and vocabulary simplicity rather than taking the first N.
- **Final DB size.** Needs measuring. Combined with Kuromoji's IPADIC this drives APK size — if it's a problem, consider trimming rare JMdict entries or dropping low-frequency example sentences.
- **FTS5 or plain indexes?** Longest-match prefix lookup (D-07) may be served fine by a plain index on word text. Measure before adding FTS complexity.
- **Dictionary versioning.** The DB should carry a version/build-date row so the app can detect an asset upgrade. Trivial to add, easy to forget.

## Notes

- The dictionary DB is **read-only and disposable** (D-09). It never needs a migration — regenerate and replace the file. Do not add migration machinery here.
- **Never expose row IDs to user data** (D-11). User data references words by text + reading.
- `kanji_in_word` (from JmdictFurigana) is an **internal index only** (D-13). It powers "words grouped by reading" and the Examples tab; per-character readings are never rendered (D-06).
- Frequency ranking is not optional — unranked example lists surface obscure words and feel broken.
- **Kana script matters (D-37).** JmdictFurigana gives hiragana; on'yomi must be stored as katakana. Determining which readings are on'yomi requires cross-referencing KANJIDIC2. Getting this wrong renders every on'yomi group header in the wrong script.
- This script is the most portable asset in the project. It produces a plain SQLite file usable on Android, iOS, or anywhere else.
