# Reflection + parallelization in a high-volume support-ticket triage pipeline

**Date:** Sunday, Oct 25, 2026 · **Status:** Answered · **Problem 01 of 13** — Daily Architect Problems

Part of *Daily Architect Problems* — thirteen applied agentic-design problems grounded in a real production agent. This folder is self-contained: publish it on its own as its own repo.

## The problem

An agent triaging 600 tickets a day, with 3x Monday-morning spikes, a 10-minute first-classification SLA, and an $0.08-per-ticket budget. Design triage using parallelization and reflection together: what fans out, where reflection sits, a hard stopping rule, and a fallback for unresolved tickets.

## How to use it

1. Read `problem.md` — the scenario, the task, and the self-check.
2. Write your answer as a design paper: the decision, the trade-offs, the numbers, and the failure case your design leaves uncovered.
3. Run the example to see one key mechanism as a working sketch: `python3 01_reflection_parallelization.py`
4. Use the self-check at the end of `problem.md` to test whether your design holds up.

## The example code

`01_reflection_parallelization.py` is an illustrative sketch of one core mechanism in this problem: parallel fan-out of log reading and knowledge-base search, with a reflection pass that only triggers on low-confidence or ambiguous results, a hard stop after 2 rounds, and a fallback route for unresolved tickets. It uses only the Python standard library. It is **not** the answer, **not** production code, and **not** the real agent's code — it is scaffolding to help you see the mechanism run.

## The solved paper

`reflection-parallelization.md` — my Oct 25 design draft, reproduced verbatim (including voice-dictation quirks), with the feedback it received kept in a separate, clearly labelled section. Read it after you've written your own paper, to compare decisions.

## Files

- `problem.md` — the full problem statement (scenario, task, self-check)
- `01_reflection_parallelization.py` — runnable example sketch
- `reflection-parallelization.md` — my solved design paper (verbatim draft) plus separate feedback

## References

- Shinn, Noah, et al. "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS 2023. arXiv:2303.11366. https://arxiv.org/abs/2303.11366 — the reflection pattern behind this problem; the repo takes its name from it.
- Gullí, Antonio. *Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems*. Springer, 2025. https://link.springer.com/book/10.1007/978-3-032-01402-3 — the pattern vocabulary this series studies (reflection, parallelization).
