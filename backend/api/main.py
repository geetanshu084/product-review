"""
FastAPI main application
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Disable Google Cloud ADC check - use API key instead
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''  # Disable ADC

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.core.config import settings
from api.routes import products, chat
import sys

# Validate LLM configuration at startup (CRITICAL - fail fast)
if not settings.has_llm_configured():
    print("=" * 80)
    print("❌ ERROR: No LLM provider configured!")
    print("=" * 80)
    print("\nLLM is required for core functionality. Please configure one of:")
    print("  - Google Gemini: Set GOOGLE_API_KEY and LLM_PROVIDER=google")
    print("  - OpenAI: Set OPENAI_API_KEY and LLM_PROVIDER=openai")
    print("  - Anthropic: Set ANTHROPIC_API_KEY and LLM_PROVIDER=anthropic")
    print("  - Groq: Set GROQ_API_KEY and LLM_PROVIDER=groq")
    print("  - Cohere: Set COHERE_API_KEY and LLM_PROVIDER=cohere")
    print("  - Ollama: Set LLM_PROVIDER=ollama (runs locally)")
    print("\nSee backend/docs/LLM_PROVIDERS.md for setup instructions.")
    print("=" * 80)
    sys.exit(1)

print(f"✓ LLM Provider: {settings.LLM_PROVIDER}")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


# Include routers
app.include_router(
    products.router,
    prefix=f"{settings.API_V1_STR}/products",
    tags=["products"]
)

app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["chat"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
