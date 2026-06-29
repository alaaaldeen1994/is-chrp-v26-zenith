from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class APIKeyCreate(BaseModel):
    owner: str = Field(..., example="University Research Lab", description="Name of the client organization")
    tier: str = Field("free", example="professional", description="Access tier: free, professional, enterprise")
    expires_in_days: Optional[int] = Field(None, description="Expiry time in days from now")

class APIKeyResponse(BaseModel):
    id: int
    prefix: str
    owner: str
    tier: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
