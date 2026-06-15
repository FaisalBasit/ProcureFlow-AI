"""
ProcureFlow AI — FastAPI Application Entry Point
Multi-agent procurement orchestration backend.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.routes.procurement import router as procurement_router
from backend.routes.webhook import router as webhook_router

load_dotenv()

app = FastAPI(
    title="ProcureFlow AI",
    description="Intelligent Procurement Orchestrator — Multi-agent Band-powered API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "https://procureflow-ai.vercel.app",  # Prod frontend
        "*",  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(procurement_router)
app.include_router(webhook_router)


@app.get("/")
async def root():
    """Root health check."""
    return {
        "service": "ProcureFlow AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )