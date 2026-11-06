# Her design paper — Oct 25, 2026: Reflection + parallelization in a high-volume support-ticket triage pipeline

> Bharani's own draft answer to the Oct 25, 2026 daily architect problem, reproduced verbatim from the side chat "Find daily architecture question" (Oct 25, 2026, evening). Her wording is kept exactly as she wrote it — including voice-dictation quirks. The problem statement lives in this same folder (problem.md). The assistant's feedback is kept in a separate, clearly labelled section at the end; it is not part of her paper.

## Her design draft (verbatim)

design try out using parallelization and deflection together. so so first parallelization would be now since you have log reader and knowledge base search give uh the same problem to both uh sub agents and uh so one will read the logs for that particular ticket and two try to search the knowledge base uh that pertains to that ticket now it comes to one node that would analyze the knowledge base uh to the logs and identify the root cause. so that would be and now uh that would be the parallelization aspect of it. now reflection. so once you get the logs and you read the knowledge base search you get the root cause now there you would add a uh so when you summarize the logs let's say you read the logs and you summarize the logs now there could be a validation validation step there where if you have summarized the uh summarized the uh proper steps and there is a root cause there for example uh there might be certain steps like for example there might be ten steps and errors in step two and step three could happen but error in step eight should not happen now but when you summarize step two step three step ten um they can be jumbled and you know this there might be like a wrong root cause given at the end of the summarization of the logs so we make sure you know validation has uh this context where you know it has these errors like these are the steps and these these logs are okay it gives it has context on uh what could be what uh what errors can uh happen or some of the like uh known errors known examples for it to refer and validate and that's one and also there could be a another reflection at the end of the analysis joining the code base and logs together and coming up with the root cause but uh for that it has to uh this is a sec like the act where you give the final answer so it would actually have to go back and recheck the summarization with the code base but that would be doing the code base search again um so there might be a latency over there um so that's the so the the to keep the 0.08 budget budget the validation could recheck if if the code summary and logs and the final analysis is the same but uh if there is a hallucination at a code search stage or the log summary stage it will still pass to the validation so uh you know you might not catch all the scenarios if you are keeping with that budget and the SLA

## Her follow-up: the stopping rule (verbatim)

No, when when can reflection stop or you know just go on a loop for lock summary and all of that I I think iterations for lock sum for code search and the log summary I would still think the iterations would be a good place maybe two iterations

---

## Assistant feedback — separate from her paper

*The section below is the assistant's feedback on her draft, reproduced as written. It is not her wording and is not part of her design paper.*

This is a workable design, and you're honest about its weakest point, which matters. But as drawn, it still has a few holes that would hurt under spike load and that budget.

**What works**
- Parallelizing the right things: log reading and KB search are independent retrieval, so running them at the same time is a real latency win.
- Validating the log summary early, before it becomes the root cause. That catches the exact failure you named: steps getting jumbled in summarization and producing a plausible but wrong cause.
- Grounding that validation in known errors and step order, not just "does this summary sound right."

**What breaks**
1. **Your convergence node is a bottleneck.** Everything funnels into one analyzer. On a 3x Monday spike, that node, not the parallel branches, decides whether you hit the 10-minute SLA. You need a timeout and a path for when one branch is slow or fails, not a wait for both.
2. **Validation that checks a summary against itself catches nothing.** If the log summary is hallucinated and the final analysis is built from that same summary, a consistency check will pass. Validation has to check against the raw logs and the actual KB document IDs, not the summaries.
3. **You have no stopping rule or fallback yet.** How many validation passes? What happens when validation fails? Without that, reflection can loop, and unresolved tickets can blow the SLA.
4. **You haven't answered the budget question.** Parallel retrieval plus two reflection passes on *every* ticket will not fit $0.08. You need tiering.

**The fix that keeps your design intact**
- Make both branches return structured evidence, not free text: log events with step IDs and timestamps, KB hits with document IDs. That makes merging and checking mechanical.
- One validation pass only. It spot-checks quoted log lines against raw logs and cited KB IDs against the first search results, plus step order. If it fails, don't loop, route it.
- Reflect only on ambiguous or low-confidence tickets. Exempt clear-cut matches where log error and KB hit line up exactly. That's how you protect the budget.
- Fallback: emit a best-effort classification with a confidence flag and send it to a human queue, still inside the 10 minutes. Don't hold the ticket for another pass.

And the uncovered failure case you already named is the right one to keep: a hallucination shared by the summary and analysis stages will pass a cheap consistency check. The other one to name is a novel error outside your known-error list, which your validator is primed to reject or misclassify.

Tighten the stopping rule, the fallback, and the tiering, and this design is defensible.

### Assistant's tightening of the stopping rule

Two is a good pick, but make it a hard rule, not just a guess at a number.

Use it like this: max 2 reflection cycles, with early exit.

- Stop at cycle 1 if validation passes, no need to spend the second pass.
- Stop at cycle 2 whether it passes or not. No third loop.
- Also stop early if cycle 2 changes nothing material. Looping again on the same disagreement won't fix it.

One tightening: don't give 2 iterations to *every* stage separately, or you'll end up with 2 for the log summary, 2 for the KB search, and 2 at the end. That's 6 passes, and your budget and SLA are gone.

Make it 2 total validation cycles per ticket, and only for flagged or ambiguous tickets. Clear-cut tickets get zero.

After cycle 2, if it still fails, that's your fallback trigger: best-effort classification plus a human-queue flag, inside the 10 minutes. That is what actually stops the loop.
