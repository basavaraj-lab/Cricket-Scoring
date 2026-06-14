import sys
import os
import importlib.util
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# load score _manage.py (filename has a space)
_spec = importlib.util.spec_from_file_location(
    "score_manage",
    os.path.join(os.path.dirname(__file__), "score _manage.py")
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
save_match        = _mod.save_match
get_all_matches   = _mod.get_all_matches
get_overall_stats = _mod.get_overall_stats
delete_match      = _mod.delete_match

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates-admin")


# ── Pages ────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")

@app.get("/matches", response_class=HTMLResponse)
@app.get("/matches.html", response_class=HTMLResponse, include_in_schema=False)
async def read_matches(request: Request):
    return templates.TemplateResponse(request=request, name="matches.html")

@app.get("/Team", response_class=HTMLResponse)
async def read_team(request: Request):
    return templates.TemplateResponse(request=request, name="Team.html")

@app.get("/table", response_class=HTMLResponse)
async def read_table(request: Request):
    return templates.TemplateResponse(request=request, name="table.html")

@app.get("/status", response_class=HTMLResponse)
async def read_status(request: Request):
    return templates.TemplateResponse(request=request, name="status.html")

@app.get("/stats", response_class=HTMLResponse)
async def read_stats(request: Request):
    return templates.TemplateResponse(request=request, name="stats.html")


# ── API ──────────────────────────────────────────────
@app.post("/api/save-match")
async def api_save_match(request: Request):
    body = await request.json()
    result = save_match(body)
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

app = FastAPI()

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
    del otp_store[email]  # Remove OTP after successful verification

    return {"message": "OTP verified successfully", "token": token}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
