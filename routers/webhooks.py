import hmac
import hashlib
import json
import secrets
import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session
from database.connection import get_db, SessionLocal
from database.models import WebhookSubscription, APIKey
from schemas.responses import APIEnvelope

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])

class WebhookSubscribeRequest(BaseModel):
    url: str = Field(..., example="https://myapi.com/callbacks/zenith", description="HTTPS callback URL to send webhook events to")

class WebhookSubscriptionResponse(BaseModel):
    subscription_id: int
    url: str
    signing_secret: str
    status: str
    created_at: datetime

@router.post("/subscribe", response_model=APIEnvelope)
def post_subscribe(
    payload: WebhookSubscribeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    api_key_id = getattr(request.state, "api_key_id", None)
    if not api_key_id:
        api_key = getattr(request.state, "api_key", None)
        if not api_key:
            raise HTTPException(status_code=401, detail="Valid API key required to subscribe to webhooks")
        try:
            api_key_id = api_key.id
        except Exception:
            raise HTTPException(status_code=401, detail="Valid API key required to subscribe to webhooks")

    # Limit total subscriptions per key for abuse prevention (e.g. max 5)
    existing_count = db.query(WebhookSubscription).filter(WebhookSubscription.api_key_id == api_key_id, WebhookSubscription.is_active == True).count()
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum of 5 active webhook subscriptions reached for this API key")

    # Generate a cryptographically secure signing secret for verification
    secret = f"whsec_{secrets.token_hex(24)}"
    
    sub = WebhookSubscription(
        api_key_id=api_key_id,
        url=str(payload.url),
        secret=secret,
        is_active=True
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    data = WebhookSubscriptionResponse(
        subscription_id=sub.id,
        url=sub.url,
        signing_secret=sub.secret,
        status="active",
        created_at=sub.created_at
    )
    return APIEnvelope(data=data, meta={"compute_time_ms": 0, "credits_used": 0})

def dispatch_webhook_sync(api_key_id: int, event_type: str, data: dict):
    """
    Looks up active subscriptions, signs the payload, and dispatches POST requests to clients.
    Designed for async execution inside a background thread pool.
    """
    db = SessionLocal()
    try:
        subs = db.query(WebhookSubscription).filter(
            WebhookSubscription.api_key_id == api_key_id,
            WebhookSubscription.is_active == True
        ).all()
        
        if not subs:
            return
            
        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        
        with httpx.Client(timeout=8.0) as client:
            for sub in subs:
                # Generate signature: HMAC SHA256 of the exact payload body
                signature = hmac.new(
                    sub.secret.encode(),
                    payload_bytes,
                    hashlib.sha256
                ).hexdigest()
                
                try:
                    # Send payload with signature headers for client-side auth validation
                    client.post(
                        sub.url,
                        content=payload_bytes,
                        headers={
                            "Content-Type": "application/json",
                            "X-Zenith-Signature": signature,
                            "X-Zenith-Subscription-ID": str(sub.id)
                        }
                    )
                    print(f"[WebhookDispatcher] Successfully dispatched event '{event_type}' to {sub.url}")
                except Exception as e:
                    print(f"[WebhookDispatcher] Delivery failed to {sub.url}: {e}")
                    
    finally:
        db.close()
