from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import tokenization, calls

app = FastAPI(
    title="Automated Compliance Reviewer API",
    description="Backend API for auditing VoiceBot calls against compliance rules.",
    version="0.2.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tokenization.router)
app.include_router(calls.router)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Automated Compliance Reviewer API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
