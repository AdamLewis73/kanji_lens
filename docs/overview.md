# Overview

**Start here if you're new to this project.** This document explains what the app does, why, and defines the Japanese-language terms used throughout the other docs.

## The problem

Kanji don't have fixed meanings in isolation — they have meanings *in context*.

- 生 alone means "life / birth". In 先生 it's "teacher". In 生産 it's "production".
- 手 alone means "hand". In 上手 it's "skilled". In 歌手 it's "singer".

Translation apps optimize for *replacing* Japanese text with English, which destroys exactly the information a learner needs. Kanji Lens keeps the Japanese and explains it.

## The product

Point the camera at real-world Japanese — a sign, a menu, a package — freeze the frame, tap a word, and see what it means, how it's read, and which kanji compose it. Save words to lists and review them with spaced repetition.

The learning claim: **contextual exposure to real text beats memorizing isolated characters.**

## Worked example: what actually happens

A user photographs a sign reading `先生と生産`. This walks the whole system end to end.

**1. Scan.** The camera preview shows a "Japanese text detected" indicator. The user presses the shutter. The frame freezes (D-02) and everything afterward happens on that still image.

**2. Recognition.** ML Kit reads the image and returns the text `先生と生産` along with pixel rectangles for each chunk it found.

**3. Tokenization.** Japanese has no spaces, so the app must decide where words begin and end. Kuromoji splits it into 先生 / と / 生産. Separately, longest-match against the bundled dictionary notes that position 0 also matches the shorter word 先, and keeps it as an alternate (D-07).

**4. Overlay.** The image dims, leaving the recognized text bright (D-33). Each detected word is now tappable.

**5. Peek.** The user taps 先生. A bottom sheet rises partway:

> **先生** ・ せんせい
> teacher; instructor; master
> `[Save]` `[Full Details]`

**6. Word screen.** Dragging the sheet up expands it (D-30) into the full word screen:

> **先生** ・ せんせい — teacher; instructor; master
> Composed of: `先 previous, ahead` `生 life, birth`
> Examples: 日本語の先生 — *a Japanese teacher*

Note the component chips show meanings but **not** readings (D-06).

**7. Kanji screen.** The user taps the 生 chip. The sheet swaps in place, with a back arrow (D-32), to a three-tab kanji screen. The **Examples** tab is where the app's core idea lands:

> **セイ** — 先生 teacher · 学生 student · 生活 daily life
> **ショウ** — 一生 a lifetime · 誕生日 birthday
> **なま** — 生ビール draft beer
> **い(きる)** — 生きる to live

The user sees, without reading any authored explanation, that 生 carries different sounds and senses depending on the company it keeps. That's the entire product thesis in one screen (D-04).

**8. Save and review.** Tapping Save stores 先生 as a study item, optionally into a named list like "Street Signs". It enters the FSRS schedule and reappears for review at the right time. The scan image is saved with it, so the word stays attached to the place it was found.

## Product principles

1. **Word-first, kanji-second.** The unit of study is the word. Kanji screens are reference material reached by drilling down.
2. **Offline always.** No network required for any core function. No runtime LLM calls.
3. **Show, don't assert.** Rather than authoring an explanation of why 生 means teacher in 先生, show every common word using 生 grouped by reading and let the pattern teach.
4. **Usage completeness.** A learner should be able to look at any word or kanji and answer: *"Do I know how to use this in all the ways it's used?"* A word with only one reading isn't a thin screen — it's useful information: *this one is easy.* The UI should say so rather than looking empty.
5. **Real-world capture.** The scan image is saved with the word. "That sign outside the ramen shop" is a stronger memory hook than a bare flashcard.

## Core features

| Feature | Summary |
|---|---|
| **Scan** | Camera → freeze frame → tap detected words → detail sheet |
| **Word screen** | Reading, meanings, component kanji, example sentences |
| **Kanji screen** | Overview / Examples / Stroke Order tabs |
| **Saved lists** | Multiple user-named lists ("Street Signs", "Food Menu") |
| **SRS review** | FSRS-scheduled quizzes over saved words |

## Platform

Android first, targeting recent API levels with a low `minSdk` for reach. iOS is a later possibility; the codebase is layered so business logic and data can migrate via Kotlin Multiplatform rather than being rewritten. See `architecture.md`.

## Glossary

Terms used throughout these docs.

| Term | Meaning |
|---|---|
| **Kanji** | Chinese-derived logographic character. ~2,000 in common use. |
| **Kana** | The two phonetic scripts — hiragana (ひらがな) and katakana (カタカナ). |
| **Furigana** | Small kana printed above kanji to show pronunciation. |
| **On'yomi** | A kanji's Chinese-derived reading. Typically used in multi-kanji compounds. |
| **Kun'yomi** | A kanji's native Japanese reading. Typically used standalone or with kana endings. |
| **Jukujikun** | A word whose reading attaches to the word as a whole and cannot be split per character. 明日 = あした. Important because it invalidates per-character reading display (D-06). |
| **Compound (熟語)** | A word made of two or more kanji. 先生, 生産. |
| **Radical (部首)** | The classical indexing component of a kanji. Exactly one per kanji, drawn from a set of 214 established in a 1716 dictionary. Distinct from the full set of visual components a kanji contains. |
| **Tokenization** | Splitting Japanese text into words. Necessary because Japanese is written without spaces, and technically the central problem of this app. |
| **Morphological analyzer** | A tool that performs tokenization, also returning part of speech and dictionary base forms. Kuromoji is one. |
| **SRS** | Spaced Repetition System. Schedules reviews at growing intervals timed to just before predicted forgetting. |
| **FSRS** | Free Spaced Repetition Scheduler. The modern open-source SRS algorithm, successor to SM-2, adopted by Anki. |
| **縦書き (tategaki)** | Vertical writing — top to bottom, right to left. Common on signage and book spines, and a real constraint on the scan overlay. |
| **Peek sheet** | This project's term for the partially-expanded bottom sheet shown when a word is tapped on a scan. See D-30. |
| **Component chips** | This project's term for the tappable per-kanji elements on the word screen. See D-06. |
