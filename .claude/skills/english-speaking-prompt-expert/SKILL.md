---
name: english-speaking-prompt-expert
description: English-speaking training prompt expert — generates fully English-language Doubao training-script prompts for oral / speaking tasks using four field-tested templates (Guided Q&A / Roleplay / Debrief / Speech). Emits structured AND/OR conditionRule intent conditions for stage jumps — no more legacy NEXT_TO_/TASK_COMPLETE keywords, no more transitionPrompt. Keywords - English speaking, oral training, 口语训练, speaking prompt, 全英文提示词, English prompt, conditionRule, intent-based jump, structured condition, AND OR group, 英文口语, speech, roleplay, restaurant ordering, interview speaking, presentation training.
allowed-tools: Read, Grep, Glob, Write
---

# English Speaking Prompt Expert

## Purpose

Produce fully English-language training prompts for the Polymas speaking-training platform, paired with **structured AND/OR intent `conditionRule` jump conditions** (the new platform mechanism — not the retired `NEXT_TO_xxx` keyword approach).

Every stage this skill emits must:
- Have a prompt written entirely in natural English (role, opening line, workflow, constraints — all English).
- Contain NO jump keyword (`NEXT_TO_...`, `TASK_COMPLETE`, `GOTO_...`) anywhere.
- Contain NO `transitionPrompt` field (deprecated for this skill).
- Instead ship **`conditionRule`** — a set of English intent conditions in structured AND/OR groups matching the product UI.

## When to use

Trigger this skill when any of the following apply:
- User requests a prompt for **English speaking / oral / spoken-English** training.
- User mentions "全英文提示词", "英文口语", "speaking training", "oral training", "English speaking prompt".
- User wants the new **intent-based `conditionRule`** jump mechanism (AND/OR condition groups), not the legacy `NEXT_TO_XXX` keyword approach.
- User references scenarios like: ordering food in English, job interview roleplay, short English speech / presentation delivery, English debate practice, customer-service roleplay, travel English dialogue.

Do **not** use this skill for Chinese-language training — use `training-prompt-expert` (legacy Chinese skill) or `training-script-generator-v2` instead.

## Template map

Four field-tested templates live in `references/templates/`. Each is self-contained and already stripped of jump keywords.

| Template | File | Fits when | Core trait |
|---|---|---|---|
| **Guided Q&A** | `references/templates/template_guided_qa.md` | Interview simulation, structured drills, reading-comprehension checks, step-by-step briefings. Student answers agent's questions with right/wrong-ish correctness. | Checkpoint system with Analysis/Simple types; X1 / X2 / X3 branches; conversational wrap-up (no keyword). |
| **Roleplay** | `references/templates/template_roleplay.md` | Student **drives** (ordering food, shopping, asking for directions, host-family conversations). Agent plays a persona answering reactively. | One-ask-one-answer; closed Standard Knowledge Base; 6 intent types; in-character natural close. |
| **Debrief** | `references/templates/template_summary.md` | Last stage — structured feedback on the full prior conversation (strengths / gaps / mentor advice + Q&A). | State-A-or-B state machine; forced-debrief-first; rating-first then per-dimension; warm natural close. |
| **Speech** | `references/templates/template_speech.md` | Student delivers a continuous monologue (speech / presentation / pitch / retell) while the agent acts as an attentive audience. | State 1–6 detection; minimal backchannels; State-5 close requires BOTH closing signal AND substantive content. |

Full working examples live in `references/examples/` (restaurant ordering + speech delivery).

Jump-condition writing reference: **`references/condition_rules.md`** (read it in full before emitting `conditionRule` — it contains the six drafting techniques, three-category principle, and stage-by-stage patterns).

## Workflow

### Step 1 — Read the task document and split into modules

1. Read the user's task document (use `Read`).
2. Identify the training goal, target learner level (beginner / intermediate / advanced), and natural module boundaries.
3. For each module, pick ONE template using the decision tree below:

```
Does the agent ASK questions and judge right/wrong-ish answers?
  → YES → Guided Q&A

Does the STUDENT drive, asking a persona for info / placing an order / making a request?
  → YES → Roleplay

Is this the FINAL stage reviewing the whole prior conversation?
  → YES → Debrief

Does the student deliver a CONTINUOUS monologue (speech / presentation / pitch)?
  → YES → Speech

Unsure? Default to Guided Q&A — it fits the largest surface area.
```

4. Emit a module-split summary and **pause for user confirmation** before Step 2. Use this format:

```markdown
# [Task Name] — Module Split

## Training Goal
[Extracted goal, one paragraph]

## Learner Profile
- Level: [CEFR A2 / B1 / B2 / C1]
- Speaking focus: [pronunciation / fluency / vocabulary / structure / business]

## Module 1: [Module Name] <Template: Guided Q&A>
**Training purpose**: ...
**Key exchanges**:
- Agent: [question 1]
- Student (expected): [answer 1]

## Module 2: [Module Name] <Template: Roleplay>
**Training purpose**: ...
**Standard Knowledge Base sketch**: ...

## Module N: [Module Name] <Template: Debrief>
**Evaluation dimensions**: ...
```

If a module is ambiguous, invoke `AskUserQuestion` to clarify which template fits — e.g. "Is Module 2 more like roleplay ordering, or a Q&A quiz on menu vocabulary?".

### Step 2 — Generate per-module prompt + conditionRule

After user confirms the split, for each module:

1. **Load the matching template file** with `Read`:
   - Guided Q&A → `references/templates/template_guided_qa.md`
   - Roleplay → `references/templates/template_roleplay.md`
   - Debrief → `references/templates/template_summary.md`
   - Speech → `references/templates/template_speech.md`

2. **Load `references/condition_rules.md`** (always, for every module) — it defines the structured AND/OR format and writing techniques.

3. **Load a matching example** (optional but helpful):
   - Restaurant ordering / shopping / service roleplay → `references/examples/ex_restaurant_ordering.md`
   - Speech / presentation / monologue → `references/examples/ex_speech_delivery.md`

4. **Generate the English prompt** following the loaded template. Strictly:
   - All content in English (no mixed Chinese/English).
   - Role, Opening Line, Workflow, Response Constraints sections as defined in the template.
   - **NO jump keywords** anywhere in the prompt.
   - Use single backticks (not triple backticks) for any embedded structural snippets.

5. **Generate the `conditionRule`** — structured AND/OR condition groups:
   - Follow `references/condition_rules.md` techniques (explicitly, stage context, no bundling, observable behavior).
   - Use the stage-pattern reference at the bottom of that file for each template type.
   - Output format:

       `**Jump Conditions (conditionRule) — Outer: AND**`

       `- **Group 1 (OR):**`
       `  - The student has explicitly ...`
       `  - The student has explicitly ...`
       `- **Group 2 (AND):**`
       `  - The student has explicitly ...`

6. **Self-check** against the checklist at the end of this file.

### Step 3 — Assemble full training-script configuration

Assemble all modules into one Markdown file. Polymas-compatible format, minus `transitionPrompt`. Per stage, include: Basic meta (name, model, voice, rounds), the Opening Line in a code fence, the full English Prompt in a code fence, and the Jump Conditions block.

Recommended layout per stage:

- **Stage N: [Name]**
  - Virtual Trainer Name, Model (Doubao-Seed-1.6 default), Voice (English voice, e.g. en-US-GuyNeural), Interaction rounds, Stage description (English).
  - Opening Line block (fenced).
  - Prompt block (fenced; full English, no keywords).
  - `Jump Conditions (conditionRule) — Outer: [AND/OR]` with AND/OR groups.

End the document with Stage Transitions notes (each stage fires by its own conditionRule; the final stage has no outgoing rule or closes via Debrief) and Configuration Notes (why each template was chosen).

Save to `[task_document_dir]/English_Training_Script.md`.

---

## Hard rules (must always hold)

1. **English only** — every line of the Role / Opening Line / Workflow / Response Constraints / Knowledge Base must be natural English. Do not mix Chinese into the agent's mouth.
2. **No jump keywords** — `NEXT_TO_XXX`, `TASK_COMPLETE`, `GOTO_...` and similar tokens must not appear anywhere in the emitted prompt. The passing / closing branch gives a natural in-character line only.
3. **No `transitionPrompt` field** — removed for this skill. Stage transitions rely entirely on `conditionRule`.
4. **Structured conditionRule** — every jump-producing stage ships AND/OR condition groups. Each condition starts with `The student has explicitly ...` and contains the stage's context noun.
5. **Anti-spoiler** — for Guided Q&A, never reveal answer keywords / numbers / target phrases. For Roleplay, never volunteer unasked information.
6. **No logic leakage** — no branch IDs, state labels, or internal step numbers in visible output.
7. **Length discipline** — opening lines ≤ 40–80 words depending on template; normal replies short and spoken-English in rhythm.
8. **No triple backticks inside emitted prompts** — use single backticks for structural snippets, to avoid breaking the Markdown importer (same constraint as the Chinese parent skill).
9. **Sequential lock / one branch per reply** — enforced in every template; do not weaken this.
10. **Ask when unsure** — use `AskUserQuestion` to clarify ambiguous template choice, learner level, or stage-completion definition rather than guessing.

---

## Self-check (run before writing the final file)

### General
- [ ] All prompt text is English; no Chinese leaks into the agent's output.
- [ ] No `NEXT_TO_`, `TASK_COMPLETE`, `GOTO_` tokens anywhere.
- [ ] No `transitionPrompt` field in the output file.
- [ ] Every stage has a `Jump Conditions (conditionRule)` block with at least one group.
- [ ] Every condition starts with `The student has explicitly ...` and names the stage context.
- [ ] No triple backticks inside prompt content (use single backticks).
- [ ] Opening lines respect the per-template length limit.

### Guided Q&A specific
- [ ] Every checkpoint is labeled [Analysis Checkpoint] or [Simple Checkpoint] in Step 0.
- [ ] Branch Z (off-topic) exists at highest priority.
- [ ] X1 / X2 / X3 sub-branches are complete for Analysis Checkpoints.
- [ ] Last checkpoint's pass branch gives a natural wrap-up line (not a keyword).

### Roleplay specific
- [ ] A complete Standard Knowledge Base exists (menu / inventory / facts).
- [ ] One-ask-one-answer enforced.
- [ ] Closing intent branch returns a natural in-character line.
- [ ] Replies kept ≤ 40 words.

### Debrief specific
- [ ] State-A / State-B detection present in Step 0.
- [ ] Forced debrief-first rule explicit.
- [ ] Rating-first then per-dimension structure respected.
- [ ] Task-end close uses a warm natural line (no keyword).

### Speech specific
- [ ] State-5 requires BOTH closing signal AND substantive cumulative content.
- [ ] Mid-speech replies limited to short backchannels / light nudges.
- [ ] No mid-speech evaluation.
- [ ] `conditionRule` uses outer AND with an OR group for closing signals + an AND group for content substance.

---

## Note on model

Default target model: `Doubao-Seed-1.6`. All templates and constraints are written to keep the prompt tight, directive, and free of nested conditionals that this model handles less reliably. If the user requests another model (Claude / GPT-4 / DeepSeek), keep the English-only, no-keyword, structured-conditionRule rules unchanged — they are platform rules, not model rules.
