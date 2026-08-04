# Kanji Lens

By Adam Lewis

An Android app for learning kanji **in context**.

Kanji don't have fixed meanings in isolation. 生 alone is "life", but 先生 is "teacher" and 生産 is "production". 手 alone is "hand", but 上手 is "skilled" and 歌手 is "singer". Translation apps replace the Japanese, which destroys exactly the information a learner needs.

Kanji Lens keeps the Japanese and explains it. Point the camera at a sign, a menu, or a package; freeze the frame; tap a word to see what it means, how it's read, and which kanji compose it. Save words to lists and review them with spaced repetition.

## Status

**Pre-development.** Design is complete; no code yet.

## Documentation

| Doc | Contents |
|---|---|
| [Overview](docs/overview.md) | Product vision, principles, glossary |
| [Decisions](docs/decisions.md) | Numbered decisions with rationale |
| [Architecture](docs/architecture.md) | Stack, modules, layering, navigation |
| [Data model](docs/data-model.md) | Datasets, schema, migrations, backup |
| [UX](docs/ux.md) | Screens, interaction, visual rules |
| [Roadmap](docs/roadmap.md) | Phases, checkpoints, deferred backlog |
| [Progress](docs/progress/) | Living state of work in flight |

## Working on this project

Two project slash commands, defined in `.claude/skills/`:

- **`/orient`** — load current context at the start of a session: phase, progress, open questions, repo state.
- **`/phase <n>`** — plan and begin a roadmap phase, e.g. `/phase 1`. Loads that phase's docs and verification cases, and stops at any decision checkpoint before writing code.

## Attribution

Dictionary data comes from [JMdict/KANJIDIC2](https://www.edrdg.org/) (EDRDG, CC BY-SA), [KanjiVG](https://kanjivg.tagaini.net/) (CC BY-SA), [JmdictFurigana](https://github.com/Doublevil/JmdictFurigana), and [Tatoeba](https://tatoeba.org/) (CC-BY). Full attribution ships in-app as required by these licenses.
