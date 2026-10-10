# Self-Learning Research Agent — Improvement Plan

**Purpose:** Take this project from a strong prototype to a deployable, portfolio-grade system.
**How to use this doc:** Work top to bottom within each phase. Phase 1 items are cheap and high-impact — do those first, today if possible.

---

## Phase 1 — Do First (Security & Safety Fixes)

These are quick fixes that remove real risk before anyone else touches the app.

- [ ] **Harden URL/SSRF validation in `src/utils/web_utils.py`**
  Current `BLOCKED_HOSTS` only blocks literal strings (`localhost`, `127.0.0.1`, etc.). It does not block private IP ranges or the cloud metadata endpoint.
  - Resolve the hostname to an IP before fetching.
  - Reject IPs in `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16` (cloud metadata), and IPv6 private/link-local ranges.
  - Consider Python's `ipaddress` module: `ipaddress.ip_address(ip).is_private`.

- [ ] **Fail fast on missing config**
  In `src/config.py`, `validate_config()` exists but confirm it's actually called at startup for every provider path (not just Ollama/llama.cpp which self-check). Add a startup check in `main.py` / `app.py` that calls `config.validate_config()` before the graph is built, so a missing API key fails immediately with a clear message instead of failing mid-research.

- [ ] **Add basic rate limiting to the Chainlit app**
  Even a simple per-session counter (e.g., max N research runs per hour per session) prevents runaway cost if this is ever shared with others.

- [ ] **Remove/rotate any committed cache artifacts**
  `.cache/research/cache.json` and `.cache/research_history.json` are present in the zip. Confirm these are gitignored (they are, per `.gitignore`) but scrub them from the shipped project directory before any public sharing — they may contain content from past queries.

---

## Phase 2 — Testing Foundation

No tests currently exist despite `pytest` being listed as a dependency. This is the highest-leverage investment for reliability.

- [ ] **Unit tests for pure-logic modules (easiest wins, do these first):**
  - `src/utils/credibility.py` — scoring logic
  - `src/utils/citations.py` — citation formatting per style (APA/MLA/Chicago/IEEE)
  - `src/utils/cache.py` — TTL expiry logic
- [ ] **Integration test for the full graph** (`src/graph.py`)
  - Mock the LLM calls and search provider.
  - Run `create_research_graph()` end-to-end on a fixed fake topic.
  - Assert the state machine reaches `write_report` and produces a non-empty `final_report`.
  - Assert it correctly routes to `END` early when a stage returns no results (test each `should_continue_after_*` branch).
- [ ] **Set up `pytest` config** in `pyproject.toml` (test paths, markers for slow/integration tests).
- [ ] **Add a coverage report** (`pytest-cov`) and put the badge in the README once CI exists.

---

## Phase 3 — Deployment Infrastructure

- [ ] **Write a `Dockerfile`**
  - Multi-stage build: install deps, copy source, run as non-root user.
  - Expose the Chainlit port.
- [ ] **Write a `docker-compose.yml`**
  - Bundle the app + Ollama service together for a true one-command local demo (`docker compose up`).
- [ ] **Set up CI (GitHub Actions)**
  - On every PR: run `ruff` (lint), `black --check` (format), `pytest` (tests).
  - Optionally build the Docker image to confirm it still builds.
- [ ] **Add environment-based config profiles** (dev / staging / prod) so credibility thresholds, cache TTLs, etc. can differ by environment without editing code.

---

## Phase 4 — Observability

- [ ] **Wire up LangSmith tracing properly** (already partially scaffolded in `config.py` via `LANGCHAIN_TRACING_V2`) — document how to enable it in the README.
- [ ] **Expose `llm_tracker.py` data as a simple dashboard or log summary** — cost per report, tokens per stage, so you can answer "how much does one research run cost?"
- [ ] **Add structured logging** (the `structlog` dependency is listed but confirm it's actually used consistently — right now `logging.basicConfig` is called ad hoc in multiple files, which can cause duplicate handlers).

---

## Phase 5 — Product / Feature Improvements

- [ ] **Human-in-the-loop checkpoint**: let the user review/edit the generated plan (queries + outline) before the searcher runs. LangGraph supports interrupts — this is a natural extension of the existing checkpointing code.
- [ ] **Parallelize search queries** — confirm `max_parallel_searches` in `config.py` is actually enforced with `asyncio.gather`, not run sequentially.
- [ ] **Expand search sources** for research-heavy topics — arXiv / Semantic Scholar / PubMed connectors alongside DuckDuckGo/Tavily, selected based on topic domain.
- [ ] **Streaming progress in the UI** — `src/callbacks.py` already tracks stage progress; surface it live in Chainlit ("Planning… Searching 2/3 queries… Synthesizing…") rather than only at the end.
- [ ] **REST API layer** (FastAPI, already a transitive dependency) so the agent can be called programmatically, not just via chat UI.

---

## Phase 6 — Evaluation & Credibility (what makes this stand out)

- [ ] **Build a small labeled benchmark set** — 10–20 research topics with manually reviewed expected quality bars (citation accuracy, factual grounding, completeness).
- [ ] **Score automatically** on that benchmark after every significant prompt/agent change, so regressions are caught, not guessed at.
- [ ] **Publish real numbers in the README**: average report generation time, cost per report by provider, citation accuracy rate — replacing the current unverified "production-ready" framing with evidence.
- [ ] **Baseline comparison**: run the same topics through a single-LLM one-shot baseline (no multi-agent pipeline) and show the measurable quality difference. This is the single best piece of evidence for why the multi-agent architecture is worth the added complexity.

---

## Suggested Order of Operations (Today → This Month)

| Timeframe | Focus |
|---|---|
| Today | Phase 1 (all items) — these are small, high-risk-reduction fixes |
| This week | Phase 2 — get a test suite in place, even a minimal one |
| Next 1–2 weeks | Phase 3 — Docker + CI, so the project is reproducible for anyone |
| Ongoing | Phase 4 (observability) alongside Phase 5/6 as time allows |

Start with Phase 1 today — it's the fastest way to remove real risk before anything else changes.
