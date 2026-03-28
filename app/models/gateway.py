from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = "gpt-4o-mini"
    messages: list[Message]
    stream: bool = True
    temperature: float = 0.7

class GatewayError(BaseModel):
    error: str
    code: str
    credits_remaining: int | None = None