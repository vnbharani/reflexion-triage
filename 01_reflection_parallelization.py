"""Illustrative sketch: reflection + parallelization in ticket triage.

Core mechanism only — NOT a solution to the design problem, and NOT
production code. It shows one idea in miniature:

  1. Independent analyses (log reader + knowledge-base search) fan out
     in parallel — neither depends on the other's output, so running
     them sequentially would just add their latencies.
  2. Reflection is *selective*: it runs only when the first-pass result
     is low-confidence or ambiguous. High-confidence tickets skip it,
     which is what keeps the per-ticket cost inside budget.
  3. A hard stopping rule caps reflection at MAX_REFLECTION_ROUNDS.
     When it is exhausted without a confident answer, the ticket goes
     to the fallback route (human queue) instead of looping forever.

Run:  python3 01_reflection_parallelization.py
"""

from concurrent.futures import ThreadPoolExecutor
import time

# Hard stopping rule: never reflect more than this many times per ticket.
MAX_REFLECTION_ROUNDS = 2
# Confidence below this triggers reflection; at/above it, ship the answer.
CONFIDENCE_THRESHOLD = 0.7


def read_logs(ticket_id: str) -> dict:
    """Stand-in for the log-reader tool. Returns a candidate root cause."""
    time.sleep(0.05)  # simulate tool latency
    # Ambiguous logs (ticket T-102) produce a shaky first guess.
    if ticket_id == "T-102":
        return {"cause": "unclear — timeout or auth failure?", "confidence": 0.4}
    return {"cause": "disk full on worker node", "confidence": 0.9}


def search_kb(ticket_id: str) -> dict:
    """Stand-in for the knowledge-base search tool."""
    time.sleep(0.05)
    if ticket_id == "T-102":
        return {"match": "known issue: expired API token", "confidence": 0.5}
    return {"match": "known issue: disk-full runbook", "confidence": 0.85}


def reflect(ticket_id: str, draft: dict, round_no: int) -> dict:
    """Reflection pass: re-examine the draft against both sources.

    Each round can raise confidence; here round 2 resolves T-102 by
    favouring the KB match over the ambiguous log reading.
    """
    if ticket_id == "T-102" and round_no == 2:
        return {"cause": "expired API token (KB match)", "confidence": 0.8}
    # A round that finds nothing new returns the draft unchanged —
    # the stopping rule, not the model, is what ends the loop.
    return draft


def triage(ticket_id: str) -> dict:
    """Triage one ticket: parallel fan-out, selective reflection, fallback."""
    # 1. Fan out the independent analyses in parallel.
    with ThreadPoolExecutor(max_workers=2) as pool:
        log_future = pool.submit(read_logs, ticket_id)
        kb_future = pool.submit(search_kb, ticket_id)
        log_result = log_future.result()
        kb_result = kb_future.result()

    # Combine: the weaker signal sets the draft's confidence.
    draft = {
        "cause": log_result["cause"],
        "kb_match": kb_result["match"],
        "confidence": min(log_result["confidence"], kb_result["confidence"]),
    }

    # 2. Reflect only on low-confidence / ambiguous drafts.
    rounds = 0
    while draft["confidence"] < CONFIDENCE_THRESHOLD and rounds < MAX_REFLECTION_ROUNDS:
        rounds += 1
        draft = reflect(ticket_id, draft, rounds)

    # 3. Hard stop: if reflection is exhausted and confidence is still
    #    low, do NOT keep looping — route to the human fallback.
    if draft["confidence"] < CONFIDENCE_THRESHOLD:
        return {"ticket": ticket_id, "route": "human_queue (fallback)",
                "reason": f"unresolved after {rounds} reflection round(s)",
                "draft": draft}

    return {"ticket": ticket_id, "route": "auto_answer",
            "reflection_rounds": rounds, "draft": draft}


def main() -> None:
    for ticket_id in ("T-101", "T-102", "T-103"):
        result = triage(ticket_id)
        print(f"{result['ticket']}: route={result['route']}", end="")
        if "reflection_rounds" in result:
            print(f" | reflection rounds={result['reflection_rounds']}"
                  f" | cause={result['draft']['cause']}"
                  f" (conf {result['draft']['confidence']})")
        else:
            print(f" | {result['reason']}"
                  f" | draft cause={result['draft']['cause']}"
                  f" (conf {result['draft']['confidence']})")


if __name__ == "__main__":
    main()
