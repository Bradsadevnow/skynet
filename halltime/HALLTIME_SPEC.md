# HallTime Spec

Status: active working spec
Last updated: 2026-05-29
Scope: `halltime/` in `/home/brad/projects/gemma`

## 1. Purpose

HallTime is a synthetic cable network generator for Lifetime- and Hallmark-adjacent movie artifacts presented as if they are leaking in from an illegal interdimensional station.

It is not only a one-shot text generator.
It is a three-layer system:

1. structured broadcast generation
2. corpus indexing and editorial criticism
3. feedback-driven recurrence pressure on future generations

The project goal is not realism.
The goal is synthetic cultural continuity inside a fake network that learns what deserves recurrence.

## 2. Core Product Thesis

HallTime should feel like:
- a haunted regional movie network
- a shared county mythology
- a criticism loop, not just a prompt toy
- obvious satire at the presentation layer
- genre-authentic structure underneath the joke layer

The system should distinguish between:
- climate: substrate motifs that are always around
- signal: charged props, doctrine particles, and productive contradictions

Examples:
- `kitchen`, `basement`, `brunch`, `municipal policy failure` are climate
- `boat key`, `snow globe`, `scarf with impossible timing`, `portable suspicion`, `regional utility` are signal candidates

## 3. System Components

### 3.1 Generator

Primary file: `halltime/movie_generator.py`

Responsibilities:
- choose a starter premise from `halltime/universe_bible.yaml`
- select cast archetypes from `halltime/archetypes.yaml`
- generate structural beats from category and intensity logic
- build presentation metadata for the HallTime network wrapper
- optionally expand the scaffold through LM Studio prose generation
- save markdown and JSON artifacts to `halltime/outputs/`
- save run traces to `halltime/runs/`

### 3.2 Universe Bible

Primary file: `halltime/universe_bible.yaml`

Responsibilities:
- define network canon and unstable lore
- define recurring towns, institutions, props, omens, and relationship dynamics
- define starter premises and their variants
- define category skeletons and prose registers

### 3.3 Archetype Bank

Primary file: `halltime/archetypes.yaml`

Responsibilities:
- provide the trope starter pack for cast generation
- cover the broad Lifetime spectrum rather than one narrow county template
- support thriller, trauma drama, romance, holiday, feel-good, and wine-xanax-horror lanes

### 3.4 Refinement Layer

Primary file: `halltime/refinement.py`

Responsibilities:
- treat `halltime/outputs/` as a searchable corpus
- build `halltime/index/` artifacts
- classify motif tiers
- generate criticism artifacts such as `best_of_batch.md` and `failed_patterns.md`
- run a retrieval-backed editorial LM pass
- update `generation_feedback.json` so future broadcasts inherit editorial pressure

## 4. Runtime Contract

### 4.1 Default behavior

`movie_generator.py` must use LM Studio by default.

That is the standing contract.
Users should not need an opt-in flag for the interesting path.

Current CLI behavior:
- default run: LM expansion enabled
- explicit fallback: `--no-llm-expand`

This exists because unnecessary friction is considered a product defect for HallTime.

### 4.2 Generator command shape

Typical command:

```bash
python halltime/movie_generator.py --count 3 --seed 100 --run-label afternoon-broadcast
```

Scaffold-only fallback:

```bash
python halltime/movie_generator.py --count 1 --no-llm-expand
```

### 4.3 Refinement command shape

Build corpus index:

```bash
python halltime/refinement.py index
```

Search corpus:

```bash
python halltime/refinement.py search "boat key therapist dead wife"
```

Run editorial pass:

```bash
python halltime/refinement.py editorial-pass
```

## 5. Broadcast Generation Model

Each broadcast is built in layers.

### 5.1 Premise selection

The generator chooses one `starter_premise` from `universe_bible.yaml`.

A premise includes:
- `title`
- `category`
- `premise`
- `intensity`
- `signature_tell`
- optional `variants`

This is the first real story engine. HallTime no longer starts from only a title or only a random trope cluster.

### 5.2 Category skeleton

Category determines the dramatic engine before intensity mutates it.

Current category engines:
- `holiday`: deadline engine
- `romance`: misunderstanding engine
- `trauma_drama`: pressure cooker engine
- `wine_xanax_horror`: dread engine
- `thriller`: information asymmetry engine
- `feel_good`: permission engine

This logic lives in `universe_bible.yaml` and is enforced by `movie_generator.py`.

### 5.3 Intensity mutation

Intensity modifies the structure selected by category.

Current intended semantics:
- `low`: lighter version of the category engine
- `mid`: standard version of the category engine
- `high`: escalated consequences and stronger signal density
- `extreme`: may break the base template entirely

Important design rule:
- `low` and `mid` may share a skeleton with altered beat behavior
- `extreme` is allowed to change beat count, reveal timing, isolation pattern, and ending shape

Examples already encoded:
- police beat is more hostile at `extreme`
- ally beat collapses earlier at `extreme`
- `extreme` may use dread-first dramatic knowledge instead of discovery-first
- `extreme` endings may remain partially open or pyrrhic

### 5.4 Cast generation

Cast generation pulls archetypes and assigns roles such as:
- protagonist
- male_interest_or_threat
- best_friend
- elegant_wildcard
- secondary_male_pressure
- secondary_witness
- supporting

The cast is intentionally unstable, but it should still remain legible enough to support the genre machine.

### 5.5 Shared county atmosphere

All movies inherit Blackthorn County substrate:
- unstable geography
- porous male identity fields
- interpretively unstable mortality
- spiritually elastic basements
- regional institutions such as St. Agnes Regional and Channel 8 Night Report

This atmosphere is not supposed to be discovered fresh every time.
It is inherited as county weather.

## 6. LM Studio Role

### 6.1 What is hard-coded versus model-authored

Hard-coded / deterministic layers:
- premise bank
- category engine selection
- intensity branching
- cast scaffolding
- motif weighting from `generation_feedback.json`
- interruption placement in beat sheets
- editorial indexing logic

LM-authored layers:
- expanded synopsis
- dialogue lines
- scene paragraphs
- contradiction intensification notes
- alternate titles
- franchise adjacency

Current reality:
- HallTime is a structured authored machine with LM-driven surface expansion
- it is not a pure LLM improvisation engine

That is intentional. The skeleton should remain governed even when the prose gets weirder.

### 6.2 LM transport

LM Studio endpoint resolution:
- `LM_STUDIO_URL` if present
- else `LM_STUDIO_BASE_URL` plus `/chat/completions`
- else default `http://127.0.0.1:1234/v1/chat/completions`

Current default model:
- `openai/gpt-oss-20b`
- overridable via `--llm-model` or `CHAT_MODEL_ID`

### 6.3 Known LM seam

Current observed failure mode:
- LM sometimes returns malformed JSON
- generator retries multiple times
- a later retry may still succeed

This is currently tolerated but not fully hardened.
It is a real system seam and should be treated as such.

## 7. Presentation Layer

HallTime output is not just a plot outline.
It is rendered as a fake network broadcast dossier.

### 7.1 Wrapper voice

The markdown output includes:
- announcer intro
- viewer advisory
- broadcast teaser
- local ad slot
- continuity alert
- beat sheet interruptions
- return-to-broadcast copy
- critic blurb
- sequel hook
- `Up Next on HallTime` bumper

### 7.2 Diegetic ad logic

Ads must be in-universe.
They should advertise services that only make sense in Blackthorn County.

Examples:
- locksmiths who do not ask why
- grief groups with optional background checks
- realtors who refuse to discuss previous owners

### 7.3 Category-aware station voice

The presentation layer must mutate with genre.

Examples:
- holiday voice should sound coercively festive and deadline-driven
- romance voice should sound soft, yearning, and structurally manipulative
- thriller voice should sound procedural and ominous
- wine-xanax-horror should sound too calm and therefore threatening
- trauma drama should sound solemn and witnessed
- feel-good should sound warm but permission-oriented

The station should feel like one illegal network with corrupted sub-departments, not one static narrator reading every format.

## 8. Artifact Model

### 8.1 Output artifacts

Saved per broadcast under `halltime/outputs/`:
- `*.json`
- `*.md`

Markdown includes sections such as:
- title and wrapper copy
- synopsis
- recurring props
- cast
- beat sheet
- contradiction ledger
- dialogue samples
- scores
- franchise hooks
- optional LM expansion metadata

### 8.2 Run artifacts

Saved per run under `halltime/runs/<run-id>/`:
- `run.log`
- `summary.jsonl`
- `prompts/`
- `responses/`
- `artifacts/`

This run trail is part of the artwork and part of system debugging.

### 8.3 Index artifacts

Saved under `halltime/index/`:
- `broadcasts.jsonl`
- `summary.json`
- `concept_graph.json`
- `editorial_report.md`
- `best_of_batch.md`
- `failed_patterns.md`
- `canon_candidates.json`
- `generation_feedback.json`
- `editorial/` prompt/response/note archives

## 9. Refinement and Taste Formation

Refinement is where HallTime stops being a prompt toy and starts acting like a network with taste.

### 9.1 Corpus indexing

`refinement.py index` extracts fields from all JSON broadcasts:
- title
- title family
- mode
- theme
- omen
- relationship dynamic
- props
- towns
- archetypes
- spaces
- contradiction types
- doctrine phrases
- scores
- LM enabled flag
- normalized text blob
- TF-IDF weights

### 9.2 Motif tiering

Current tier model:
- `tier_0_foundational_texture`: nearly universal climate motifs
- `tier_1_identity_markers`: recurring but still differentiating markers
- `tier_2_high_variance_mutations`: rarer doctrine particles worth protecting
- `tier_3_dead_sludge_candidates`: low-yield clutter or exhausted residue

This tiering feeds criticism and future generation weights.

### 9.3 Feedback artifact

`generation_feedback.json` currently controls pressure such as:
- `demote_phrases`
- `promote_props`
- `protect_phrases`
- `title_weights`
- `male_archetype_weights`
- `mode_weights`
- `theme_weights`

This is HallTime's current preference substrate.

### 9.4 Editorial pass

The editorial LM pass is retrieval-backed.

It:
- loads `canon_candidates.json`
- retrieves sibling broadcasts by similarity
- builds an editorial prompt
- asks the model what deserves recurrence
- merges adjustments back into `generation_feedback.json`
- archives prompt, raw response, notes, and update log

This is the first real criticism loop in the system.

## 10. Concept Graph

`concept_graph.json` models recurrent relationships across the corpus.

Current node families:
- title
- prop
- archetype
- phrase
- town

Current edge families:
- `appears_with`
- `casts`
- `recurs_in`
- `located_in`

This graph supports the project's shift from pure memory toward symbolic digestion.

## 11. Design Principles

HallTime should obey these principles.

### 11.1 Structure before prose

Genre scaffolding should be explicit and inspectable.
The model should decorate and elaborate structure, not replace it blindly.

### 11.2 Criticism before recurrence

Just because a motif appears often does not mean it should gain more weight.
Repetition alone does not create meaning.

### 11.3 Climate is not novelty

Foundational substrate should be inherited quietly.
Novelty budget should be spent on signal, not rediscovering kitchens.

### 11.4 Presentation is part of the work

The network wrapper is not cosmetic.
The illegal-channel voice is part of HallTime's identity.

### 11.5 Friction is a defect unless it buys something real

Interesting behavior should be the default path.
Fallbacks should be explicit escape hatches, not the main contract.

## 12. Known Issues

Current known issues include:
- LM responses can still fail JSON parsing and require retries
- some cast assignments still drift into gender or role incoherence in funny but not always useful ways
- dialogue samples are less category-specific than the wrapper and synopsis layers
- some generic county phrasing still leaks into surfaces that should be more lane-specific
- cluster rules in refinement are intentionally broad and need more selective intolerance
- many scores are still more aesthetic than evaluative

## 13. Near-Term Next Work

Highest-value next steps:
- make dialogue samples category-aware the same way synopsis and station voice already are
- harden LM JSON handling so default generation is robust instead of lucky
- widen editorial criticism from simple weight updates to more explicit doctrine formation
- improve cast coherence without sanding off HallTime weirdness
- refine concept clustering so everything stops counting as the same franchise cloud
- consider a lightweight operator dashboard for corpus browsing and editorial inspection

## 14. Non-Goals

HallTime is not trying to be:
- a realistic screenplay generator
- a polished consumer app first
- a generalized creative writing engine
- a clean continuity universe with no contradictions

Contradiction, recurrence drift, and county folklore are part of the point.

## 15. Success Criteria

HallTime is succeeding when:
- outputs feel like broadcasts from the same impossible network
- categories actually differ structurally and tonally
- the corpus develops recognizable climate and signal separation
- editorial passes measurably affect later generation
- the system's taste becomes more interesting over time
- watching the machine learn preference is at least as interesting as any individual movie artifact
