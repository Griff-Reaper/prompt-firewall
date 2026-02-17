"""
Prompt Firewall - FastAPI Gateway

Production-ready REST API for prompt security
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from firewall import create_firewall, Action

# Create FastAPI app
app = FastAPI(
    title="Prompt Firewall API",
    description="Enterprise LLM Security Gateway",
    version="1.0.0"
)

# Mount dashboard static files
dashboard_path = Path(__file__).parent.parent / "dashboard"
if dashboard_path.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_path)), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize firewall
firewall = create_firewall(
    use_prompt_shield=False,  # Set to True when Prompt-Shield available
    log_dir="../logs",
    enable_logging=True
)

print("[✓] Firewall API initialized")


# Request/Response Models
class CheckRequest(BaseModel):
    """Request to check a prompt"""
    prompt: str = Field(..., description="Prompt to analyze")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What is the capital of France?",
                "user_id": "user123",
                "session_id": "session456"
            }
        }


class CheckResponse(BaseModel):
    """Response from firewall check"""
    action: str
    allowed: bool
    threat_score: float
    threat_level: str
    message: str
    sanitized_prompt: Optional[str] = None
    processing_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "allow",
                "allowed": True,
                "threat_score": 15.0,
                "threat_level": "safe",
                "message": "Request allowed",
                "sanitized_prompt": None,
                "processing_time_ms": 3.42
            }
        }


class StatsResponse(BaseModel):
    """Firewall statistics"""
    total_requests: int
    blocked: int
    sanitized: int
    allowed: int
    threats_detected: int
    block_rate: float
    sanitize_rate: float
    threat_rate: float


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to dashboard"""
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/dashboard" />
        </head>
        <body>
            <p>Redirecting to dashboard...</p>
        </body>
    </html>
    """


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve the live dashboard"""
    dashboard_file = Path(__file__).parent.parent / "dashboard" / "index.html"
    if dashboard_file.exists():
        return FileResponse(dashboard_file)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "prompt-firewall",
        "version": "1.0.0"
    }


@app.post("/check", response_model=CheckResponse)
async def check_prompt(request: CheckRequest):
    """
    Check a prompt against the firewall
    
    Returns decision: allow, block, or sanitize
    """
    try:
        # Check prompt
        response = firewall.check(
            prompt=request.prompt,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return CheckResponse(
            action=response.action.value,
            allowed=response.allowed,
            threat_score=response.threat_score,
            threat_level=response.threat_level.value,
            message=response.message,
            sanitized_prompt=response.sanitized_prompt,
            processing_time_ms=response.processing_time_ms
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get firewall statistics"""
    try:
        stats = firewall.get_stats()
        return StatsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threats")
async def get_threats(limit: int = 10):
    """
    Get recent threat detections
    
    Args:
        limit: Maximum number of threats to return (default: 10)
    """
    try:
        threats = firewall.get_recent_threats(limit=limit)
        return {"threats": threats, "count": len(threats)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch")
async def batch_check(prompts: List[str]):
    """
    Check multiple prompts in batch
    
    Useful for bulk validation
    """
    try:
        results = []
        
        for prompt in prompts:
            response = firewall.check(prompt=prompt)
            results.append({
                "prompt": prompt,
                "action": response.action.value,
                "allowed": response.allowed,
                "threat_score": response.threat_score,
                "threat_level": response.threat_level.value
            })
        
        return {
            "total": len(results),
            "allowed": sum(1 for r in results if r["allowed"]),
            "blocked": sum(1 for r in results if not r["allowed"]),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print(" "*20 + "PROMPT FIREWALL API")
    print("="*70)
    print("\n[*] Starting server...")
    print("    API:       http://localhost:8000")
    print("    Docs:      http://localhost:8000/docs")
    print("    Dashboard: http://localhost:8000/dashboard")
    print("\n[*] Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )