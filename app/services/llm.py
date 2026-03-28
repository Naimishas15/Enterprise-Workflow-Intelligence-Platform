import litellm
from app.config import settings

litellm.openai_key = settings.OPENAI_API_KEY
litellm.anthropic_key = settings.ANTHROPIC_API_KEY

async def stream_completion(model: str, messages: list, temperature: float = 0.7):
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True
    )
    return response

async def simple_completion(model: str, messages: list) -> dict:
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        stream=False
    )
    return {
        "content": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "model": response.model
    }