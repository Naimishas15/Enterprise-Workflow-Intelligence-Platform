PRICING = {
    "gpt-4o": {
        "input": 0.005,
        "output": 0.015,
    },
    "gpt-4o-mini": {
        "input": 0.00015,
        "output": 0.0006,
    },
    "claude-3-5-sonnet-20241022": {
        "input": 0.003,
        "output": 0.015,
    },
    "claude-3-haiku-20240307": {
        "input": 0.00025,
        "output": 0.00125,
    },
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model, PRICING["gpt-4o-mini"])
    input_cost  = (input_tokens  / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    return round(input_cost + output_cost, 6)

def get_supported_models() -> list:
    return list(PRICING.keys())