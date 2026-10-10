# Making the Research Agent Adaptive — What We Built and Why

**Project:** Self-Learning Research Agent
**Feature:** Adaptive plan refinement — letting the agent notice what it missed and go look for it
**Status:** Steps 1 & 2 complete and tested. Step 3 (wiring into the live pipeline) is next.

---

## Part 1 — The Big Picture (read this even if you're not technical)

### The problem, in plain terms

Imagine you ask a research assistant: *"Tell me about electric vehicle battery degradation."*

A good human researcher would:
1. Look into it.
2. Write up what they found.
3. Read back over their own notes and think: *"Wait — I never actually found out how LFP batteries compare to NMC batteries. Let me go look that up specifically before I finish."*
4. Do one more focused search, then write the final report.

Our agent, before this change, could only do steps 1 and 2. It never did step 3. It wrote whatever report it could from the first round of searching — even if it privately "knew" (in the sense that its own analysis step said so) that something important was missing. It just shipped the report with the hole still in it.

### What we're building

We're teaching the agent to do step 3: **notice its own gaps, and go do one more targeted search to fill them** — before writing the final report. This is the difference between a research assistant who does one pass and hopes for the best, versus one who double-checks their own work.

### Why this matters

- **Better answers**: reports will have fewer "the sources don't really cover X" moments, because the agent actively goes back for X instead of shrugging and moving on.
- **This is the single highest-value improvement** we identified for the whole project — bigger than any speed or infrastructure fix, because it changes what the agent *does*, not just how reliably it does it.

### How we're building it (safely)

Big changes to a working system are risky if done all at once — if something breaks, you don't know which of five changes caused it. So we're building this in small, separately-tested pieces:

1. **Step 1** — Teach the "analysis" part of the agent to write down what it's missing (instead of just quietly noticing and ignoring it).
2. **Step 2** — Teach the "planning" part of the agent to turn that list of gaps into 1-2 smart, specific follow-up questions to search for.
3. **Step 3 (next)** — Actually connect these two pieces into the live pipeline, so a real research run uses this loop automatically.

We are currently done with Steps 1 and 2, and we tested Step 2 extremely thoroughly (more on that below) before touching anything live.

---

## Part 2 — Step 1: Teaching the Agent to Notice Its Own Gaps

### Why

The "Synthesizer" — the part of the agent that reads all the search results and writes up the key findings — was already implicitly capable of noticing gaps (its instructions even mentioned "note limitations"). But it had no structured way to *report* that. It was like an employee who notices a problem but has no form to write it up on — so the observation just evaporates.

### What we changed

We gave the Synthesizer three things to hand back instead of one:
1. **Findings** — what it already did (the actual facts learned).
2. **Gaps** — a new, explicit list: "here's what I looked for and couldn't confirm."
3. **Confidence** — a simple rating (high / medium / low) of how well the research actually covered what was asked.

### How (technical summary)

- **`src/state.py`**: added three new fields to the shared research state — `research_gaps` (a list of text descriptions), `synthesis_confidence` (high/medium/low), and `refinement_count` (a counter we'll use later to prevent infinite loops).
- **`src/prompts/synthesizer.py`**: changed the instructions given to the LLM so that instead of returning a bare list of findings, it now returns one structured object: `{"findings": [...], "gaps": [...], "confidence": "..."}`.
- **`src/agents.py`** (`ResearchSynthesizer` class): rewrote the parsing logic (`_extract_synthesis_output`) to read this new structured format, with safety fallbacks in case a smaller/local model doesn't format its output perfectly (it degrades gracefully instead of crashing).

**Important design choice:** this step was deliberately "inert" — nothing in the live pipeline reads `research_gaps` yet. It's plumbing only. That let us verify the Synthesizer was actually producing sensible gaps before building anything that acts on them.

---

## Part 3 — Step 2: Teaching the Agent to Act on Its Gaps

### Why

Noticing a gap is useless if nothing happens next. Step 2 gives the agent a way to turn "here's what I'm missing" into "here's a smart, specific search to go fill that hole" — without wastefully re-searching things it already knows, and without inventing busywork when there's nothing real to search for.

### What we changed

We added a brand-new capability to the "Planner" part of the agent, called `refine_plan()`. Given:
- the original topic,
- what's already been found,
- and the list of gaps,

...it produces up to 2 new, narrow search queries — one per real gap — or **zero**, if none of the gaps are actually worth searching for.

That last part — knowing when to do *nothing* — turned out to be the hardest and most important part to get right, and is most of what Step 2's testing effort went into.

### How (technical summary)

- **`src/prompts/planner.py`**: added two new prompt templates, `PLANNER_REFINE_SYSTEM_PROMPT` and `PLANNER_REFINE_USER_TEMPLATE`, dedicated to this second-pass, gap-filling task (kept completely separate from the original first-pass planning prompt).
- **`src/agents.py`** (`ResearchPlanner` class): added a new method, `refine_plan()`, following the same retry/error-handling/token-tracking pattern as the rest of the codebase. On any failure, it fails *safely* — it lets the pipeline continue to write a report with what it already has, rather than crashing the whole research run.
- **`src/callbacks.py`**: added two new progress-update events (`emit_refinement_start`, `emit_refinement_complete`) so the UI can show "Refining research plan..." as a visible stage.
- **`src/prompts/__init__.py`**: exported the two new prompt templates.

### The testing process (this is the part worth understanding, technical or not)

Before touching the live pipeline, we built a standalone test script (`test_refine.py`) that calls `refine_plan()` directly with made-up ("fake") research scenarios — no real search, no real LLM research run, just: *"here's a topic, here's what was already found, here are the gaps — what would you do?"*

We deliberately designed four **adversarial** test cases — not friendly ones — because a feature like this is only trustworthy if it behaves correctly on the tricky cases, not just the easy ones:

| Test | What it checks | What "success" looks like |
|---|---|---|
| **A — Vague gaps** | Does the agent invent a fake-specific query when the gap is really just "needs more research"? | It should return **nothing** |
| **B — Overlapping gaps** | Does the agent accidentally re-search something it already found? | It should keep the genuinely new query, drop the duplicate |
| **C — Too many gaps** | Given more gaps than its query budget, does it pick the *best* ones? | It should choose the specific gaps over the vague ones |
| **D — Specific-sounding but unanswerable** | Does the agent confuse "phrased precisely" with "actually findable on the public web"? | It should recognize private/future/unknowable info and return **nothing** |

### What we found and fixed along the way

Nothing about this process was "write once and it worked" — that's normal and expected for prompt-driven behavior, and worth documenting honestly:

1. **First attempt**: Tests A and B failed. The model was treating "up to 2 queries" as "always give me 2," so it invented plausible-sounding queries even for meaningless gaps, and repeated ground it had already covered.
   - **Fix**: rewrote the prompt to explicitly say zero or one query is a *normal, correct* outcome, added a hard rule against duplicating existing findings, and added a worked example showing the model exactly what "correctly skipping" looks like.

2. **A code bug surfaced**: after the prompt fix, the code itself crashed with a template-formatting error. This was a genuine software bug, not a prompt issue — a JSON example inside the prompt was being processed twice by two different formatting systems, and the second pass choked on it.
   - **Fix**: changed how the prompt is passed into the LLM-calling code so it's only formatted once, at the right time. (Good lesson: always separate "is this a model behavior problem" from "is this a code problem" — they need completely different fixes.)

3. **After the bug fix**: Tests A, B, and C passed. Test D failed — the model generated a search query for a company's *private internal headcount*, which sounds specific but is never publicly searchable information.
   - **Fix**: added a second worked example specifically teaching the difference between "specific-sounding" and "actually findable," and tightened the rule about what counts as a valid gap.

4. **Final verification**: re-ran all four tests, including re-checking A/B/C after the Test-D fix (to make sure fixing one problem didn't quietly break something that was already working). All four passed.

### Why this level of testing mattered

This is the core discipline behind building something genuinely reliable rather than something that merely *looks* like it works in a demo: **every fix gets tested against everything it might have broken, not just the thing it was meant to fix.** That's exactly what separates a fragile prototype from something trustworthy enough to put in front of real users — and it's part of what will make this agent better than the average "wire an LLM to some tools and hope" project.

---

## Part 4 — Where Things Stand Right Now

- ✅ The Synthesizer can identify and report specific gaps in its own research, along with a confidence rating.
- ✅ The Planner can take those gaps and generate smart, targeted follow-up searches — and, just as importantly, knows when to generate *nothing* rather than invent busywork.
- ✅ Both pieces are individually tested and verified against adversarial cases, in isolation, with no risk to the live app.
- ⏳ **Not yet done**: these two pieces are not yet connected to the actual research pipeline. Today, if you run the app end-to-end, it still behaves exactly as before — this was intentional, to de-risk the work.

## Part 5 — What's Next: Step 3

Step 3 connects everything above into the live LangGraph pipeline:

1. Add a new `refine_plan` node to the graph (`src/graph.py`), sitting between `synthesize` and `write_report`.
2. Add a routing rule: after synthesis, if there are real `research_gaps`, go to `refine_plan` → then back to `search` for one more focused round. If there are no gaps (or confidence is already high), skip straight to writing the report.
3. **Fix a real technical risk we've already identified**: the `search` node currently *overwrites* all previous search results every time it runs. If we loop back into it for a second pass, as-is it would delete the first pass's results. This needs to be fixed so a second search pass *adds to* the existing results rather than replacing them.
4. Add a hard cap (using the `refinement_count` field we already added in Step 1) so the agent can never loop more than once or twice — an adaptive agent should still have a hard stop, not the ability to search forever.

This is the step where the feature goes from "built and tested in isolation" to "actually changes what a real research run produces."
