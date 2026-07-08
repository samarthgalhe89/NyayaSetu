"""
FastAPI Application — the entry point for the NyayaSetu API server.

WHAT THIS FILE DOES:
  1. Creates the FastAPI app instance
  2. Adds CORS middleware (allows the browser to call the API)
  3. Registers API routes under /api/
  4. Mounts the ui/static/ directory for CSS & JS files
  5. Serves ui/index.html at the root / URL

KEY INSIGHT:
  By mounting static files here, we don't need a separate web server like
  Nginx. FastAPI serves EVERYTHING — both the API endpoints and the frontend
  HTML/CSS/JS files. One command, one server.

HOW CORS WORKS:
  When your browser loads a page from localhost:8000 and that page's JavaScript
  tries to call localhost:8000/api/query, the browser checks CORS rules. Our
  middleware says "allow everything" (fine for development — restrict in production).
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router

# ── Create the FastAPI application ───────────────────────────────────────
app = FastAPI(
    title="NyayaSetu API",
    description="AI-powered Indian legal rights navigator — Know Your Rights",
    version="1.0.0",
)

# ── CORS Middleware ──────────────────────────────────────────────────────
# Allows the frontend (or any client) to call the API from any origin.
# In production, replace allow_origins=["*"] with your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routes ─────────────────────────────────────────────────
# All routes from routes.py will be prefixed with /api/
# So @router.post("/query") becomes /api/query
app.include_router(router, prefix="/api")

# ── Serve Static Files (CSS, JS) ────────────────────────────────────────
# This makes files in ui/static/ accessible at /static/...
# For example: ui/static/css/style.css → http://localhost:8000/static/css/style.css
ui_static_dir = Path(__file__).parent.parent / "ui" / "static"
if ui_static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(ui_static_dir)), name="static")

# ── Serve the Frontend HTML ─────────────────────────────────────────────
# When someone visits http://localhost:8000/, they get the chat UI
ui_index = Path(__file__).parent.parent / "ui" / "index.html"


@app.get("/")
async def serve_frontend():
    """Serve the NyayaSetu frontend."""
    if ui_index.exists():
        return FileResponse(str(ui_index))
    return {"message": "NyayaSetu API is running. Frontend not found at ui/index.html."}
