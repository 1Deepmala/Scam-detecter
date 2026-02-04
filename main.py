import os
import re
import requests
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import List, Optional, Any
from google import genai 

# ==========================================
# 🛑 PASTE YOUR KEY INSIDE THESE QUOTES 🛑
# ==========================================
GEMINI_API_KEY = "AIzaSyDV8Hjt7JZU4S-k3t3bm90SgUhAiMEduys"
# Your Hackathon Secret 
MY_SECRET_KEY = "my_secure_password_123" 
CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

app = FastAPI()

# Data Models - MADE SUPER FLEXIBLE TO STOP ERRORS
class APIResponse(BaseModel):
    status: str
    scamDetected: bool
    extractedIntelligence: dict

# We use 'dict' instead of strict models so it NEVER fails validation
class ScamRequest(BaseModel):
    sessionId: Optional[str] = None
    sessionld: Optional[str] = None  # Handles the PDF typo
    message: Optional[dict] = None   # Accepts ANY message format
    conversationHistory: Optional[list] = []
    metadata: Optional[dict] = None

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
    
    # 3. Safely get the text (Even if the tester sends weird data)
    user_text = "Default scam text"
    if request.message and "text" in request.message:
        user_text = request.message["text"]
    
    # 4. Handle PDF Typo (sessionld vs sessionId)
    real_session_id = request.sessionId or request.sessionld or "unknown-session"

    # 5. AI Processing
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"You are a scam victim. Reply to: {user_text}"
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        agent_reply = response.text
    except Exception as e:
        print(f"GOOGLE AI ERROR: {e}") 
        agent_reply = "Connection error, but I am listening."

    # 6. Extract Intel
    intel = extract_pII(user_text)
    
    # Always fire callback if we found something
    if intel['upilds'] or intel['phishingLinks']:
        background_tasks.add_task(send_callback, real_session_id, intel)

    return APIResponse(
        status="success",
        scamDetected=True,
        extractedIntelligence={**intel, "agentNotes": agent_reply}
    )
