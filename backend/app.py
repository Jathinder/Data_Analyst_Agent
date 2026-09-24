from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
from pathlib import Path


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(BASE_DIR)
)


# =========================================================
# IMPORT AGENT
# =========================================================

from agent_core import run_agent


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="AI Data Analyst API",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class AnalyzeRequest(BaseModel):
    question: str


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "AI Data Analyst API",
        "version": "1.0.0"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "SQLite · Chinook",
        "ai_engine": "Ollama · Llama 3.1"
    }


# =========================================================
# ANALYZE
# =========================================================

@app.post("/analyze")
def analyze(request: AnalyzeRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:

        result = run_agent(question)

        return {
            "answer": result.get("answer", ""),
            "sql": result.get("sql", ""),
            "columns": result.get("columns", []),
            "rows": result.get("rows", []),
            "steps": result.get("steps", 0),
            "error": result.get("error")
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )