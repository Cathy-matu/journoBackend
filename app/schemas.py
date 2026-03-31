from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    expert: str
    session_id: Optional[str] = None
    anonymous_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

class AssessmentRequest(BaseModel):
    answers: List[int]
    anonymous_id: Optional[str] = None

class AssessmentResponse(BaseModel):
    message: str
    recommendation: str
    should_connect_expert: bool = True
    score: Optional[int] = None

class Expert(BaseModel):
    id: int
    name: str
    initials: str
    color: str
    specialty: str
    status: str
    rating: str
    sessions: str