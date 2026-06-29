from pydantic import BaseModel
from typing import Any, Optional, Dict

class APIEnvelope(BaseModel):
    status: str = "success"
    data: Any
    meta: Dict[str, Any] = {
        "model_version": "zenith-v30.0",
        "credits_used": 1
    }

class AsyncJobResponse(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    status_url: str
    eta_seconds: Optional[float] = None
