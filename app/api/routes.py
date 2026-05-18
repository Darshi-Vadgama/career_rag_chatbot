# app/api/routes.py

from fastapi import APIRouter, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.services.rag_pipeline import run_rag
from app.services.resume_service import scan_resume
from app.services.roadmap_service import generate_roadmap
from app.services.auth_service import (
    register_user,
    login_user,
    refresh_tokens,
    logout_user,
    decode_access_token,
    create_chat,
    get_user_chats,
    get_chat_messages,
    save_message,
    update_chat_title,
    delete_chat,
)

router   = APIRouter()
security = HTTPBearer()


# ── Auth schemas ──────────────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    user_id:       str
    refresh_token: str


class LogoutRequest(BaseModel):
    user_id:       str
    refresh_token: str


class NewChatRequest(BaseModel):
    user_id: str


class SaveMessageRequest(BaseModel):
    chat_id: str
    role:    str
    content: str


class UpdateTitleRequest(BaseModel):
    chat_id: str
    title:   str


# ── Auth dependency ───────────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    return decode_access_token(credentials.credentials)


# ── Auth routes ───────────────────────────────────────────────────────────────

@router.post("/auth/register")
def register(body: AuthRequest):
    return register_user(body.username, body.password)


@router.post("/auth/login")
def login(body: AuthRequest):
    return login_user(body.username, body.password)


@router.post("/auth/refresh")
def refresh(body: RefreshRequest):
    return refresh_tokens(body.user_id, body.refresh_token)


@router.post("/auth/logout")
def logout(body: LogoutRequest):
    logout_user(body.user_id, body.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["sub"]}


# ── Chat session routes ───────────────────────────────────────────────────────

@router.post("/chats/new")
def new_chat(
    body: NewChatRequest,
    current_user: dict = Depends(get_current_user)
):
    return create_chat(body.user_id)


@router.get("/chats/{user_id}")
def list_chats(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    return get_user_chats(user_id)


@router.get("/chats/{chat_id}/messages")
def chat_messages(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    return get_chat_messages(chat_id)


@router.post("/chats/message")
def add_message(
    body: SaveMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    save_message(body.chat_id, body.role, body.content)
    return {"ok": True}


@router.post("/chats/title")
def set_title(
    body: UpdateTitleRequest,
    current_user: dict = Depends(get_current_user)
):
    update_chat_title(body.chat_id, body.title)
    return {"ok": True}


@router.delete("/chats/{chat_id}")
def remove_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user)
):
    delete_chat(chat_id)
    return {"ok": True}


# ── Career routes (session_id aware) ─────────────────────────────────────────

@router.post("/career-search")
async def career_search(
    question:   str = Form(None),
    file:       UploadFile = File(None),
    session_id: str = Form("default"),
    current_user: dict = Depends(get_current_user),
):
    if file:
        stream = await scan_resume(file)
        return StreamingResponse(stream, media_type="text/plain")

    if question and "roadmap" in question.lower():
        career = question.replace("roadmap", "").strip()
        stream = await generate_roadmap(career)
        return StreamingResponse(stream, media_type="text/plain")

    stream = await run_rag(question, session_id=session_id)
    return StreamingResponse(stream, media_type="text/plain")


@router.post("/resume-scan")
async def resume_scan(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    stream = await scan_resume(file)
    return StreamingResponse(stream, media_type="text/plain")


@router.post("/roadmap")
async def roadmap(
    
    career: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    stream = await generate_roadmap(career)
    return StreamingResponse(stream, media_type="text/plain")