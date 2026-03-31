from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import uuid
from typing import List
from anthropic import AsyncAnthropic
from datetime import datetime

from .database import get_db
from .schemas import ChatRequest, ChatResponse, AssessmentRequest, AssessmentResponse, Expert
from .config import ANTHROPIC_API_KEY

app = FastAPI(title="JournoMind Connect API", version="1.0.0")

# CORS - Allow specific origins (update in production)
allowed_origins = [
    "http://localhost:5173",      # Vite dev server
    "http://localhost:3000",      # Alternative dev port
    "http://127.0.0.1:5173",
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
async def chat_endpoint(request: ChatRequest):
    try:
        if anthropic_client:
            # Real Anthropic call
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
            # Fallback when no API key
            ai_reply = "Thank you for sharing. I'm here with you. Would you like to tell me more about how you're feeling?"

        # Generate unique session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        return ChatResponse(reply=ai_reply, session_id=session_id)

    except Exception as e:
        print(f"Chat error: {e}")
        return ChatResponse(
            reply="I'm here with you. Sometimes the connection is slow — please try sending your message again.",
            session_id=request.session_id or str(uuid.uuid4())
        )

@app.post("/api/assessment", response_model=AssessmentResponse)
async def assessment_endpoint(request: AssessmentRequest):
    try:
        # Validate answers
        for answer in request.answers:
            if not (0 <= answer <= 4):
                raise HTTPException(status_code=400, detail="Answers must be between 0 and 4")
        
        # Calculate score with proper thresholds
        score = sum(request.answers)  # 0-20 range
        
        # Determine recommendation based on score
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
        
        return AssessmentResponse(
            message="Assessment completed successfully",
            recommendation=recommendation,
            should_connect_expert=should_connect,
            score=score
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Assessment error: {e}")
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)