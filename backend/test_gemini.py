from google import genai
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

class SymptomExtraction(BaseModel):
    symptom_tags: List[str] = Field(description="Short, plain-language symptom tags, e.g. 'runny nose', 'small cut', 'chest pain'.")
    duration: str = Field(description="How long symptoms have lasted, in the user's words, or 'unknown'.")
    severity: str = Field(description="mild, moderate, severe, or unknown.")
    red_flag_detected: bool = Field(description="True if the message mentions ANY of: chest pain, breathing difficulty, high fever in an infant under 3 months, severe bleeding, signs of stroke, suicidal thoughts, severe allergic reaction, pregnancy-related symptoms, fever over 3 days.")
    red_flag_reason: str = Field(description="Which red flag matched and why, if any. Empty string otherwise.")

client = genai.Client()

message = "I cut my finger and it's bleeding a little"

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=f"Extract structured symptom information from this message. Do not diagnose or add advice, only extract what is stated: {message}",
    config={
        "response_mime_type": "application/json",
        "response_schema": SymptomExtraction,
    }
)

result = SymptomExtraction.model_validate_json(response.text)
print(result)