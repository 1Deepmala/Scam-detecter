import requests
import json

# 1. The Setup
url = "https://scam-detecter-wtut.onrender.com/api/honey-pot" 
api_key = "my_secure_password_123"

# 2. The Data (No external file needed!)
payload = {
    "sessionId": "test-session-01",
    "message": {
        "sender": "scammer",
        "text": "Your account is blocked. Send money to upi@scammer immediately.",
        "timestamp": "2026-02-03T10:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {
        "language": "English", 
        "locale": "IN"
    }
}

headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key
}

# 3. The Request
print(f"Sending request to {url}...")
try:
    response = requests.post(url, json=payload, headers=headers)
    
    # 4. The Result
    print("\nSTATUS CODE:", response.status_code)
    print("\nRESPONSE FROM SERVER:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print("\n❌ CONNECTION ERROR:", e)
    print("Make sure 'uvicorn main:app --reload' is running in another window!")