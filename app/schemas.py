from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MessageRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    reply: str
    intent: str
    user_segment: str
    needs_human_support: bool

class UserOut(BaseModel):
    user_id: str
    name: str
    segment: str
    created_at: datetime
    last_seen_at: datetime
    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    user_id: str
    user_message: str
    assistant_reply: str
    intent: Optional[str]
    needs_human_support: bool
    created_at: datetime
    class Config:
        from_attributes = True