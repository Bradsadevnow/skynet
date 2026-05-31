# HallTime Experiment Process

## Why This Is More Than "AI Wrote A Bad Movie"

HallTime is not just a one-shot content generator. It is a documented experiment in machine-assisted genre production, where the creation process itself is part of the artwork.

The current system already does two important things:

1. It separates generative ideation from structural constraints.
2. It preserves intermediate artifacts instead of only keeping final outputs.

That matters because the interesting part is not only the finished movie outline. The interesting part is watching a model and a procedural system produce, discard, repeat, distort, and canonize ideas across a shared fictional universe.

## Current Pipeline

### Phase 1: Brainstorming

The current HallTime generator behaves like a rapid-fire idea machine.

It produces:
- titles
- taglines
- archetypal casts
- recurring props
- beat sheets
- contradiction ledgers
- sample dialogue
- sequel hooks
- scorecards

This phase is intentionally permissive.
Some ideas are excellent.
Some are thin.
Some are repetitive.
Some are accidental gold.

That is acceptable because the point of brainstorming is volume, not judgment.

### Phase 2: Expansion

By default, LM Studio receives a structured HallTime broadcast package and expands each HallTime broadcast into. Use `--no-llm-expand` only when you explicitly want scaffold-only output:
- longer synopsis text
- scene paragraphs
- more dialogue lines
- contradiction intensification notes
- alternate titles
- franchise adjacency notes

This lets the model spend tokens on prose and atmospheric drift while the local generator holds onto the structural doctrine.

### Phase 3: Logging And Preservation

Every unattended run produces a durable evidence trail under `halltime/runs/`.

Each run can include:
- `run.log`: append-only event log
- `summary.jsonl`: one summary record per broadcast
- `prompts/`: exact prompt packages sent to LM Studio
- `responses/`: raw model responses or failure records
- `artifacts/`: copies of saved markdown and JSON outputs

This is critical. The experiment is not only the generated movie. The experiment is also the trace of how the system got there.

## The Next Required Step: Refinement

Right now HallTime is strong at ideation.
The next layer is editorial selection.

The refinement process should not ask:
- "Can the model generate more?"

It should ask:
- "Which ideas did the system appear to like?"
- "Which motifs kept recurring because they were actually productive?"
- "Which outputs felt dead, generic, or redundant?"
- "Which contradictions became mythology instead of noise?"

This is where HallTime stops being a slop emitter and becomes a synthetic studio process.

## Proposed Refinement Architecture

### A. Broadcast Corpus

Treat the output directory as a corpus, not a dump.

Each generated broadcast is a document containing:
- title
- mode
- cast
- props
- locations
- beat sheet
- contradiction ledger
- dialogue
- scores
- optional LM Studio expansions

This corpus becomes the raw material for later editorial reasoning.

### B. Retrieval Layer

With a 60k token budget, we do not need to choose between tiny context and no memory.
We can retrieve meaningful subsets of prior broadcasts.

Possible retrieval methods:
- semantic search over synopsis, beat sheet, contradiction ledger, and dialogue
- structured search by title family, props, town, archetype, omen, or mode
- score-based ranking for high `slop_elegance`, `canon_drift`, or `wine_saturation`
- contradiction retrieval for phrases like `emotionally true`, `interpretively unstable`, or `just storage`

The goal is to pull back the most useful prior examples before refinement.

### C. Concept Graph

A concept graph is especially promising for HallTime because the universe is built from recurring relational motifs rather than exact continuity.

Potential graph nodes:
- titles
- towns
- props
- omens
- archetypes
- characters
- locations
- relationship dynamics
- contradiction types
- signature phrases

Potential graph edges:
- `appears_with`
- `recurs_in`
- `contradicts`
- `mutates_into`
- `feels_like`
- `belongs_to_franchise_cluster`

This would let refinement ask questions like:
- Which props most often correlate with strong contradiction ledgers?
- Which archetype combinations produce the funniest menace?
- Which titles are overrepresented but still productive?
- Which phrases are becoming HallTime doctrine?

### D. Editorial Model Pass

After retrieval, a second model pass should evaluate candidate artifacts in an explicitly editorial way.

That pass should be asked to:
- identify strongest motifs
- identify dead repetition
- compare similar broadcasts
- nominate best titles and sub-franchises
- compress multiple similar outputs into a stronger canonical version
- explain why some ideas worked and others did not

This is not another brainstorm.
This is machine-assisted curation.

## What Refinement Should Produce

The refinement stage should output artifacts like:
- `best_of_batch.md`
- `franchise_clusters.json`
- `recurring_doctrine.md`
- `failed_patterns.md`
- `editorial_notes.jsonl`
- `canon_candidates.md`

Examples:
- best five casserole movies and why one became the dominant casserole variant
- strongest uses of "just storage"
- best shared-universe callbacks to the vineyard fire
- weakest repeated title families and why they collapsed
- strongest contradiction patterns worth formalizing into doctrine

## Why This Matters Artistically

If HallTime only generates thousands of weird artifacts, that is amusing.

If HallTime also documents how an artificial system brainstormed, repeated itself, discovered motifs, and then refined its own output under editorial pressure, that becomes a more distinct experiment.

Then the project is not simply:
- AI made content

It becomes:
- AI participated in a serialized creative process
- the corpus became searchable memory
- recurring mistakes became style
- refinement decisions became observable
- the machine's own taste formation became part of the work

That is much more interesting.

## Practical Near-Term Plan

### Step 1

Keep generating broadcast artifacts exactly as we are doing now.

### Step 2

Add a corpus indexer that extracts structured fields from every JSON broadcast into one searchable file.

### Step 3

Add retrieval commands for:
- nearest neighbor broadcasts
- title-family grouping
- motif frequency
- contradiction family grouping
- top-scoring outputs by metric

### Step 4

Add a refinement pass that takes:
- one current candidate
- a retrieved comparison set
- a relevant concept neighborhood
- explicit editorial instructions

Then asks the model to produce:
- what worked
- what failed
- what should be kept
- what should be condensed
- what should become canon

### Step 5

Publish the process documentation alongside the artifacts.

## Recommended Documentation Principle

Do not present HallTime as "the AI autonomously wrote movies."
That is too shallow and too generic.

Present it more honestly:
- a procedural doctrine generated the structural field
- a language model contributed ideation and expansion
- unattended runs produced a searchable corpus
- later passes performed retrieval, comparison, and refinement
- the entire cycle was preserved as evidence

That framing is both more accurate and more novel.

## Current Status

As of May 28, 2026, HallTime has:
- a shared-universe doctrine
- archetype and character ecology files
- a procedural broadcast generator
- optional LM Studio expansion
- durable run logging
- a large batch of generated outputs suitable for editorial review

The missing piece is not generation.
The missing piece is taste-making.

That is the next experiment.
