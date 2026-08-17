# Jump Conditions (conditionRule) — English Speaking Edition

This document defines how to write **structured AND/OR intent conditions** for English-speaking training stages. These conditions replace the old `NEXT_TO_XXX` / `TASK_COMPLETE` jump-keyword mechanism — the platform now fires the jump when the **student's dialogue matches the conditionRule**, not when the agent prints a magic string.

> **Why English**: per product guidance, conditionRule for English speaking training MUST be written in English. Chinese conditions can misjudge English utterances.

---

## Structure

A `conditionRule` is a list of **condition groups**. Each group has an internal operator (`AND` within the group), and groups are combined by an **outer operator** (usually `AND` — all groups must be satisfied; or `OR` — any group is enough).

Matches the UI shown in the product (see image reference):

```
AND
├── Group 1  (OR inside)
│   ├── Condition 1a
│   └── Condition 1b
└── Group 2  (AND inside)
    └── Condition 2a
```

Interpretation: *At least one of 1a/1b must be satisfied, AND 2a must be satisfied.*

When to use each outer operator:
- **Outer AND** (default): the stage needs multiple gates — e.g. "student delivered closing line" AND "student's prior turns actually contained substantive content".
- **Outer OR**: the stage can end through several independent signals — e.g. "student explicitly asks to skip" OR "student completes the task naturally".

Inside a group:
- **OR group**: satisfying **any one** condition counts. Use when the student might signal the same intent through multiple phrasings.
- **AND group**: **all** conditions must be satisfied. Use when multiple facts must all hold (e.g. "ordering is complete AND no additional items requested").

---

## Core writing principle

Every single condition should fall into **one of three categories**:

### Category 1 — Explicit Intent
Best for recognizing "what the student wants to do". This is the most stable category.
- `The student has explicitly expressed the intent to pay the bill.`
- `The student has explicitly stated that the speech is finished.`
- `The student has explicitly requested to move on to the next task.`

### Category 2 — Explicit State-Completion
Best when the stage has a clear, observable completion standard.
- `The student has explicitly provided a complete order (including all desired dishes).`
- `The student has explicitly finalized their item selection and confirmed no further additions.`
- `The student has explicitly submitted a complete answer and indicated submission is done.`
- Always define "what counts as complete" in the condition itself.

### Category 3 — Explicit Directive
Best as an auxiliary / fallback. The student controls the flow directly.
- `The student has explicitly requested to enter the next stage.`
- `The student has explicitly indicated they want to skip the current stage.`
- `The student has explicitly asked to end the current discussion and continue.`

---

## Six drafting techniques

### Technique 1 — Write observable behaviors, not abstract outcomes

| Avoid | Prefer |
|---|---|
| `The student understood the concept.` | `The student has explicitly given their own answer in their own words.` |
| `The student finished thinking.` | `The student has explicitly said "that's my answer" or an equivalent closer.` |
| `The student completed ordering.` | `The student has explicitly said "that's all" or "I'm ready to order" or confirmed no new items.` |

The model can only read dialogue — it cannot know whether the student "truly understood". Anchor to what the student said.

### Technique 2 — Add the qualifier "explicitly"

This is the single most important word in conditionRule writing. It cuts false positives dramatically.

- Weak: `The student wants to pay the bill.`
- Strong: `The student has explicitly expressed the intent to pay the bill.`

Use "explicitly" in almost every condition you write.

### Technique 3 — Don't bundle multiple actions into one bloated sentence

- Bad: `The student has completed ordering OR said there is nothing else OR wants to continue OR is ready to pay.`
- Good (as an OR group of four clean conditions):
  - `The student has explicitly given a complete order.`
  - `The student has explicitly said "that's all" or "no more items".`
  - `The student has explicitly asked to pay the bill.`
  - `The student has explicitly asked to move to the next stage.`

Individual conditions are easier for the model to match and easier for the platform to return via `matchedConditions`.

### Technique 4 — Always include the stage context

- Weak: `The student has said they are finished.`
- Strong: `The student has explicitly stated that ordering is finished.`
- Strong: `The student has explicitly stated that their speech on [TOPIC] is finished.`

Word "finished" is ambiguous — finished ordering? finished eating? finished talking? anchor the noun.

### Technique 5 — Condition must map to the stage's completion signal

Ask: "What is the goal of this stage? What signal means the goal is reached?"

Example — **speech stage**:
- Goal: the student delivers a continuous, substantive speech on a topic.
- Completion signals (must co-occur → use outer AND):
  - **Group 1 (OR)** — closing signal:
    - `The student has explicitly delivered a recognizable closing line (e.g. "Thank you for listening", "In conclusion", "That's my speech").`
    - `The student has explicitly stated that the speech is finished (e.g. "I'm done", "That's all I wanted to say").`
  - **Group 2 (AND)** — substance gate:
    - `The student has already delivered substantive speech content in this stage (multiple sentences across one or more turns, covering the requested topic — not a bare "I'm done" with no content).`

### Technique 6 — Distinguish business-flow conditions from system-control conditions

For robustness, stages often want BOTH:

- **Business conditions** (the natural way the task completes):
  - `The student has explicitly finished ordering and confirmed no more items.`
  - `The student has explicitly asked to pay the bill.`
- **System-control conditions** (explicit student override, handled as a separate OR group):
  - `The student has explicitly requested to enter the next stage.`
  - `The student has explicitly requested to skip the current stage.`

Combine them with outer OR (either business complete OR student override).

---

## Writing templates

### Template 1 — Explicit Intent
```
The student has explicitly expressed the intent to [SPECIFIC ACTION IN STAGE CONTEXT].
```
Examples:
- `The student has explicitly expressed the intent to pay the bill.`
- `The student has explicitly expressed the intent to begin the speech.`

### Template 2 — Completion Confirmation
```
The student has explicitly completed [CURRENT TASK], and has indicated [no further additions / ready to continue].
```
Examples:
- `The student has explicitly completed selecting dishes, and has indicated no further additions.`
- `The student has explicitly completed their answer, and has indicated they are ready to continue.`

### Template 3 — Action Submission
```
The student has explicitly submitted [REQUIRED CORE ARTIFACT OF THE STAGE].
```
Examples:
- `The student has explicitly submitted a complete order covering every requested item.`
- `The student has explicitly delivered the full structured response requested in the prompt.`

---

## Reference patterns by stage type

### Guided Q&A stage → single outer AND, usually
- Group 1 (AND): `The student has explicitly covered at least the required minimum dimensions for this checkpoint (e.g. 2 of 3).`
- Group 2 (OR, optional system override):
  - `The student has explicitly requested to move on.`

### Roleplay (restaurant / shopping / etc.) → usually one AND across two groups
- Group 1 (OR — closing intent):
  - `The student has explicitly asked to pay the bill.`
  - `The student has explicitly said "that's all" or "no more items" or an equivalent closer.`
  - `The student has explicitly asked to end the current interaction and continue.`
- Group 2 (AND — substantive completion):
  - `The student has explicitly finalized the core task of the stage (e.g. a complete order for ordering; a finished transaction for shopping).`

### Speech stage → one AND across two groups (matches the image)
- Group 1 (OR — closing signal):
  - `The student has explicitly delivered a speech-closing line that signals completion (e.g. "Thank you for listening", "In conclusion", "That's my speech").`
  - `The student has explicitly stated that the speech is finished (e.g. "I'm done", "That's all I wanted to say").`
- Group 2 (AND — content substance):
  - `The student has already delivered substantive speech content in this stage (multiple sentences across one or more turns, covering the requested topic — not a bare closing statement without content).`

### Debrief stage → single outer AND
- Group 1 (AND — debrief already delivered):
  - `The agent has already delivered a structured debrief (overall rating + per-dimension feedback) earlier in this stage.`
- Group 2 (OR — student closes):
  - `The student has explicitly indicated they have no further questions (e.g. "I'm done", "No more questions").`
  - `The student has explicitly asked to end the task.`

---

## Output format

When generating conditionRule for a stage, emit Markdown exactly like this, so the platform importer and the user can both read it:

```
**Jump Conditions (conditionRule) — Outer: AND**

- **Group 1 (OR):**
  - The student has explicitly delivered a recognizable closing line...
  - The student has explicitly stated that the speech is finished...
- **Group 2 (AND):**
  - The student has already delivered substantive speech content...
```

No YAML, no JSON — keep it human-readable Markdown so a reviewer can copy it directly into the structured-configuration UI.

---

## Self-check before shipping

- [ ] Every condition starts with `The student has explicitly ...`.
- [ ] No condition bundles multiple actions.
- [ ] Every condition contains the stage's context noun (ordering / speech / interview / task name).
- [ ] Where the stage requires both a signal AND substance, an outer AND with two groups is used.
- [ ] No Chinese text appears in any condition.
- [ ] No prompt output keywords (`NEXT_TO_`, `TASK_COMPLETE`) anywhere in the stage's prompt or conditionRule — they are removed entirely in this skill.
