"""PLACEHOLDER prices (dollars per million tokens). Replace with the real price list before you believe any money number.
Multipliers are from the caching docs: 5-minute write 1.25x, 1-hour write 2x, read 0.1x (some newer models list lower read multipliers)."""
PRICES = {"fake-sonnet": {"input": 3.00, "output": 15.00}}
WRITE_5M, WRITE_1H, READ = 1.25, 2.0, 0.10


def cost(usage: dict, model: str = "fake-sonnet", read_mult: float = READ) -> float:
    p = PRICES[model]
    cc = usage.get("cache_creation", {})
    w5 = cc.get("ephemeral_5m_input_tokens", usage.get("cache_creation_input_tokens", 0) if not cc else 0)
    w1 = cc.get("ephemeral_1h_input_tokens", 0)
    base = usage.get("input_tokens", 0) + w5 * WRITE_5M + w1 * WRITE_1H + usage.get("cache_read_input_tokens", 0) * read_mult
    return (base * p["input"] + usage.get("output_tokens", 0) * p["output"]) / 1e6


def hit_rate(usage: dict) -> float:
    total = usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
    return usage.get("cache_read_input_tokens", 0) / total if total else 0.0
