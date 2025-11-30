from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Imports relative to the ai-microservice folder
from app.apis import chat
from app.libs.config import settings 

# 1. Initialize the FastAPI application
app = FastAPI(
    title="TradeLM AI Microservice",
    description="Dedicated service for LLM processing and auto-tagging, protected by a secret key.",
    version="1.0.0",
)


# 2. Configure CORS Middleware
origins = [
    settings.MAIN_BACKEND_URL, 
    "http://localhost:8000", 
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["X-Microservice-Auth"], 
)


# 3. Include API Router
# FIX: Change prefix="/" to prefix="" to resolve the Assertion Error.
app.include_router(chat.router, prefix="", tags=["AI Core"])


@app.get("/health")
def health_check():
    """Simple health check endpoint to verify the service is running."""
    return {"status": "ok", "service": "AI Microservice"}