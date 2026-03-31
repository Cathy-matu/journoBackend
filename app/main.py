from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import uuid
from typing import List
from anthropic import AsyncAnthropic
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .schemas import ChatRequest, ChatResponse, AssessmentRequest, AssessmentResponse, Expert
from .config import ANTHROPIC_API_KEY
from . import models

app = FastAPI(title="JournoMind Connect API", version="1.0.0")

# CORS - Allow specific origins (update in production)
allowed_origins = [
    "http://localhost:5173",      # Vite dev server
    "http://localhost:3000",      # Alternative dev port
    "http://127.0.0.1:5173",
    "https://juornomind.vercel.app",
    "https://journo-backend.vercel.app",
    os.getenv("FRONTEND_URL", "http://localhost:5173")  # Configurable via env
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Anthropic client
anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# Static experts (same as frontend)
EXPERTS = [
    {"id": 1, "name": "Dr. Nadia Kamau", "initials": "NK", "color": "teal", "specialty": "Trauma & PTSD Specialist · Nairobi", "status": "Available", "rating": "4.9", "sessions": "128"},
    {"id": 2, "name": "Okello Mugisha", "initials": "OM", "color": "amber", "specialty": "Conflict Trauma Counselor · Kampala", "status": "In 1hr", "rating": "4.8", "sessions": "94"},
    {"id": 3, "name": "Amina Mwangi", "initials": "AM", "color": "coral", "specialty": "Grief & Resilience · Dar es Salaam", "status": "Tomorrow", "rating": "4.7", "sessions": "67"},
    {"id": 4, "name": "Dr. Jean-Pierre Habimana", "initials": "JH", "color": "green", "specialty": "Genocide trauma · Kigali", "status": "Available", "rating": "5.0", "sessions": "210"},
]

@app.get("/")
async def root():
    return {"message": "JournoMind Connect API is running"}

@app.get("/api/experts", response_model=List[Expert])
async def get_experts():
    return EXPERTS

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        # 1. Get or create user
        anonymous_id = request.anonymous_id or "legacy_user"
        result = await db.execute(select(models.User).where(models.User.anonymous_id == anonymous_id))
        user = result.scalars().first()
        
        if not user:
            user = models.User(anonymous_id=anonymous_id)
            db.add(user)
            await db.flush()

        # 2. Get or create session
        session_id_str = request.session_id or str(uuid.uuid4())
        # For simplicity in this MVP, we'll use the session_id_str to find/create a session
        # In a real app, you'd probably use a database ID, but we'll use expert_name + user_id mapping for now
        # or just create a new session if none provided
        
        # 3. AI Reply logic
        if anthropic_client:
            system_prompt = f"""You are {request.expert}, a compassionate, trauma-informed psychosocial support counselor 
            working with journalists in East Africa. Be warm, empathetic, culturally sensitive, and concise (2-4 sentences). 
            Never diagnose. If in crisis, recommend Africa Mental Health Foundation: +254 20 272 4724."""

            response = await anthropic_client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=800,
                system=system_prompt,
                messages=[{"role": "user", "content": request.message}]
            )
            ai_reply = response.content[0].text
        else:
            ai_reply = "Thank you for sharing. I'm here with you. Would you like to tell me more about how you're feeling?"

        # 4. Persist messages
        # We need a ChatSession object. Let's create one if it doesn't exist for this session_id string
        # Actually, let's just create a new entry for every "session" initiated
        # To keep it simple, we'll try to find an existing session by user and expert
        res_session = await db.execute(
            select(models.ChatSession)
            .where(models.ChatSession.user_id == user.id, models.ChatSession.expert_name == request.expert)
            .order_by(models.ChatSession.started_at.desc())
        )
        chat_session = res_session.scalars().first()
        
        if not chat_session:
            chat_session = models.ChatSession(user_id=user.id, expert_name=request.expert)
            db.add(chat_session)
            await db.flush()

        # Save user message
        user_msg = models.Message(session_id=chat_session.id, content=request.message, is_user=True)
        # Save AI message
        ai_msg = models.Message(session_id=chat_session.id, content=ai_reply, is_user=False)
        
        db.add(user_msg)
        db.add(ai_msg)
        await db.commit()

        return ChatResponse(reply=ai_reply, session_id=session_id_str)

    except Exception as e:
        print(f"Chat error: {e}")
        await db.rollback()
        return ChatResponse(
            reply="I'm here with you. Sometimes the connection is slow — please try sending your message again.",
            session_id=request.session_id or str(uuid.uuid4())
        )

@app.post("/api/assessment", response_model=AssessmentResponse)
async def assessment_endpoint(request: AssessmentRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Validate answers
        for answer in request.answers:
            if not (0 <= answer <= 4):
                raise HTTPException(status_code=400, detail="Answers must be between 0 and 4")
        
        # Calculate score
        score = sum(request.answers)
        
        # Recommendations
        if score >= 16:
            recommendation = "You've reported severe symptoms. Connecting with a trauma specialist is important."
            should_connect = True
        elif score >= 11:
            recommendation = "Your responses suggest moderate stress. A conversation with a specialist could help."
            should_connect = True
        elif score >= 6:
            recommendation = "You're showing some signs of stress. Consider our resources or optional expert support."
            should_connect = False
        else:
            recommendation = "Your wellbeing looks strong. Keep using these tools for ongoing support."
            should_connect = False
        
        # Persist to database
        anonymous_id = request.anonymous_id or "legacy_user"
        result = await db.execute(select(models.User).where(models.User.anonymous_id == anonymous_id))
        user = result.scalars().first()
        
        if not user:
            user = models.User(anonymous_id=anonymous_id)
            db.add(user)
            await db.flush()
            
        assessment = models.Assessment(
            user_id=user.id,
            answers=json.dumps(request.answers),
            score=score
        )
        db.add(assessment)
        await db.commit()
        
        return AssessmentResponse(
            message="Assessment completed successfully",
            recommendation=recommendation,
            should_connect_expert=should_connect,
            score=score
        )
    except Exception as e:
        print(f"Assessment error: {e}")
        await db.rollback()
        # Return the actual error message in the message field for easier debugging
        return AssessmentResponse(
            message=f"Backend Error: {str(e)}",
            recommendation="We encountered a problem saving your results. Please check the backend logs.",
            should_connect_expert=False,
            score=None
        )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)