from pydantic import BaseModel
from datetime import datetime

class TenantCreate(BaseModel):
    name: str
    plan: str = "starter"
    credits: int = 1000

class TenantResponse(BaseModel):
    id: str
    name: str
    plan: str
    credits_remaining: int
    is_active: bool
    created_at: datetime

class CreditsAdd(BaseModel):
    amount: int