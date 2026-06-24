import sys
import os
import random
from typing import List

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Setup paths
sys.path.insert(0, os.path.dirname(__file__))

# Import score management
import score_manage
save_match        = score_manage.save_match
get_all_matches   = score_manage.get_all_matches
get_overall_stats = score_manage.get_overall_stats
delete_match      = score_manage.delete_match

# Import other services
from smtp_service import send_email
from otp_store import otp_store
from auth import create_access_token

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Template engines
templates_admin = Jinja2Templates(directory="templates-admin")
templates_user = Jinja2Templates(directory="templates-user")

# ── WebSocket Manager ────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass # Handle dead connections if needed

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We receive updates from the scorer here
            data = await websocket.receive_json()
            if data.get("type") == "score_update":
                # Broadcast the score update to all connected users
                await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ── Admin Pages ──────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates_admin.TemplateResponse(request=request, name="home.html")

@app.get("/matches", response_class=HTMLResponse)
async def read_matches(request: Request):
    return templates_admin.TemplateResponse(request=request, name="matches.html")

@app.get("/Team", response_class=HTMLResponse)
async def read_team(request: Request):
    return templates_admin.TemplateResponse(request=request, name="Team.html")

@app.get("/table", response_class=HTMLResponse)
async def read_table(request: Request):
    return templates_admin.TemplateResponse(request=request, name="table.html")

@app.get("/status", response_class=HTMLResponse)
async def read_status(request: Request):
    return templates_admin.TemplateResponse(request=request, name="status.html")

@app.get("/stats", response_class=HTMLResponse)
async def read_stats(request: Request):
    return templates_admin.TemplateResponse(request=request, name="stats.html")

# ── User Pages ───────────────────────────────────────
@app.get("/user", response_class=HTMLResponse)
@app.get("/user/home", response_class=HTMLResponse)
async def user_home(request: Request):
    return templates_user.TemplateResponse(request=request, name="index.html")

@app.get("/user/match", response_class=HTMLResponse)
async def user_match(request: Request):
    return templates_user.TemplateResponse(request=request, name="match.html")

@app.get("/user/status", response_class=HTMLResponse)
async def user_status(request: Request):
    return templates_user.TemplateResponse(request=request, name="status.html")

@app.get("/user/table", response_class=HTMLResponse)
async def user_table(request: Request):
    return templates_user.TemplateResponse(request=request, name="table.html")

# ── API ──────────────────────────────────────────────
@app.post("/api/save-match")
async def api_save_match(request: Request):
    body = await request.json()
    result = save_match(body)
    # Also broadcast when a match is saved (finalized)
    await manager.broadcast({"type": "match_saved", "data": body})
    return JSONResponse(result)

@app.get("/api/matches")
async def api_get_matches():
    return JSONResponse(get_all_matches())

@app.get("/api/stats")
async def api_get_stats():
    return JSONResponse(get_overall_stats())

@app.delete("/api/delete-match/{match_id}")
async def api_delete_match(match_id: int):
    ok = delete_match(match_id)
    return JSONResponse({"deleted": ok})

@app.post("/admin/send-otp")
def send_admin_otp(email: str):
    otp = random.randint(100000, 999999)
    otp_store[email] = otp
    if send_email(email, otp):
        return {"message": "OTP sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    
@app.post("/admin/verify-otp")
def verify_admin_otp(email: str, otp: int):
    stored_otp = otp_store.get(email)
    if not stored_otp:
        raise HTTPException(status_code=400, detail="No OTP sent to this email")
    if stored_otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    token = create_access_token({"sub": email})
    del otp_store[email]
    return {"message": "OTP verified successfully", "token": token}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
