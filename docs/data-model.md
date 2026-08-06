# Data Model

Read `overview.md` first if you're new — it defines the Japanese-language terms used here.

## Datasets

All free. All require attribution — see the bottom of this file.

| Dataset | Provides | Format | License |
|---|---|---|---|
| **JMdict** | Japanese-English word entries: writings, readings, senses, part of speech, frequency tags | Large XML, gzipped | CC BY-SA (EDRDG) |
| **KANJIDIC2** | Per-kanji data: meanings, on/kun readings, stroke count, school grade, official radical, frequency rank | XML, gzipped — 13,108 kanji | CC BY-SA (EDRDG) |
| **KanjiVG** | Stroke order paths | **One combined XML**, gzipped | CC BY-SA |
| **JmdictFurigana** | Per-character reading alignment — **internal index only**, D-13 | Text or JSON, one entry per line | Derived, CC BY-SA |
| **Example sentences** | Japanese sentences with English translations | Three candidate sources — see below | CC-BY |
| **KRADFILE** | Kanji → its visual components | Text | CC BY-SA (EDRDG) — **deferred**, see `roadmap.md` |

### Where they come from

Confirmed August 2026. Acquisition and refresh policy is D-41.

| Dataset | Source | Versioning |
|---|---|---|
| JMdict | `ftp.edrdg.org/pub/Nihongo/JMdict_e.gz` | **None** — regenerated daily at a fixed URL |
| KANJIDIC2 | `edrdg.org/kanjidic/kanjidic2.xml.gz` | **None** — fixed URL |
| KanjiVG | GitHub `KanjiVG/kanjivg` releases | Tagged, immutable, SHA-256 published (3.6 MB gzipped) |
| JmdictFurigana | GitHub `Doublevil/JmdictFurigana` releases | Tagged, immutable, SHA-256 published (5.2 MB gzipped) |
| Tanaka Corpus | EDRDG — ~150,000 edited sentence pairs | Loose |

Two practical consequences, both feeding D-41:

- **Three of five sources have no version history.** A past version of JMdict cannot be requested. Reproducing an old build requires having kept the file.
- **The generation date is written into each EDRDG file's header**, so the checksum changes daily whether or not any content did. Pin by header date; a checksum detects difference, not meaningful change.

**Internal file structure is still unverified.** URLs, formats, licensing and versioning are confirmed; the actual element shapes are not. Phase 1's first task remains downloading and examining the real files before writing parsing code.

### Example sentences — three candidates, decide after inspection

`data-model.md` originally named Tatoeba. That predates knowing the alternatives, and the choice should be settled by looking at the files:

| Candidate | Why it might win |
|---|---|
| **Tatoeba** (raw) | Largest and most current, but sentences are not linked to dictionary words — we would have to match them ourselves |
| **Tanaka Corpus** (`examples.utf`) | ~150,000 *edited* pairs, and words were extracted per sentence during its compilation — potentially giving word↔sentence links for free |
| **`JMdict_e_examp.gz`** | A JMdict variant with examples attached; if they are attached per *sense*, that is finer-grained than anything we could reconstruct |

Download all three; the difference should be obvious within minutes of looking.

### Notes on specific datasets

**A JMdict entry is not a word.** One `<entry>` holds several kanji writings *and* several readings, plus explicit restrictions between them — `re_restr` limits a reading to particular writings, and `stagk` / `stagr` limit an individual *sense* to particular writings or readings.

Expanding an entry into `(text, reading)` rows by naive cross-product therefore **invents words that do not exist and attaches meanings to the wrong reading.** Senses must hang off the expanded row, not off the entry. V-02 (上手) is the case that catches this.

**JMdict frequency tags.** Entries carry priority markers (`nf01`–`nf48`, `news1`, `ichi1`, `spec1`) indicating how common a word is. These are **not optional** — they're what makes example lists useful. An unranked list of words containing 生 surfaces obscure vocabulary first and makes the app feel broken.

Note these live on **writing and reading elements separately** (`ke_pri`, `re_pri`), not on the entry, so `word_frequency` needs a stated derivation rule rather than a guess. Proposed: take the best `nf##` band available across the writing and reading elements, falling back to `ichi1` / `news1` / `spec1`. V-04 depends on whatever rule is chosen.

**KANJIDIC2 details that affect the schema.**

- **Stroke count may have several values** — the first is the accepted count, later ones are common miscounts. V-09 compares this against KanjiVG's path count and must name *which*.
- **`nanori`** are name-only readings. They must not be mixed into kun'yomi display, or the app will teach readings that never appear in ordinary text.
- **A frequency ranking exists** for the 2,501 most common kanji (by occurrence in Mainichi Shimbun). Useful for ordering; worth ingesting.
- **The `jlpt` field is the pre-2010 test** and is deliberately not ingested — see D-42.

**KanjiVG structure.** Distributed as a **single combined XML file** (~3.6 MB gzipped), not as eleven thousand individual SVGs — earlier drafts of this document said otherwise. Each character contains one `<path>` element per stroke, in correct drawing order. Stroke-order animation is therefore rendering those paths sequentially with an animated stroke-dash offset — not a video, not a sprite sheet. Roughly 200 lines of Compose once the data is loaded.

**JmdictFurigana purpose.** It records that in 先生, 先 carries せん and 生 carries せい. This is never shown to the user (D-06), but it is what allows example words to be grouped by which reading a kanji carries (D-04). See D-13.

**Kana script normalization (D-37).** The sources disagree on script, and the ingest must reconcile them deliberately:

| Source | Stores readings as |
|---|---|
| KANJIDIC2 | on'yomi in katakana, kun'yomi in hiragana — matches the target convention |
| JmdictFurigana | hiragana throughout, since furigana is conventionally hiragana |

Reading group labels must display on'yomi in **katakana** and kun'yomi in **hiragana**, so JmdictFurigana's hiragana readings need converting to katakana wherever the reading is an on'yomi — determined by cross-referencing KANJIDIC2's reading lists for that kanji. Furigana rendered over words remains hiragana regardless (D-14); the two conventions are separate and must not be conflated.

## Two databases (D-09)

### Dictionary DB — read-only, shipped as an asset

Built by a desktop Python script (D-10) and loaded via Room's `createFromAsset`. Replaced wholesale on app upgrade, so it **never needs a migration** — if the schema changes, regenerate the file and swap it. Do not build migration machinery for this database.

Draft schema. Expect revision once the real source files have been inspected:

```
kanji
  char              PK, the character itself: 生
  meanings          English glosses
  on_readings       katakana: セイ, ショウ
  kun_readings      hiragana: い(きる), う(まれる), なま — excludes nanori
  stroke_count      the FIRST KANJIDIC2 value; later ones are miscounts
  freq_rank         Mainichi Shimbun rank, top 2,501 only; null otherwise
  grade             school year taught, if any
  radical           the official indexing radical
                    (no jlpt column — D-42)

word
  id                internal only — NEVER referenced from user data (D-11)
  text              先生
  reading           せんせい
  ent_seq           JMdict's own entry id; a lookup hint, not an identity

word_sense
  word_id, gloss, part_of_speech, sense_order

word_frequency
  word_id, rank     derived from JMdict priority tags

kanji_in_word       ← from JmdictFurigana; powers D-04 and the Examples tab
  kanji_char        生
  word_id
  reading_of_kanji  セイ  — which reading this kanji carries in THIS word

example
  word_id, japanese, english

strokes
  kanji_char, svg_paths

changes             ← D-39; merged and removed entries
  old_text, old_reading      the key that no longer resolves
  new_text, new_reading      where it went, if anywhere
  build_id                   which build it disappeared in

meta                ← one row; lets the app detect an asset upgrade
  build_id                   this dictionary's own version
  built_at
  source_versions            header date + checksum per dataset (D-41)
```

`kanji_in_word` is the table that answers *"show me every common word where 生 is read セイ."* It is queried constantly and rendered never.

`changes` is **derived** — recomputed each build by comparing this build's `(text, reading)` key set against the previous shipped build's. It accumulates nothing, so the dictionary stays disposable (D-38). The only artifact carried between builds is the previous key list.

### User DB — writable, irreplaceable

Every table follows D-15 (UUID keys), D-16 (`updated_at` + soft delete), and D-24 (image paths, not blobs).

```
study_item
  id            UUID PK                          (D-15)
  type          WORD | KANJI                     (D-27 — v1 always writes WORD)
  text          先生
  reading       せんせい  — part of the identity  (D-12)
  ent_seq       hint only, never the identity    (D-11)
  snapshot_gloss  the gloss line as displayed at save time, ~80 chars.
                  READ ONLY WHEN LIVE LOOKUP FAILS               (D-43)
  created_at, updated_at, deleted_at             (D-16)
  UNIQUE(text, reading, type)

srs_state                                        one row per study_item (D-29)
  study_item_id      FK
  due_at             when this item should next be reviewed
  stability          FSRS: days until recall probability falls to ~90%
  difficulty         FSRS: intrinsic difficulty of this item, ~1–10
  review_count
  last_reviewed_at   FSRS needs elapsed time since this to compute recall

review_log
  id UUID, study_item_id
  rating             the user's self-assessment: Again | Hard | Good | Easy
  reviewed_at, elapsed_ms
                     kept as history so the schedule can be recomputed if
                     the algorithm is ever retuned or replaced

saved_list
  id UUID, name, created_at, updated_at, deleted_at

list_membership                                  join table (D-28)
  list_id, study_item_id, added_at

scan
  id UUID, created_at
  raw_ocr_text       kept per D-22's "capture cheap metadata now"
  image_path         RELATIVE path (D-24)
  image_type         FULL_FRAME | WORD_CROP      (D-23)
  app_version        which build created this record

scan_word            links a scanned word to where it appeared
  scan_id, study_item_id
  bbox_x, bbox_y, bbox_w, bbox_h                 (D-22)
  char_offset, char_length
```

**`srs_state` hangs off `study_item`, not off `list_membership`.** That is D-29, and it is the difference between a correct scheduler and one that reviews the same word twice because it lives in two lists.

## The two identity rules

These are the failure modes most likely to corrupt data silently — no crash, no error message, just wrong content appearing months later.

**1. Never reference dictionary rows from user data (D-11).**
A saved item pointing at `dictionary_word_id = 48123` breaks the moment the dictionary is regenerated, because that row number may now hold a different word. Store the text and reading; re-resolve against the dictionary at read time.

**2. Identity is (text, reading), never text alone (D-12).**
上手 is じょうず (skilled), うわて (upper hand), and かみて (stage left) — three distinct vocabulary items a learner must be able to study separately.

### When the key stops resolving

The natural key is far more stable than a row number, but it is not immutable — a corrected reading or a merged entry can retire one. Three mechanisms handle that, and they are deliberately independent:

| | |
|---|---|
| **D-40** | The card renders regardless. An unresolvable item never silently disappears from a list. |
| **D-43** | `snapshot_gloss` gives that card a meaning to show, and keeps it reviewable. |
| **D-39** | The `changes` table upgrades *"no longer in the dictionary"* to *"merged into 上手 (じょうず)"*. |

Only the third depends on the dictionary. The first two hold even if `changes` is empty or missing.

Note the risk profile shifts over time: before release nothing can break, because nobody has saved anything. Afterwards a refresh can orphan real saved words — which is why D-41 refreshes at defined events rather than casually.

## Migrations

Android preserves internal storage and databases across app updates automatically. Uninstalling wipes them. So the risk to user data is **schema changes**, not updates in themselves.

- **`fallbackToDestructiveMigration()` is banned in all build types (D-17).** It resolves missing-migration crashes by deleting the entire user database. It appears throughout online tutorials because it makes the development crash disappear, and it is the most common way Android apps destroy production data.
- **Schema export on, JSON committed to git (D-18).** Room can emit a description of each schema version; committing them lets migrations be written against ground truth rather than memory.
- `AutoMigration` handles simple cases (added column, added table) via annotation. Hand-write anything else.
- **Test with `MigrationTestHelper`, including multi-version chains.** A user on v1.0 installing v1.4 runs 1→2→3→4 in sequence. Never assume the prior installed version was the immediately preceding release.
- Migrations are forward-only.

## Backup

**Android Auto Backup** — a platform feature that backs an app's data up to the user's Google Drive and restores it when they set up a new device. Free, but two constraints matter:

- **The per-app quota is 25 MB.** The dictionary DB and saved images must be excluded via `data_extraction_rules`, or backups silently fail. Only the user DB should be included.
- It can restore an **old** database into a **newer** app version, so migrations must handle arriving from any prior schema version, not just the most recent one.

**Manual export/import (D-20)** — an in-app action producing a versioned JSON or zip through Android's share sheet or file picker, importable on a fresh install or another device. Include a format version field from the very first release, so future importers can recognize and upgrade older files.

Beyond user value, this is the recovery path if a production migration ever fails, and its serialization format is effectively the payload a future sync service would send (D-19).

## Attribution

The CC BY-SA licenses on JMdict, KANJIDIC2, KanjiVG, and JmdictFurigana **require attribution in the shipped app.** This is a license obligation, not a courtesy.

Build the attribution screen early — it's easy to forget until release, and collecting the correct notices is a task best done while the datasets are being ingested in Phase 1.
