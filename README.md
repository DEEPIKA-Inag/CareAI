# careAI

A home-remedy and diet assistant that takes a text description of symptoms and/or a photo, and responds with general self-care guidance — grounded in a curated, sourced knowledge base rather than an LLM's free recall, with a hard safety gate in front of everything.

**This is a personal/learning project and is not a medical device. It does not diagnose conditions and is not a substitute for professional medical advice.**

## How it works

1. **Red-flag check (deterministic + AI):** every message is checked against a fixed list of emergency symptoms (chest pain, breathing difficulty, signs of stroke, suicidal ideation, and more) before anything else runs. A plain keyword check catches obvious cases instantly and for free; a Gemini-based extraction step catches paraphrased ones the keyword list can't anticipate. If either triggers, the app immediately shows an emergency message instead of any home-remedy content.
2. **Symptom/image understanding:** Google's Gemini API extracts structured symptom tags from the user's text, and separately describes (never diagnoses) what's visible in an uploaded photo.
3. **Grounded matching:** those tags are matched against a curated knowledge base of home remedies and diet guidance, each entry sourced from a credible reference (Mayo Clinic, Cleveland Clinic) with a citation link — the model rephrases this content, it doesn't invent medical advice from its own training.
4. **Honest fallback:** if nothing matches confidently, the app says so and recommends seeing a doctor, rather than guessing.
5. **Consent gate:** first-time users must acknowledge a disclaimer describing exactly what the tool is (and isn't) and how their data is used, before the chat becomes usable.

## Tech stack

- **Backend:** Python, FastAPI
- **AI:** Google Gemini API (`google-genai` SDK) — structured text extraction and image understanding
- **Frontend:** plain HTML/CSS/JavaScript, served directly by FastAPI (no separate frontend server)
- **Data:** a hand-curated `knowledge_base.json`, sourced from public health references

## Project structure

careAI/
├── docs/
│ ├── scope.md # in-scope conditions + universal red-flag list
│ └── privacy_notes.md # data-handling notes
├── backend/
│ ├── main.py # FastAPI app: red-flag checks, Gemini extraction, matching, endpoints
│ ├── knowledge_base.json # sourced remedy/diet entries
│ └── requirements.txt
└── frontend/
├── index.html
├── style.css
└── script.js


## Running it locally

1. Clone the repo and set up the backend environment:

cd backend
python -m venv venv
venv\Scripts\Activate.ps1 # Windows
pip install -r requirements.txt

2. Create a `.env` file inside `backend/` with your own Gemini API key:

GOOGLE_API_KEY=your_key_here

   (Get one from [Google AI Studio](https://aistudio.google.com/apikey).)
3. Run the server:

python -m uvicorn main:app --reload

4. Open `http://127.0.0.1:8000/` in your browser.

## Current scope

Currently covers seven minor, non-emergency conditions: common cold, mild tension headache, minor cuts/scrapes, mild indigestion, minor insect bites/skin irritation, mild seasonal allergies, and muscle soreness. Anything outside that list — or anything matching a red flag — is deliberately not given a home remedy.

## Status / roadmap

- [x] Red-flag detection (keyword + AI layers)
- [x] Text and image symptom understanding
- [x] Sourced knowledge base
- [x] Web UI with consent gate
- [ ] Wider deployment with API billing enabled
- [ ] Expanded knowledge base
- [ ] Reviewed privacy policy (current notes are dev working notes, not legal copy)

## Disclaimer

This tool provides general self-care information only. It is not a medical diagnosis and is not a substitute for professional medical advice. If you are experiencing a medical emergency, contact emergency services or go to the nearest hospital.