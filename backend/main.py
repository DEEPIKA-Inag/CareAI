from fastapi import FastAPI
from pydantic import BaseModel
import json
from pathlib import Path

app = FastAPI()

KB_PATH = Path(__file__).parent / "knowledge_base.json"
with open(KB_PATH, "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

DISCLAIMER = (
    "This is general self-care information, not a medical diagnosis. "
    "If symptoms are severe, worsening, or don't match what's described here, please see a doctor."
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "careAI backend is running"}

def find_match(message: str):
    message_lower = message.lower()
    best_entry, best_score = None, 0
    for entry in knowledge_base:
        score = sum(1 for tag in entry["symptom_tags"] if tag.lower() in message_lower)
        if score > best_score:
            best_entry, best_score = entry, score
    return best_entry, best_score

@app.post("/chat")
def chat(request: ChatRequest):
    entry, score = find_match(request.message)
    if entry is None or score == 0:
        return {
            "reply": "I don't have reliable guidance for that yet — please consult a doctor.",
            "disclaimer": DISCLAIMER,
        }
    return {
        "condition_matched": entry["condition"],
        "remedy": entry["remedy"],
        "diet": entry["diet"],
        "see_a_doctor_if": entry["see_a_doctor_if"],
        "source": entry["source"],
        "source_url": entry["source_url"],
        "disclaimer": DISCLAIMER,
    }