# Decisions

Every significant design decision for this project, with the reasoning behind it.

## How to use this file

**IDs are stable and permanent. Decisions are not.**

`D-01` will always refer to the same decision — the number is never reused or renumbered, so it stays a reliable reference in commit messages, code comments, and conversation ("implemented per D-12").

Decisions themselves are expected to change as the project learns things. When one does:

1. Edit the old entry to begin with `**SUPERSEDED by D-##**`, and **leave the rest of the text intact**.
2. Append the replacement with the next unused ID.
3. **Grep `verification.md` for the old decision's ID.** Verification cases cite the decisions they protect, so a grep for `D-12` finds every case that assumes it. Update or retire those cases in the same change.
4. Grep the rest of `docs/` for the ID too — decisions are referenced from `architecture.md`, `data-model.md`, `ux.md`, `roadmap.md`, and the progress files.

Never delete a decision. The reasoning behind a path that was later abandoned is often the most valuable thing here — it stops a future session from re-proposing something already ruled out, and it records *why* the situation changed.

Note that references are deliberately **one-directional**: other docs cite `D-##`, but decisions don't link back. Back-links would need maintaining in two places and would drift. Grep is the mechanism, and it stays correct for free.

**A decision recorded here reflects the current plan, which may be v1-only.** Several decisions deliberately scope to v1 while a later phase expands them. Where that's the case the entry says so and links the related decision. See `roadmap.md` for the deferred backlog.

**New to this project?** Read `overview.md` first — it has a worked end-to-end example and a glossary of the Japanese-language terms used throughout these docs.

## Index

Scan for the relevant entry rather than reading the whole file.

| ID | Decision | Area |
|---|---|---|
| D-01 | v1 study items are words; kanji-only items come later | Product |
| D-02 | Freeze-frame, not live overlay | Product |
| D-03 | Fully offline; no runtime LLM calls | Product |
| D-04 | Teach by example (words grouped by reading), not authored prose | Product |
| D-05 | Two detail screens: word → kanji drill-down | Product |
| D-06 | Component chips show meanings only, never readings | Product |
| D-07 | Kuromoji for segmentation + JMdict longest-match for alternates | Tokenization |
| D-08 | Tokenization behind a `Tokenizer` interface in `:domain` | Tokenization |
| D-09 | Two databases: read-only dictionary, writable user data | Data |
| D-10 | Dictionary built by a desktop Python script, not on-device | Data |
| D-11 | **Never store dictionary row IDs in user data** | Data |
| D-12 | **Identity is (text, reading), never text alone** | Data |
| D-13 | JmdictFurigana ingested as an index, never rendered | Data |
| D-14 | Furigana display is whole-word ruby only | Data |
| D-15 | **UUID primary keys on all user data** | Migrations |
| D-16 | **`updated_at` on every row; soft deletes only** | Migrations |
| D-17 | **`fallbackToDestructiveMigration()` banned in all build types** | Migrations |
| D-18 | Room schema export on; JSON committed to git | Migrations |
| D-19 | Design for sync now; build accounts later | Migrations |
| D-20 | Manual export/import ships before any sync | Migrations |
| D-21 | v1 saves downscaled full frames; word crops deferred | Images |
| D-22 | Store the word's bounding box from v1 regardless | Images |
| D-23 | Image format migrations never reprocess old records | Images |
| D-24 | Images are files on disk; DB stores relative paths | Images |
| D-25 | Scan history and saved-word images have separate lifecycles | Images |
| D-26 | FSRS, not SM-2 or a custom algorithm | SRS |
| D-27 | Study items polymorphic (`type`) from day one | SRS |
| D-28 | Saved lists are many-to-many via a join table | SRS |
| D-29 | **Scheduling belongs to the item; lists only filter** | SRS |
| D-30 | Peek sheet and word screen are one expanding component | UI |
| D-31 | Peek state only on the scan screen | UI |
| D-32 | Kanji screen swaps in place inside the sheet | UI |
| D-33 | Overlay dims the image; detected text stays bright | UI |
| D-34 | Bundle Noto Sans JP explicitly | UI |
| D-35 | Material 3 design tokens from the first UI commit | UI |
| D-36 | Three bottom-nav destinations: Scan · Saved · Review | UI |
| D-37 | Reading labels follow dictionary kana convention | UI / Data |

**Bold** entries are the ones whose violation causes silent data corruption or a forced rewrite. They are also listed in `CLAUDE.md`.

---

## Product

**D-01 — v1 study items are words; kanji-only items come later.**
An SRS card is a word (先生), tagged with its component kanji. Reviewing bare kanji in isolation would contradict the app's core claim that meaning is contextual — a flashcard reading "生 = life, birth" teaches exactly the thing the app exists to argue against.

This is a **v1 scope decision, not a permanent restriction.** Studying individual kanji is a wanted future feature; the user should be able to opt into it. **D-27** requires the data model to support kanji items from day one so that adding them later is a feature, not a migration. In other words: v1 *ships* words only, but v1 *stores data* as though both exist.

**D-02 — Freeze-frame, not live overlay.**
The live camera preview shows only a lightweight "Japanese text detected" indicator. The user presses the shutter, and every subsequent interaction — text highlighting, tapping, detail sheets — happens on the frozen still image rather than a moving feed.
*Why:* OCR bounding boxes recompute every frame on a live feed, so highlight rectangles jitter and tap targets move under the user's finger. A person also cannot hold a phone steady while reading a detail panel. A still image additionally permits a slower, more accurate OCR pass and pinch-to-zoom (which matters a great deal — see the tap-target problem in `ux.md`).
Google Translate does use a live overlay, but its use case is different: glance-and-replace, not sustained study of one image. A Translate-style approach (background freeze-frames with change detection) is deferred, not rejected — see `roadmap.md`.

**D-03 — Fully offline. No runtime LLM calls.**
Every core function works with no network connection. This rules out generating kanji explanations on demand from a language model. Two reasons: per-call cost the project doesn't want to carry, and the risk of confidently incorrect etymology being presented as fact in an app whose entire purpose is teaching.

**D-04 — v1 teaches by example, not by authored prose.**
The obvious way to explain why 生 means "teacher" inside 先生 is a written explanation. But no free dataset contains such explanations, authoring them for 2,000+ kanji is a content project rather than a code project, and generating them is ruled out by D-03.

Instead, the kanji screen shows **other common words containing that kanji, grouped by reading, sorted by frequency.** For 生:

> **セイ** — 先生 teacher · 学生 student · 生活 daily life
> **ショウ** — 一生 a lifetime · 誕生日 birthday
> **なま** — 生ビール draft beer
> **い(きる)** — 生きる to live

This teaches through pattern recognition rather than assertion, which is arguably *more* aligned with the product thesis than a paragraph of etymology would be. It generates automatically from JMdict (words and frequency) plus JmdictFurigana (which reading each kanji carries in each word — see D-13). Curated prose remains a possible later enhancement layered on top; see `roadmap.md`.

**D-05 — Two detail screen types, with drill-down.**
Tapping a word opens the **word screen**; tapping a component kanji on that screen opens the **kanji screen**, which has three tabs (Overview / Examples / Stroke Order).

*Why the split:* radicals, stroke order, and on'yomi/kun'yomi readings are all properties of a *single character*, not of a word. 先生 has no radical — 先 has one and 生 has one. An "on'yomi of 先生" is not a meaningful concept. Trying to present per-character data on a word screen produces either nonsense or awkward compromises.

Splitting them also mirrors the actual learning motion: *"what does this say?"* → *"why does it say that?"*

**D-06 — Component kanji chips show meanings only, never readings.**
On the word screen, 先生 displays chips for 先 (previous, ahead) and 生 (life, birth) — meanings only.

*Why:* showing a reading on each chip implies the word's reading splits cleanly per character. Often it does (先生 = せん + せい), but frequently it does not. 明日 is read あした as a whole word, with no part of that reading belonging to 明 or to 日 — this is called *jukujikun*. Displaying per-character readings would teach a false rule. Whole-word furigana (D-14) is the correct presentation.

Note this is a *display* decision only. Per-character reading data is still ingested and used internally — see D-13.

---

## Tokenization

> **Background for fresh sessions:** Japanese text has no spaces. `先生と生産について話した` is one unbroken run of characters. Before anything can be looked up in a dictionary, the text must be split into words — this is called **tokenization** or morphological analysis, and it is the technically central problem of this app. OCR is the comparatively easy part.

**D-07 — Kuromoji for primary segmentation, plus JMdict longest-match for alternates.**

Two complementary mechanisms, both required:

**Kuromoji** is a Japanese morphological analyzer (pure Java, Apache-2.0, ships its own IPADIC dictionary inside the JAR). Given a string it returns a single best-guess sequence of tokens with part-of-speech tags and readings. It correctly handles conjugated verbs (食べた → base form 食べる) and grammatical particles, which raw dictionary lookup cannot.

**JMdict longest-match** is a second pass over the same text using the dictionary the app already ships. For each starting character position, it queries the dictionary for every entry that matches from that position forward. At position 0 of `先生と生産`, it finds both 先 and 先生; the longest is the primary candidate, and the shorter ones are kept as alternates. This is the technique used by Japanese reader tools such as Yomichan, 10ten, and Rikaichan.

*Why both:* Kuromoji produces exactly one parse. But the entire pedagogical point of this app is that a run of characters contains overlapping words — that 先生 contains 先, that the user should be able to ask about either. Longest-match surfaces every candidate; Kuromoji supplies the grammatical correctness that pure lookup lacks. Together they also implement the compound-vs-word view without needing a multi-granularity tokenizer.

*Why not Sudachi* (the more modern alternative, which offers native multi-granularity splitting): it memory-maps its dictionary file, requiring an uncompressed file on disk — which on Android means extracting from assets on first launch, with progress UI, failure handling, and version migration. Its dictionary is roughly 3× larger, and Android usage is poorly documented, meaning early-adopter debugging. Deferred, not rejected — see `roadmap.md`.

**D-08 — Tokenization sits behind a `Tokenizer` interface in the domain layer.**
Keeps D-07 reversible, and keeps the JVM-only Kuromoji dependency out of portable code. Kuromoji cannot run on iOS; see the portability table in `architecture.md`.

---

## Data

**D-09 — Two separate databases: a read-only dictionary and a writable user database.**

The **dictionary DB** ships as a prebuilt file in the app's assets. It contains JMdict, KANJIDIC2, KanjiVG, and the rest. It is never written to at runtime.

The **user DB** contains saved words, lists, SRS state, and scan records. It is small and precious.

*Why separate:* the dictionary is disposable. When a new JMdict release comes out, the app replaces the whole file — no migration, no risk. User data is irreplaceable and evolves slowly under carefully written migrations. If they shared one database, every dictionary refresh would put the user's study history inside the blast radius of a schema change. Keeping them apart means dictionary updates can never harm user data.

**D-10 — The dictionary DB is built by a desktop Python script, not on-device.**
JMdict is a large XML file. Parsing it on first launch would take a long time and drain battery. Instead a script run on a development machine produces `kanjilens.db`, which is committed as an app asset.

Secondary benefit: this script and its output are the most portable assets in the project. A plain SQLite file works identically on Android, iOS, or desktop.

**D-11 — Never store dictionary row IDs in user data.**

If a saved word row contains `dictionary_word_id = 48123`, and the dictionary is later regenerated from a newer JMdict release, row 48123 may now be an entirely different word. Nothing crashes and no error appears — the user's saved list simply begins showing wrong words, potentially a year later.

Store the **natural key** instead: the word text plus its reading (先生 / せんせい), and re-resolve against the dictionary at read time. JMdict's `ent_seq` identifier may be stored as a *hint* to speed lookup, but it is not the identity — JMdict entries do occasionally get merged or split between releases.

**D-12 — Saved-item identity is (text, reading), never text alone.**

上手 has three readings with genuinely different meanings:

| Reading | Meaning |
|---|---|
| じょうず | skilled, good at |
| うわて | the upper hand, superior position |
| かみて | stage left, upstream |

These are separate vocabulary items and a learner must be able to save, study, and schedule them independently.

*Second benefit:* this makes an open UI question free to answer later. Whether the app shows one word screen with a reading selector, or presents three separate tappable entries, becomes a pure presentation choice changeable at any time — because the underlying data already distinguishes them. Had identity been text alone, splitting later would be impossible: existing saved rows would be ambiguous about which reading the user meant.

**D-13 — JmdictFurigana is ingested as an internal index, never rendered.**

[JmdictFurigana](https://github.com/Doublevil/JmdictFurigana) is a dataset providing per-character reading alignment — it records that in 先生, 先 carries せん and 生 carries せい.

D-06 says this is never *displayed*. But it is what makes D-04 possible: to group example words by which reading a kanji carries, something must know that 生 is セイ in 先生 and ショウ in 一生. That mapping cannot be computed; it must come from data.

So: ingested, indexed, queried constantly, shown to the user never.

**D-14 — Furigana display is whole-word ruby only.**
Reading kana render above the entire word as a unit — せんせい positioned over 先生, not せん over 先 and せい over 生. Correctly handles jukujikun (D-06) and keeps rendering simple.

---

## User data and migrations

> **Background:** Android preserves an app's internal storage and databases across app updates automatically. Uninstalling wipes them. So the danger to user data is not updates in themselves — it is **schema changes** made during an update, and the tooling's default behavior when a migration is missing.

**D-15 — UUID primary keys on all user data, never auto-increment integers.**
Two devices creating records while offline will both generate `id = 5`, and there is no way to reconcile them afterward. This is unfixable once real user data exists. UUIDs cost nothing now and are a precondition for the sync described in D-19.

**D-16 — Every user row carries `updated_at`; deletions are soft (`deleted_at`), never hard `DELETE`.**
`updated_at` is required for sync conflict resolution. Soft delete is required for deletion *propagation*: if phone A hard-deletes a record, tablet B has no way to learn that it was deleted — B simply observes that A is missing a record it has, and helpfully re-adds it. A tombstone row communicates the deletion.

**D-17 — `fallbackToDestructiveMigration()` is banned in every build type.**

Room versions the database schema. Increment the version without supplying a migration and the app crashes on launch. `fallbackToDestructiveMigration()` resolves that crash by **deleting the entire user database and recreating it empty.**

It appears in a large fraction of online tutorials because it makes the development-time crash go away, and it is the most common way Android apps silently destroy user data in production. It must not enter this codebase, including debug builds — the habit is the hazard.

**D-18 — Room schema export is on; the generated schema JSON is committed to git.**
Room can emit a JSON description of each schema version (`room.schemaLocation`). Committing these allows diffing versions against ground truth rather than memory when writing a migration, and enables `MigrationTestHelper` to test migrations against genuine historical schemas.

Migrations must be tested as **chains**, not single hops: a user on v1.0 who installs v1.4 runs 1→2→3→4 in sequence. Never assume the previous installed version was the immediately preceding release.

**D-19 — Design for sync now; build accounts later.**
A server-backed account with cross-device sync is a plausible future direction. Building it now would add authentication, privacy obligations, a Play Store data-safety declaration, and hosting cost — none of which help v1.

D-15, D-16, and the repository pattern (`architecture.md`) are the parts that are painful to retrofit. With them in place, adding sync later means writing a sync service. Without them it means rewriting the data layer and migrating every existing user.

**D-20 — Manual export/import ships before any sync.**
An in-app action that writes a versioned JSON or zip file and hands it to Android's share sheet or file picker, importable on a fresh install or a different device.

Beyond its direct user value, it earns its place early for two reasons: it is the recovery path if a production migration ever fails, and defining a clean serializable representation of all user data is precisely the payload a future sync API would send. Building export first is therefore a head start on D-19, not a detour from it.

---

## Images

**D-21 — v1 saves the downscaled full camera frame; word crops are deferred.**
Roughly 1600px on the long edge, WebP lossy quality 80, giving about 250–400 KB per image. Cropping to the specific word would be smaller and a better memory hook, but getting crop geometry right (coordinates, padding, edge cases at image boundaries) is fiddly work that shouldn't block v1.

**D-22 — Store the word's bounding box from v1 regardless.**
Four integers per scanned word. They are already available at scan time — the same data drives the tap overlay — so recording them is a schema field, not new work.

The payoff: moving to word crops later requires **no image reprocessing at all**. The location of the word inside each stored image is already known, so cropping can happen at display time, or lazily replace the file on next access. Without this, the upgrade would mean re-running OCR across every saved image, which is slow, battery-hungry, and awkward to present to the user.

*Generalized principle:* **capture cheap metadata now even when unused.** Bounding boxes, raw OCR text, token character offsets, and the app version that created each record all cost bytes and buy future options. Deriving them later means reprocessing; recording them now is a schema field.

**D-23 — Image format migrations never reprocess old records.**
Each image row carries an `image_type` discriminator (`FULL_FRAME` | `WORD_CROP`). Old records keep their original type forever; new records use the current one. The UI renders both. Mixed-format data is the normal, expected steady state — not a problem to be cleaned up.

**D-24 — Images are files on disk; the database stores relative paths.**
Filenames are UUIDs — never sequential, never derived from content — so collisions across migrations and imports are impossible. Paths are stored **relative** to the app's storage root, because the absolute path can change (across OS versions, backup restores, and device transfers).

Storing images as SQLite BLOBs would bloat the database file and slow every query that touches those rows, including queries that don't need the image.

**D-25 — Scan history and saved-word images have separate lifecycles.**
Images attached to saved study items persist indefinitely. Images from casual scans that were never saved auto-purge after N days. Without this split, ordinary browsing quietly fills the device.

Ship a storage screen showing usage, a clear action, and a "save scan images" toggle.

---

## SRS and organization

> **Background:** a Spaced Repetition System schedules review of each item at growing intervals, timed to just before the learner is predicted to forget it. **FSRS** (Free Spaced Repetition Scheduler) is the modern open-source algorithm, adopted by Anki; it is better calibrated than the older SM-2.

**D-26 — FSRS, not SM-2 and not a custom algorithm.**
Well-researched, actively maintained, and open implementations exist to port. Scheduling algorithms are easy to get subtly wrong and the failure mode (wasting the user's study time for months) is invisible.

**D-27 — Study items are polymorphic from day one, even though v1 ships words only.**

The `study_item` table carries a `type` discriminator (`WORD` | `KANJI`) from the first schema version, and identity is `(text, reading, type)`.

*Why now:* kanji-only study is a wanted future feature (see D-01). Adding the discriminator later would mean restructuring the table that `srs_state` and every row of `review_log` point at — a migration touching the user's entire study history. Adding a column now that v1 always populates with `WORD` costs one field.

**D-28 — Saved lists are many-to-many, via a join table.**
Users can create named lists ("Street Signs", "Food Menu"). A `list_id` column on the study item would restrict each word to a single list — but the same word genuinely appears on both a restaurant menu and a street sign, and the user will want it in both.

**D-29 — Scheduling belongs to the study item; lists only filter review sessions.**

There is exactly one `srs_state` row per study item. It hangs off `study_item`, **not** off list membership.

*Why this matters:* if scheduling attached to list membership, a word saved to two lists would carry two independent schedules. The user would review 先生 today because it appeared in "Street Signs" and again tomorrow via "Food Menu" — doubling their workload and corrupting the algorithm's model of their memory, since FSRS infers retention from the interval since the last review.

Lists are organizational tags. Review sessions may *filter* by list ("review only my Food Menu words"), which gives the same flexibility with correct behavior.

---

## UI

> **Terms used below.** *Peek sheet:* a bottom sheet partially raised over the current screen, showing a summary. *Component chips:* small tappable elements on the word screen, one per constituent kanji. Full screen descriptions are in `ux.md`.

**D-30 — The peek sheet and the word screen are a single component.**
Material 3's `ModalBottomSheet` supports partial and full expansion. The partial (peek) state shows word, reading, meaning, a Save action, and a "Full Details" button. Dragging it up — or tapping Full Details — expands the same sheet into the complete word screen.

*Why:* the original design described a popup plus a separate full-screen detail view. Making them one expanding sheet means the user never loses their place in the scanned image, the gesture is natural and reversible, and the project builds one component instead of two.

**D-31 — Peek only on the scan screen.**
The peek state exists because the scan screen is where a user triages many words quickly and wants to stay in the image. Once inside a detail context, navigation is direct. No nested peeks.

**D-32 — The kanji screen swaps in place inside the sheet, with a back arrow.**
Rather than pushing a separate full screen onto the navigation stack. This keeps the frozen scan visible behind the sheet, preserves the sense of still studying *this* image, and makes one back gesture return to the word.

Cost: `ModalBottomSheet` has no built-in back stack, so this needs a small amount of custom Compose plumbing to manage the two-level word→kanji stack.

**D-33 — Overlay style: dim the image, render detected text at full brightness.**
Drawing a rectangle around every detected word turns a photograph into unreadable clutter. Dimming everything *except* the text makes the legible text itself the affordance — it reads as deliberate design rather than a debug view. A solid highlight marks the currently selected word only.

**D-34 — Bundle Noto Sans JP explicitly rather than relying on system fonts.**
Unicode unifies Chinese and Japanese characters onto shared codepoints, but the correct *glyph shapes* differ by region — 直, 骨, 令, and 化 all render visibly differently in Chinese versus Japanese typefaces. Android's default font stack may select Chinese forms depending on locale and device.

In an app whose purpose is teaching people to read and write kanji, displaying the wrong glyph form is a correctness bug, not a polish issue.

**D-35 — Material 3 with a design-token layer from the first UI commit.**
Centralized colors, type scale, and spacing. Roughly ten minutes of setup at the start; a refactor touching every composable if retrofitted later.

**D-36 — Three bottom-navigation destinations: Scan · Saved · Review.**
Resist a fourth. Settings, storage, and attribution live inside Saved or a menu, not in the primary navigation.

**D-37 — Reading labels follow the standard dictionary kana convention: on'yomi in katakana, kun'yomi in hiragana.**

On the kanji screen's Overview and Examples tabs, reading group headers render as:

> **セイ** — 先生 · 学生 · 生活          ← on'yomi, katakana
> **ショウ** — 一生 · 誕生日             ← on'yomi, katakana
> **なま** — 生ビール                    ← kun'yomi, hiragana
> **い(きる)** — 生きる                  ← kun'yomi, hiragana

*Why:* this is the convention used by every Japanese dictionary and learning resource, so it matches what learners will encounter elsewhere. It also carries information for free — the script alone tells the user whether a reading is on'yomi or kun'yomi, without a label, which matters because on'yomi typically appear in multi-kanji compounds and kun'yomi typically stand alone.

**This requires deliberate normalization during Phase 1 ingest, because the source datasets disagree:**

| Source | Stores readings as |
|---|---|
| KANJIDIC2 | on'yomi in katakana, kun'yomi in hiragana — already correct |
| JmdictFurigana | hiragana throughout, since furigana is conventionally hiragana |

Since JmdictFurigana is what powers the grouping (D-13), its hiragana readings must be converted to katakana when the reading is an on'yomi. Determining which is which means cross-referencing KANJIDIC2's reading lists for that kanji. Get this wrong and every on'yomi group header renders in the wrong script.

*Scope note:* this governs **reading labels only.** Furigana displayed over words stays hiragana in all cases (D-14) — that is a separate convention and the two must not be conflated.
