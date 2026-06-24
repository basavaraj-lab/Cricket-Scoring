import sys
import os
import random
from typing import List

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from auth import create_access_token, verify_password, get_current_user

user_templates = Jinja2Templates(directory="templates-user")
admin_templates = Jinja2Templates(directory="templates-admin")

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

from fastapi import Request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print("===================================")
    print("Request:", request.method, request.url.path)
    print("Referer:", request.headers.get("referer"))
    print("===================================")

    response = await call_next(request)
    return response

# app.mount("/static", StaticFiles(directory="static"), name="static")
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

#admin login
from fastapi import FastAPI, HTTPException, Depends
import random

from backend.smtp_service import send_email
from otp_store import otp_store
from auth import create_access_token, verify_password, get_current_user 

# app = FastAPI()
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

#websocket
from fastapi import WebSocket, WebSocketDisconnect
connected_clients = []

@app.websocket("/ws/score")
async def websocket_score(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

    print("User Connected")

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print("User Disconnected")

        from fastapi import Body

# current_score = {
#     "runs": 0,
#     "wickets": 0,
#     "overs": "0.0"
# }

from fastapi import FastAPI, Request, Body, WebSocket, WebSocketDisconnect
@app.post("/api/update-score")
async def update_score(score: dict = Body(...)):
    global current_score
    current_score = score
    for client in connected_clients:
        await client.send_json(current_score)
    return {
        "message": "Score Updated",
        "score": current_score
    }
# current_score = {}

from fastapi import Body
from fastapi import Request
from fastapi.responses import JSONResponse

current_score = {
    "runs": 0,
    "wickets": 0,
    "overs": "0.0"
} 
current_match = {
    "team1": "",
    "team2": "",
    "venue": "",
    "date": ""
}

@app.post("/api/update-score")
async def update_score(score: dict = Body(...)):
    global current_score
    global current_match
    # current_score = score

    current_score = score
    current_match = score.get("match", {})

    print("Received from Admin:", current_score)
    print("Connected Clients:", len(connected_clients))
    print("Updated Score:", current_score)

    for client in connected_clients:
        await client.send_json(current_score)

    return {"message": "Score Updated"}

@app.post("/api/update-match")
async def update_match(match: dict = Body(...)):
    global current_match
    current_match = match
    return {"message": "Match Updated"}

@app.get("/api/current-score")
async def get_current_score():
    return current_score

@app.get("/api/match-details")
async def get_match_details():
    return JSONResponse({
        "team1": current_match["team1"],
        "team2": current_match["team2"],
        "venue": current_match["venue"],
        "date": current_match["date"]
    })

@app.get("/api/status")
async def get_status():
    return JSONResponse({
        "status": "live",
        "innings": "1st Innings"
    })

@app.get("/api/team-info")
async def get_team_info():
    return JSONResponse({
        "team1": {
            "name": current_match["team1"],
            "players": ["Player1", "Player2", "Player3"]
        },
        "team2": {
            "name": current_match["team2"],
            "players": ["Player4", "Player5", "Player6"]
        }
    })

from fastapi import Request

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     print("Request:", request.method, request.url.path)
#     response = await call_next(request)
#     return response

@app.get("/user/home")
async def home(request: Request):
    return user_templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/user/match")
async def matches(request: Request):
    return user_templates.TemplateResponse(
        request=request,
        name="match.html"
    )

@app.get("/user/status")
async def status(request: Request):
    return user_templates.TemplateResponse(
        request=request,
        name="status.html"
    )

@app.get("/user/table")
async def table(request: Request):
    return user_templates.TemplateResponse(
        request=request,
        name="table.html"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
