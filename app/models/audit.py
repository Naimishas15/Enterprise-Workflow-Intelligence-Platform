from pydantic import BaseModel
from datetime import datetime

class AuditEntry(BaseModel):
    tenant_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    cached: bool

class AuditResponse(BaseModel):
    id: str
    tenant_id: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    cached: bool
    created_at: datetime