from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
client = genai.Client()

KB_PATH = Path(__file__).parent / "knowledge_base.json"
with open(KB_PATH, "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

DISCLAIMER = (
    "This is general self-care information, not a medical diagnosis. "
    "If symptoms are severe, worsening, or don't match what's described here, please see a doctor."
)

RED_FLAG_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing", "shortness of breath",
    "severe bleeding", "won't stop bleeding", "stroke", "face drooping", "slurred speech",
    "suicide", "suicidal", "kill myself", "want to die",
    "anaphylaxis", "throat swelling", "swelling of face",
    "pregnant", "pregnancy",
    "unconscious", "passed out", "confusion",
]

class ChatRequest(BaseModel):
    message: str

class SymptomExtraction(BaseModel):
    symptom_tags: List[str] = Field(description="Short, plain-language symptom tags, e.g. 'runny nose', 'small cut', 'chest pain'.")
    duration: str = Field(description="How long symptoms have lasted, in the user's words, or 'unknown'.")
    severity: str = Field(description="mild, moderate, severe, or unknown.")
    red_flag_detected: bool = Field(description="True if the message mentions ANY of: chest pain, breathing difficulty, high fever in an infant under 3 months, severe bleeding, signs of stroke, suicidal thoughts, severe allergic reaction, pregnancy-related symptoms, fever over 3 days.")
    red_flag_reason: str = Field(description="Which red flag matched and why, if any. Empty string otherwise.")

class ImageFindings(BaseModel):
    visual_description: str = Field(description="A plain, factual description of what is visible in the image (e.g. 'a red raised patch of skin, about 2cm, on the forearm'). Do not diagnose or name a condition.")
    symptom_tags: List[str] = Field(description="Short plain-language tags describing the visual findings, the way a person would describe them, e.g. 'skin rash', 'redness', 'swelling'.")
    red_flag_detected: bool = Field(description="True if the image shows something urgent: severe bleeding, a deep wound, signs of serious infection (spreading redness, pus, blackened tissue), or anything requiring immediate medical attention.")
    red_flag_reason: str = Field(description="Which visual red flag was matched, if any. Empty string otherwise.")

@app.get("/")
def root():
    return {"status": "careAI backend is running"}

def rule_based_red_flag_check(message: str):
    message_lower = message.lower()
    for kw in RED_FLAG_KEYWORDS:
        if kw in message_lower:
            return kw
    return None

def extract_symptoms(message: str) -> SymptomExtraction:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Extract structured symptom information from this message. Do not diagnose or add advice, only extract what is stated: {message}",
        config={
            "response_mime_type": "application/json",
            "response_schema": SymptomExtraction,
        }
    )
    return SymptomExtraction.model_validate_json(response.text)

def extract_image_findings(image_bytes: bytes, mime_type: str) -> ImageFindings:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            "Describe only what is visibly present in this image relevant to a minor health concern (skin, wound, rash, swelling, etc.). Do not diagnose or name a specific condition — describe observations only.",
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": ImageFindings,
        }
    )
    return ImageFindings.model_validate_json(response.text)

def match_knowledge_base(extracted_tags: list):
    best_entry, best_score = None, 0
    for entry in knowledge_base:
        score = 0
        for etag in extracted_tags:
            etag_l = etag.lower()
            for ktag in entry["symptom_tags"]:
                ktag_l = ktag.lower()
                if ktag_l in etag_l or etag_l in ktag_l:
                    score += 1
                    break
        if score > best_score:
            best_entry, best_score = entry, score
    return best_entry, best_score

@app.post("/chat")
def chat(request: ChatRequest):
    rule_flag = rule_based_red_flag_check(request.message)
    if rule_flag:
        return {
            "emergency": True,
            "message": "This may need urgent medical attention — please seek emergency care or see a doctor right away.",
            "reason": f"Matched red-flag keyword: '{rule_flag}'",
            "disclaimer": DISCLAIMER,
        }

    extraction = extract_symptoms(request.message)

    if extraction.red_flag_detected:
        return {
            "emergency": True,
            "message": "This may need urgent medical attention — please seek emergency care or see a doctor right away.",
            "reason": extraction.red_flag_reason,
            "disclaimer": DISCLAIMER,
        }

    entry, score = match_knowledge_base(extraction.symptom_tags)
    if entry is None or score == 0:
        return {
            "reply": "I don't have reliable guidance for that yet — please consult a doctor.",
            "extracted": extraction.model_dump(),
            "disclaimer": DISCLAIMER,
        }

    return {
        "condition_matched": entry["condition"],
        "remedy": entry["remedy"],
        "diet": entry["diet"],
        "see_a_doctor_if": entry["see_a_doctor_if"],
        "source": entry["source"],
        "source_url": entry["source_url"],
        "extracted": extraction.model_dump(),
        "disclaimer": DISCLAIMER,
    }

@app.post("/chat-with-image")
async def chat_with_image(message: Optional[str] = Form(None), image: UploadFile = File(...)):
    if message:
        rule_flag = rule_based_red_flag_check(message)
        if rule_flag:
            return {
                "emergency": True,
                "message": "This may need urgent medical attention — please seek emergency care or see a doctor right away.",
                "reason": f"Matched red-flag keyword: '{rule_flag}'",
                "disclaimer": DISCLAIMER,
            }

    image_bytes = await image.read()
    mime_type = image.content_type or "image/jpeg"
    findings = extract_image_findings(image_bytes, mime_type)

    all_tags = list(findings.symptom_tags)
    red_flag = findings.red_flag_detected
    red_flag_reason = findings.red_flag_reason

    if message:
        text_extraction = extract_symptoms(message)
        all_tags += text_extraction.symptom_tags
        if text_extraction.red_flag_detected:
            red_flag = True
            red_flag_reason = red_flag_reason or text_extraction.red_flag_reason

    if red_flag:
        return {
            "emergency": True,
            "message": "This may need urgent medical attention — please seek emergency care or see a doctor right away.",
            "reason": red_flag_reason,
            "disclaimer": DISCLAIMER,
        }

    entry, score = match_knowledge_base(all_tags)
    if entry is None or score == 0:
        return {
            "reply": "I don't have reliable guidance for that yet — please consult a doctor.",
            "visual_description": findings.visual_description,
            "extracted_tags": all_tags,
            "disclaimer": DISCLAIMER,
        }

    return {
        "condition_matched": entry["condition"],
        "remedy": entry["remedy"],
        "diet": entry["diet"],
        "see_a_doctor_if": entry["see_a_doctor_if"],
        "source": entry["source"],
        "source_url": entry["source_url"],
        "visual_description": findings.visual_description,
        "extracted_tags": all_tags,
        "disclaimer": DISCLAIMER,
    }