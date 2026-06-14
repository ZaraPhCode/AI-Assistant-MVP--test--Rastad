import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, Message
from app.schemas import MessageRequest, MessageResponse
from app.services.classifier import classify_message
from app.services.knowledge_service import knowledge_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/message", response_model=MessageResponse)
def handle_message(request: MessageRequest, db: Session = Depends(get_db)):
    intent, segment, needs_human = classify_message(request.message)
    knowledge = knowledge_service.search(request.message)
    reply = llm_service.generate_reply(intent, knowledge, request.message)

    user = db.query(User).filter(User.user_id == request.user_id).first()
    if not user:
        user = User(
            user_id=request.user_id,
            name=request.name,
            segment=segment,
            created_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db.add(user)
    else:
        user.name = request.name
        user.segment = segment
        user.last_seen_at = datetime.now(timezone.utc)

    msg_record = Message(
        user_id=request.user_id,
        user_message=request.message,
        assistant_reply=reply,
        intent=intent,
        needs_human_support=needs_human,
        created_at=datetime.now(timezone.utc),
    )
    db.add(msg_record)
    db.commit()

    logger.info(
        f"user_id={request.user_id}, intent={intent}, segment={segment}, "
        f"needs_human={needs_human}, msg_len={len(request.message)}"
    )
    return MessageResponse(
        reply=reply,
        intent=intent,
        user_segment=segment,
        needs_human_support=needs_human,
    )

# HTML form handler
@router.post("/message-form")
async def handle_message_form(
    request: Request,
    user_id: str = Form(...),
    name: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    intent, segment, needs_human = classify_message(message)
    knowledge = knowledge_service.search(message)
    reply = llm_service.generate_reply(intent, knowledge, message)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(
            user_id=user_id,
            name=name,
            segment=segment,
            created_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db.add(user)
    else:
        user.name = name
        user.segment = segment
        user.last_seen_at = datetime.now(timezone.utc)

    msg_record = Message(
        user_id=user_id,
        user_message=message,
        assistant_reply=reply,
        intent=intent,
        needs_human_support=needs_human,
        created_at=datetime.now(timezone.utc),
    )
    db.add(msg_record)
    db.commit()

    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": {
            "reply": reply,
            "intent": intent,
            "user_segment": segment,
            "needs_human_support": needs_human,
            "user_id": user_id,
            "name": name,
            "message": message
        }
    })