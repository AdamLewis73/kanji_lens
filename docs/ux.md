# UI / UX

Read `overview.md` first if you're new — it has a worked end-to-end walkthrough of the main flow and defines the Japanese-language terms used here.

The app's core interaction — tapping one specific word on a photograph — has no established convention to borrow from. It deserves more design attention than a typical app's navigation.

## Vocabulary used in these docs

| Term | Meaning |
|---|---|
| **Peek sheet** | A Material 3 `ModalBottomSheet` raised partway over the frozen scan, showing a one-line summary of the tapped word. Expanding it reveals the full word screen — they are the same component (D-30). |
| **Word screen** | The expanded sheet. Reading, meanings, component chips, examples. No tabs. |
| **Kanji screen** | Reached by tapping a component chip. Three tabs. Swaps in place inside the sheet (D-32). |
| **Component chips** | Small tappable elements on the word screen, one per constituent kanji, showing meanings only (D-06). |
| **Ambiguity chips** | A different thing: a row of candidate words shown when a tap could resolve to more than one token. See below. |

## Screen map

```
Bottom nav: Scan · Saved · Review          (three — resist a fourth, D-36)

Scan
 └─ live preview + "text detected" indicator + large shutter
     └─ frozen image + overlay
         └─ tap word → PEEK SHEET
                        word · furigana · reading · meaning
                        [Save]  [Full Details]
             └─ expand → WORD SCREEN            (same sheet, D-30)
                          reading(s), meanings + part of speech,
                          component kanji chips, example sentences
                 └─ tap chip → KANJI SCREEN     (in place, back arrow, D-32)
                                Overview | Examples | Stroke Order
```

### Word screen — no tabs

Reading(s), meanings with part of speech, **component chips showing meanings only** (D-06), and examples of the word's own usage variations.

### Kanji screen — three tabs

| Tab | Content |
|---|---|
| **Overview** | Meanings, on'yomi / kun'yomi, stroke count, JLPT level, official radical |
| **Examples** | Other words containing this kanji, grouped by reading, frequency-sorted (D-04) |
| **Stroke Order** | KanjiVG animation — paths drawn sequentially in correct stroke order |

The Examples tab expresses the same idea at both levels: **show every distinct way this thing is used.** For a kanji that means its different readings; for a word it means its sense variations.

Design this so that a word or kanji with only **one** reading reads as *information*, not as a broken screen. "Only one reading — this one's easy to remember" is genuinely useful to a learner. An empty-looking panel is not.

## The overlay

**Style (D-33):** dim the whole image and render detected text at full brightness, with a solid highlight on the selected word only. Drawing a box around every detected word is unreadable clutter; making the legible text itself the affordance reads as deliberate design rather than a debug view.

### Tap targets are the hard problem

Material's accessibility minimum for a touch target is 48dp. A kanji on a shop sign photographed from three metres away may occupy 12dp. All three mitigations below are needed — none is sufficient alone.

1. **Pinch-zoom and pan on the frozen image.** The primary fix, and wanted regardless. It's also a strong argument for freeze-frame (D-02): a moving feed cannot be zoomed and inspected.
2. **Ambiguity chips.** When a tap could resolve to more than one token, show a small horizontal row of candidates near the touch point rather than silently guessing. This doubles as the compound-versus-word interface: tapping 先 offers both 先 and 先生, which is exactly the pedagogical point (D-07).
3. **Snap to nearest token** within a tolerance radius, so near-misses still land.

### Vertical text

Japanese signage, menus, and book spines are frequently written **縦書き** — top to bottom, right to left. Overlay geometry, reading order, and sheet placement must all tolerate it. See `architecture.md` for the coordinate-mapping implications.

Test against vertical text from the first day of overlay work. Discovering it later means redoing the most error-prone stage of the pipeline.

## Typography

**Furigana rendering is custom work.** Compose has no built-in ruby-text support. A composable that draws small kana above a word — with correct centering, sizing, and line breaking — will appear on nearly every screen in the app. Build it once, early, and reuse it everywhere.

Whole-word ruby only (D-14): せんせい positioned over 先生 as a unit, never split per character.

Include a **global furigana toggle.** Advanced learners find constant furigana distracting, and hiding it during review makes recall genuinely harder in a useful way.

**Bundle Noto Sans JP (D-34).** Without an explicit Japanese font, Android may render kanji using Chinese glyph forms — 直, 骨, 令, and 化 all differ visibly between the two. In an app that teaches people to read and write kanji, that is a correctness bug rather than a polish issue.

## Context of use

This app gets opened while standing in a shop, sitting at a restaurant table, or waiting on a train platform. That drives several things that are easy to miss when designing at a desk:

- **One-handed reachability.** Nothing important in the top corners — the user is holding the phone up with one hand. The bottom-sheet pattern is already correct for this.
- **Dark mode is not optional.** Evenings and dim interiors are prime usage time.
- **Large shutter target**, comfortably thumb-reachable while the phone is raised.
- **Fast cold start.** If reaching a working camera takes four seconds, people give up and open Google Translate instead.

## Easy to skip, shouldn't be

**Onboarding.** The app's premise is not self-evident from a viewfinder — a new user sees a camera and assumes it's a translator. Three screens explaining the 生 → 先生 → 生産 idea, or better, a bundled sample image they can tap around in *before* granting camera permission. Request the permission after they understand why it's needed.

**Empty states.** "No saved words yet" and "Nothing due for review" are the screens a new user sees most often, which makes them the best onboarding surface available. Don't leave them blank.

**Attribution screen.** A license obligation under CC BY-SA — see `data-model.md`. Not a nicety.

**Storage screen (D-25).** Usage breakdown, a clear action, and a "save scan images" toggle. Users who discover an app consuming 500 MB uninstall it.

## Process

**Wireframe the frozen-scan screen and the expanded sheet before writing any Compose code** — paper is fine. The overlay/tap/sheet interaction is the app's entire identity, and problems are enormously cheaper to find with a pencil than with a rebuild. Everything else (Saved, Review) follows conventional patterns that can be borrowed wholesale.

Set up Material 3 design tokens — colors, type scale, spacing — in the first UI commit (D-35). Ten minutes then; a refactor touching every composable later.
