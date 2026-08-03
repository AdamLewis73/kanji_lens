# Roadmap

Read `overview.md` first if you're new to this project.

## Sequencing principle

**Build inside-out, not outside-in.** The instinct is to start with the camera because it's the exciting part. Don't — it's the hardest component to debug, and it sits on top of everything else, so a bug anywhere in a camera-first build looks like a camera bug.

By the end of Phase 3, roughly 70% of the app exists and is fully testable without ever pointing a phone at anything.

## Phases

| # | Phase | Status | Output |
|---|---|---|---|
| 1 | Dictionary builder (desktop Python) | Not started | `kanjilens.db` asset |
| 2 | Android app, text input only | Not started | Paste 先生 → word + kanji screens |
| 3 | Stroke order tab | Not started | KanjiVG animation |
| 4 | CameraX + ML Kit | Not started | Raw recognized text into the Phase 2 pipeline |
| 5 | Tappable overlay | Not started | The real scan experience |
| 6 | Saved lists | Not started | Multiple lists, many-to-many |
| 7 | SRS review | Not started | FSRS scheduling and quizzes |
| 8 | Export / import | Not started | Versioned JSON/zip |

### Phase 1 — Dictionary builder

A desktop Python script that parses JMdict, KANJIDIC2, KanjiVG, JmdictFurigana, and Tatoeba into a single SQLite file shipped as an Android asset (D-10). Contains no Android code and requires no emulator, so it de-risks the entire data layer before any Android work begins.

Schema draft is in `data-model.md`. **First task is inspecting the real source files**, since the draft was written from documentation rather than from the actual data.

Reading normalization (D-37) happens here: JmdictFurigana supplies readings in hiragana, but on'yomi must be stored as katakana, which requires cross-referencing KANJIDIC2.

### Phase 2 — Android app with a text box

**No camera at all.** Paste `先生と生産` into a text field, tokenize with Kuromoji, look up in Room, and render the word screen and kanji screen. This is where the app's actual value gets proven, and it's fully testable without any of the camera complexity.

### Phase 3 — Stroke order

Self-contained, visually rewarding, and good Compose practice. Renders KanjiVG's per-stroke SVG paths sequentially.

### Phase 4 — Camera

CameraX plus ML Kit's Japanese model, feeding recognized text into a pipeline that already works and is already trusted.

### Phase 5 — Overlay

The coordinate-mapping work described in `architecture.md` — connecting ML Kit's pixel rectangles to the tokenizers' character offsets so a tap resolves to a word. Highest risk of subtle bugs in the project. Include vertical text (縦書き) in test images from day one.

### Phases 6–8 — The study loop

Saved lists, then FSRS review, then export/import.

**A shippable v1 is Phases 1–5.** Phases 6–8 turn it from a lookup tool into a study app. The staging matters: the full spec is a large build, and stalling at 60% is the common failure mode for solo projects of this size.

---

## Decision checkpoints

Stop and decide before proceeding past each of these. Every one is cheap now and expensive or impossible to retrofit.

The project owner has asked to be consulted at these points rather than having a default chosen silently.

| Before | Decision | Why it's hard to undo |
|---|---|---|
| Phase 1 | Dictionary schema and natural-key strategy | Regenerating the dictionary is trivial; migrating user data that references it is not (D-11) |
| Phase 1 | Which datasets to ingest — JmdictFurigana is in (D-13) | Adding one later means a full rebuild plus a schema change |
| Phase 2, first commit | Module structure; `:domain` and `:data` free of `android.*` | This is the iOS-portability line — retrofitting is a rewrite |
| Phase 2, first UI commit | Material 3 plus a design-token layer (D-35) | Touches every composable if done later |
| Phase 2, first user-data write | UUID keys, `updated_at`, soft delete, schema export on, destructive migration off (D-15 – D-18) | Getting this wrong deletes user data in production |
| Phase 5 | Bounding box stored in the scan record (D-22) | Cheap now; later requires re-running OCR over every saved image |
| Phase 6 | Study-item identity `(text, reading)` plus the `type` discriminator (D-12, D-27) | All review history is keyed to it |

---

## Deferred

Pinned deliberately, each with the reason and the cost of adding it later. **None of these are rejected** — several are wanted, just not in v1.

| Item | What it is | Why deferred | Cost to add later |
|---|---|---|---|
| **Sudachi** | An alternative tokenizer with native multi-granularity splitting — it can return both 選挙管理委員会 and its parts 選挙 / 管理 / 委員会 from one pass | Requires extracting a memory-mapped dictionary from assets on first launch; ~3× larger dictionary; poorly documented on Android. May prove unnecessary since JMdict longest-match already surfaces overlapping candidates (D-07) | **Low** — the `Tokenizer` interface isolates it (D-08) |
| **Live camera overlay** | Google Translate-style continuous recognition instead of freeze-frame | Doing it well means background freeze-frames with change detection — genuinely complex. D-02's reasoning holds for v1 | **Medium** — new capture path, but everything downstream is reused |
| **Object recognition** | Point the camera at an object, get its Japanese name | ML Kit image labelling returns generic English labels ("Food", "Building") that then need translating into Japanese with no context. Weak payoff next to the text path, and effectively a separate app mode | **Medium** |
| **Curated kanji explanations** | Authored prose explaining why a kanji means what it does in a compound | Writing these for 2,000+ kanji is a content project, not a code project. D-04 delivers most of the value automatically and free | **Low** — purely additive content layer |
| **Word crops instead of full frames** | Save just the tapped word's region rather than the whole photo | Crop geometry is fiddly and shouldn't block v1 (D-21) | **Near zero** — D-22 stores the bounding box now, so no image reprocessing is ever needed |
| **KRADFILE radical components** | Show which visual pieces a kanji is built from | The component *data* is free, but standard English *names* for components are not, and inventing them risks looking derivative of WaniKani, whose names are their own authored content. ~214 names is a bounded task if ever wanted | **Low** — additive |
| **Word-level stroke order** | Play 先 then 生 in sequence on the word screen | Redundant and visually busy for long words; D-05 places stroke order on the kanji screen | **Low** — composes existing per-kanji data |
| **Accounts + server sync** | User profiles with cross-device sync | Authentication brings privacy obligations, a Play Store data-safety declaration, and hosting cost. None of it helps v1 | **Low — but only because** D-15, D-16, and D-19 are being followed from the start |
| **Ads** | Post-quiz placement, Duolingo-style | No reason to add before there are users | **Zero** — genuinely bolt-on: a dependency and a composable |
| **Kanji-only study items** | Let users add individual kanji to their SRS, not just words | v1 studies words (D-01) | **Near zero** — D-27 puts the `type` discriminator in the schema from day one |
| **Smart / auto lists** | Lists generated by rule — by JLPT level, shared kanji, or scan date | Nice-to-have | **Low** — falls out of D-28's join table |
