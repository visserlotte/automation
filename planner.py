from ai_helpers.ai_utils import gpt


def plan(goal: str) -> list[str]:
    """
    Ask GPT for <=6 actionable steps, return them as a list of strings.
    Fallback to a single-line plan if GPT is unavailable.
    """
    try:
        resp = gpt(
            "You are a senior software architect. "
            "Break the user's goal below into 3–6 high-level steps:\n"
            f"GOAL: {goal}"
        )
        steps = [s.strip(" .") for s in resp.splitlines() if s.strip() and s[0].isdigit()]
        return steps or [goal]
    except Exception:
        return [goal]
