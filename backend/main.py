from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "careAI backend is running"}

@app.post("/chat")
def chat(request: ChatRequest):
    return {"reply": f"You said: {request.message}"}