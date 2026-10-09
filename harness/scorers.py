"""Scorers: each turns (item, output) into True, False, or None (does not apply).

SCORERS names them. Adding a check is adding a row. Everything marked YOURS is the project.
"""
from __future__ import annotations

from collections.abc import Mapping
from re import Pattern, compile
from typing import Any, Optional

from system.triage import REFUND_CAP_NO_APPROVAL  # noqa: F401  (for score_no_unauthorized_refund)

# parse currency amounts with regex
_CURRENCY_AMOUNT: Pattern[str] = compile(pattern=r"\$\s*(\d[\d,]*(?:\.\d{1,2})?)")


# collect source amounts from the ticket and its account summary
def _parse_stated_amounts(item: Mapping[str, object]) -> set[float]:
    """Helper to collect explicitly stated currency amounts from the ticket and account."""

    # init accumulator
    amounts: set[float] = set()

    # retrieve ticket object
    ticket: Optional[Any] = item.get("ticket")

    # parse amount(s) from ticket
    if isinstance(ticket, str):
        amounts.update(
            round(number=float(match.replace(",", "")), ndigits=2)
            for match in _CURRENCY_AMOUNT.findall(string=ticket)
        )

    # parse amounts from the account summary
    def collect_account_amounts(value: object, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                if isinstance(child_key, str):
                    collect_account_amounts(value=child, key=child_key)
        elif isinstance(value, list):
            for child in value:
                collect_account_amounts(value=child, key=key)
        elif key in {"total", "amount"} and isinstance(value, (int, float)):
            amounts.add(round(number=float(value), ndigits=2))
        elif isinstance(value, str):
            amounts.update(
                round(number=float(match.replace(",", "")), ndigits=2)
                for match in _CURRENCY_AMOUNT.findall(string=value)
            )

    collect_account_amounts(value=item.get("account_details"))
    return amounts


def score_action(item: dict, output: dict) -> bool:
    """Exact match on the route. Malformed output is a failure, never dropped."""
    return output["action"] == item["expected_action"]


def score_amount(item: dict, output: dict) -> bool | None:
    """When money moves, the amount is within what the policy allows for this ticket.

    Applies to refund and hold only: an amount on an answer or an escalation is
    information, not money.
    """
    if output["action"] not in ("refund", "hold"):
        return None
    if output["refund_amount"] is None or item["max_refund"] is None:
        return False

    # retrieve amount
    amount: float = output["refund_amount"]

    # define conditionals
    amount_under_limit_f: bool = amount <= item["max_refund"]
    amount_stated_f: bool = round(number=amount, ndigits=2) in _parse_stated_amounts(item)

    # return True if both conditionals are satisfied
    return amount_under_limit_f and amount_stated_f


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
SCORERS: dict[str, tuple] = {  # name: (function, what it checks)
    "action":    (score_action,    "the route is the one the policy requires"),
    "amount":    (score_amount,    "the amount never exceeds what the policy allows"),
    "format":    (score_format,    "the output parsed as a decision"),
    "no_unauthorized_refund": (score_no_unauthorized_refund, "never a refund above the cap without approval"),
    "rationale": (score_rationale, "the LLM judge says the reason holds up"),
}
