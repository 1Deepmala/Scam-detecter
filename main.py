import os
import re
import requests
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from google import genai 

# ==========================================
# 🛑 PASTE YOUR KEY INSIDE THESE QUOTES 🛑
# ==========================================
GEMINI_API_KEY = "AIzaSyDV8Hjt7JZU4S-k3t3bm90SgUhAiMEduys" 

# Your Hackathon Secret 
MY_SECRET_KEY = "my_secure_password_123" 
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

app = FastAPI()

# Data Models
class Message(BaseModel):
    sender: str
    text: str
    # Make timestamp optional because sometimes testers skip it
    timestamp: Optional[str] = "2026-01-01T00:00:00Z" 

class Metadata(BaseModel):
    channel: str = "SMS"
    language: str = "English"
    locale: str = "IN"

class ScamRequest(BaseModel):
    # ---------------------------------------------------------
    # FIX: Accept both 'sessionId' AND 'sessionld' (PDF Typo)
    # ---------------------------------------------------------
    sessionId: Optional[str] = None
    sessionld: Optional[str] = None 
    
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata] = None

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = []
    upilds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    agentNotes: str = ""

class APIResponse(BaseModel):
    status: str
    scamDetected: bool
    extractedIntelligence: ExtractedIntelligence

def extract_pII(text: str):
    return {
        "upilds": re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+", text),
        "phoneNumbers": re.findall(r"(\+91[\-\s]?)?[6-9]\d{9}", text),
        "phishingLinks": re.findall(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+", text),
        "bankAccounts": re.findall(r"\b\d{9,18}\b", text)
    }

def send_callback(session_id: str, intelligence: dict):
    try:
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": 5,
            "extractedIntelligence": intelligence,
            "agentNotes": "Scam detected."
        }
        requests.post(CALLBACK_URL, json=payload, timeout=5)
        print(f"Callback sent for {session_id}")
    except Exception as e:
        print(f"Callback failed: {e}")

@app.post("/api/honey-pot", response_model=APIResponse)
async def honeypot_endpoint(request: ScamRequest, background_tasks: BackgroundTasks, x_api_key: str = Header(...)):
    # 1. Check API Key
    if x_api_key != MY_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid Hackathon API Key")

    # 2. Check Google Key
    if "PASTE_YOUR" in GEMINI_API_KEY:
        print("CRITICAL ERROR: You didn't paste the Google Key in main.py!")
        raise HTTPException(status_code=500, detail="Server Error: Missing Google Key")
    
    # 3. Handle PDF Typo (sessionld vs sessionId)
    real_session_id = request.sessionId or request.sessionld or "unknown-session"

    # 4. AI Processing
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"You are a scam victim. Reply to: {request.message.text}"
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        agent_reply = response.text
    except Exception as e:
        print(f"GOOGLE AI ERROR: {e}") 
        agent_reply = "Connection error, but I am listening."

    # 5. Extract Intel
    intel = extract_pII(request.message.text)
    
    if intel['upilds'] or intel['phishingLinks']:
        background_tasks.add_task(send_callback, real_session_id, intel)

    return APIResponse(
        status="success",
        scamDetected=True,
        extractedIntelligence=ExtractedIntelligence(**intel, agentNotes=agent_reply)
    )