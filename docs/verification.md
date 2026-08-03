# Verification Cases

Known-good expected values, tied to the decisions they protect.

## What belongs here

**Only cases where a bug produces plausible-looking output with no error.** That is the selection criterion, and it keeps this file from becoming a generic test plan.

The failure mode this file exists to catch: the script runs, the app builds, the screen renders, nothing throws — and the content is wrong in a way nobody notices for months. Wrong kana script. A word silently collapsed to one of its three readings. Furigana split across characters that don't own it. Examples sorted by database order instead of frequency.

A crash is self-reporting. These aren't.

Each case names the decision it protects, so grepping this file for a decision ID (`D-12`) finds every case that assumes it. Keeping those in sync is part of the supersede procedure documented at the top of `decisions.md` — a stale verification case is worse than none, because it asserts something the project no longer believes.

**Readings below should be confirmed against KANJIDIC2 during Phase 1 rather than trusted from this file** — this document records the *shape* of the expected answer and the trap being tested, not an authoritative reading list.

---

## Phase 1 — Dictionary builder

### V-01 · Kana script by reading type (D-37)

The trap: JmdictFurigana supplies all readings in hiragana. On'yomi must be stored and displayed in katakana. Nothing errors if this is skipped — every on'yomi header simply renders in the wrong script.

Query the kanji 生 and check the script of each reading group:

| Reading | Type | Expected script |
|---|---|---|
| セイ | on'yomi | **katakana** |
| ショウ | on'yomi | **katakana** |
| なま | kun'yomi | hiragana |
| い(きる) | kun'yomi | hiragana |

Fails silently as `せい` / `しょう` if normalization is skipped.

### V-02 · Words with multiple readings survive ingest (D-12)

The trap: a naive "one row per word text" schema keeps whichever reading it encountered last and silently discards the others.

Query 上手. Expect **three** distinct entries:

| Reading | Meaning |
|---|---|
| じょうず | skilled, good at |
| うわて | the upper hand, superior position |
| かみて | stage left, upstream |

One row returned means identity is keyed on text alone — a D-12 violation that makes the readings unrecoverable later.

### V-03 · Jukujikun alignment (D-06, D-13, D-14)

The trap: assuming every word's reading splits cleanly per character.

明日 is unusually good as a fixture because its readings behave differently from one another:

| Reading | Splits per character? |
|---|---|
| みょうにち | **Yes** — みょう = 明, にち = 日 |
| あした | **No** — jukujikun, the reading belongs to the whole word |
| あす | **No** — also irregular |

Expect `kanji_in_word` to contain rows for みょうにち and **no per-character rows** for あした or あす. If the ingest invents an alignment for あした, it will teach a false reading.

### V-04 · Frequency ranking is applied (D-04)

The trap: examples sorted by insertion order look fine but surface obscure vocabulary, which quietly makes the app's core feature feel broken.

Query example words for 生 grouped by reading. The セイ group should lead with high-frequency words — 先生, 学生, 生活 — not rare compounds. If the ordering looks arbitrary, the JMdict priority tags (`nf01`–`nf48`, `news1`, `ichi1`) were parsed but not applied to sorting.

### V-05 · Dictionary row IDs absent from any user-facing contract (D-11)

Not a data check but a review check, and cheap: grep the export format, the user DB schema, and any serialization for dictionary row IDs. They must not appear. This is verifiable before the user DB exists and gets harder to audit later.

---

## Phase 2 — Tokenization and lookup

### V-06 · Segmentation plus alternates (D-07)

Input: `先生と生産`

| Mechanism | Expected |
|---|---|
| Kuromoji primary parse | 先生 / と / 生産 |
| JMdict longest-match at position 0 | 先生 (longest) **and** 先 (alternate) |

Both halves matter. Only the Kuromoji parse means longest-match isn't running, and the compound-versus-word interaction — the app's whole pedagogical premise — silently won't work. The user could never ask about 先 on its own.

### V-07 · Conjugated verbs resolve to dictionary form (D-07)

Input: `生きた`

Expect resolution to the dictionary entry 生きる. Plain longest-match cannot do this; it's the specific reason Kuromoji is in the stack alongside it. Failure looks like "word not found" on perfectly ordinary text.

### V-08 · Reading labels vs. furigana use different scripts (D-14, D-37)

Two conventions that are easy to conflate, on screen at the same time:

- Furigana rendered above 先生 → **せんせい** (hiragana, always)
- On'yomi group header on the 生 kanji screen → **セイ** (katakana)

If both render in the same script, one convention has been applied globally.

---

## Phase 3 — Stroke order

### V-09 · Stroke count and stroke path count agree (KanjiVG)

For any kanji, the number of animated paths must equal KANJIDIC2's `stroke_count`. A mismatch means the SVG was parsed incorrectly — the animation still plays and still looks like handwriting, which is exactly why this needs an assertion rather than an eyeball.

Spot-check a low-stroke and a high-stroke character.

---

## Phase 4–5 — Camera and overlay

### V-10 · Vertical text (縦書き) (D-33, `architecture.md`)

Collect a **vertical** Japanese text image as a permanent test fixture before overlay work starts, not after.

Expected: correct reading order (top to bottom, then right column to left column), and tap targets aligned to characters. A horizontal-only coordinate implementation typically still returns *something* on vertical text — usually the wrong character, or the right characters in scrambled order.

### V-11 · Character-level tap resolution (`architecture.md` stage 4)

On a frozen scan of `先生と生産`, tapping the 産 glyph must open 生産, not 先生 and not と.

This is the interpolation math connecting ML Kit's pixel rectangles to tokenizer character offsets. Off-by-one errors here are systematically wrong but rarely obviously wrong — taps land on a neighbouring word, which reads as "the OCR is a bit flaky" rather than as a bug.

### V-12 · Japanese glyph forms (D-34)

Render 直, 骨, 令, 化 and confirm they show **Japanese** forms rather than Chinese ones. These four are known divergent characters under Unicode CJK unification.

Both forms are legible and neither errors. In an app teaching people to write kanji, the wrong form is a correctness bug — and it's device- and locale-dependent, so it may look correct on the development device and wrong on a user's.

---

## Phase 6–7 — Study loop

### V-13 · One schedule per item across multiple lists (D-29)

Setup: save 先生, add it to two lists ("Street Signs" and "Food Menu"), review it once.

Expect **one** `srs_state` row and **one** due date. If the word appears twice in a review session, or has two independent schedules, scheduling has been attached to list membership instead of to the study item — which doubles the user's workload and corrupts FSRS's model of their retention.

### V-14 · Study item type discriminator populated (D-27)

Every v1 row must have `type = WORD` explicitly, never null or defaulted. A nullable discriminator that "works" because v1 only writes one kind is the exact retrofit D-27 exists to prevent.

---

## Phase 8 — Export/import

### V-15 · Round-trip fidelity (D-20)

Export, wipe app data, import. Expect study items, readings, list membership, SRS state, and review history all preserved.

Specifically confirm 上手 (じょうず) and 上手 (うわて) survive as **separate** items with separate schedules — the export format is the most likely place for identity to silently collapse back to text alone (D-12).

### V-16 · Format version present from the first release (D-20)

The export file must carry a format version field from v1.0. Adding it in v1.1 means the first release's exports are unidentifiable to any future importer, and there is no way to fix that retroactively.
