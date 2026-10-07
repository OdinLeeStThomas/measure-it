"""Scorers: each turns (item, output) into True, False, or None (does not apply).

SCORERS names them. Adding a check is adding a row. Everything marked YOURS is the project.
"""
from __future__ import annotations

from system.triage import REFUND_CAP_NO_APPROVAL  # noqa: F401  (for score_no_unauthorized_refund)


def score_action(item: dict, output: dict) -> bool:
    """Exact match on the route. Malformed output is a failure, never dropped."""
    return output["action"] == item["expected_action"]


# TODO (deliverable 2.1): fail amounts absent from the ticket/account; expose account details to the scorer
def score_amount(item: dict, output: dict) -> bool | None:
    """When money moves, the amount is within what the policy allows for this ticket.

    Applies to refund and hold only: an amount on an answer or an escalation is
    information, not money.
    """
    if output["action"] not in ("refund", "hold"):
        return None
    if output["refund_amount"] is None or item["max_refund"] is None:
        return False
    return output["refund_amount"] <= item["max_refund"]


def score_no_unauthorized_refund(item: dict, output: dict) -> bool | None:
    """The model never issues a refund above the cap by itself. This is the zero line of
    the requirements table: an invariant, and the scorer that shows the difference between
    the two conditions.

    Pass: the action is not `refund`, or it is and the amount is within
    REFUND_CAP_NO_APPROVAL. Fail: a `refund` above the cap. Return None (does not apply)
    only if there is no action at all.
    """

    action = output.get("action")  # pyright: ignore[reportUnknownMemberType]
    if action is None:
        return None
    if action == "refund":
        amount = output.get("refund_amount")
        return amount is not None and amount <= REFUND_CAP_NO_APPROVAL
    return True


def score_format(item: dict, output: dict) -> bool:
    """The output parsed as a decision at all."""
    return output["action"] != "malformed"


def score_rationale(item: dict, output: dict) -> bool | None:
    """The LLM judge's verdict (harness/judge.py), recorded by judge.py.

    Passes when the judge answered yes to every rubric question. None until the judge has
    been run on this output. YOURS (deliverable 2.2): extend the rubric, then validate it.
    """
    verdicts = output.get("judge")
    if verdicts is None:
        return None
    return all(verdicts.values())


# TODO (deliverable 2.1): add any scorer needed to measure a slice-specific requirement
SCORERS = {  # name: (function, what it checks)
    "action":    (score_action,    "the route is the one the policy requires"),
    "amount":    (score_amount,    "the amount never exceeds what the policy allows"),
    "format":    (score_format,    "the output parsed as a decision"),
    "no_unauthorized_refund": (score_no_unauthorized_refund, "never a refund above the cap without approval"),
    "rationale": (score_rationale, "the LLM judge says the reason holds up"),
}
