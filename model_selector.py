"""
Model Selector
==============
Chooses the cheapest model that satisfies a requested metric.

• Pricing table lives in MODELS.
• choose_model(metric)  -> returns the model_id string
• update_price(model_id, price)  -> runtime update (auto-persists JSON)
"""

from __future__ import annotations

import json
import pathlib

DATA_PATH = pathlib.Path("model_prices.json")

# fall-back pricing table (USD per 1K tokens)
DEFAULT_PRICES = {
    "gpt-4o": 0.005,
    "gpt-3.5-turbo": 0.001,
    "claude-3-haiku": 0.0008,
    "claude-3-sonnet": 0.003,
}


def _load_prices() -> dict[str, float]:
    if DATA_PATH.exists():
        try:
            return json.loads(DATA_PATH.read_text())
        except Exception:
            pass
    return DEFAULT_PRICES.copy()


def _save_prices(prices: dict[str, float]) -> None:
    DATA_PATH.write_text(json.dumps(prices, indent=2))


PRICES: dict[str, float] = _load_prices()


# ──────────────────────────────────────────────────────────────
def choose_model(metric: str = "cheap") -> str:
    """
    metric:
        "cheap"   – lowest cost
        "premium" – top-tier (gpt-4o)
        "speed"   – mid-range but faster (gpt-3.5 / haiku)
    """
    if metric == "premium":
        return "gpt-4o"
    if metric == "speed":
        return min(
            PRICES,
            key=lambda m: (PRICES[m], m not in ("gpt-3.5-turbo", "claude-3-haiku")),
        )
    # default: cheapest
    return min(PRICES, key=PRICES.get)


def update_price(model_id: str, price_per_1k: float) -> None:
    PRICES[model_id] = price_per_1k
    _save_prices(PRICES)


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Cheapest model →", choose_model())
