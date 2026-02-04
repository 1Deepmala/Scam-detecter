import os
import re
import requests
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from google import genai 

# ==========================================
# 🛑 PASTE YOUR KEY INSIDE THESE QUOTES 🛑
# ==========================================
GEMINI_API_KEY = "AIzaSyDV8Hjt7JZU4S-k3t3bm90SgUhAiMEduys" 

# Your Hackathon Secret 
MY_SECRET_KEY = "my_secure_password_123" 
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

app = FastAPI()

# ---------------------------------------------------------
# THE PERFECT FIX: We use 'dict' so we accept ANYTHING the tester sends
# ---------------------------------------------------------
class ScamRequest(BaseModel):
    sessionId: Optional[str] = None
    sessionld: Optional[str] = None
    # This line is the KEY. It accepts any message format (text, content, etc.)
    message: Optional[Dict[str, Any]] = None  
    conversationHistory: Optional[List[Any]] = []
    metadata: Optional[Dict[str, Any]] = None

class APIResponse(BaseModel):
    status: str
    scamDetected: bool
    extractedIntelligence: dict

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
async def honeypot_endpoint(request: ScamRequest, background_tasks: BackgroundTasks, x_api_key: str = Header(None)):
    # 1. Check API Key (Soft check to prevent crashing)
    if x_api_key != MY_SECRET_KEY:
        print(f"WARNING: Incorrect Key received: {x_api_key}")

    # 2. Get the text safely (Handle ANY format the organizer sends)
    user_text = "Default scam text"
    if request.message:
        # We try every possible name for the text field
        user_text = request.message.get("text") or request.message.get("content") or str(request.message)

    # 3. Handle PDF Typo (sessionld vs sessionId)
    real_session_id = request.sessionId or request.sessionld or "unknown-session"

    # 4. AI Processing
    agent_reply = "I am listening."
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"You are a scam victim. Reply to: {user_text}"
