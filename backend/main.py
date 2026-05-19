from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates-admin")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html"
    )

@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home.html"
    )

@app.get("/matches", response_class=HTMLResponse)
@app.get("/matches.html", response_class=HTMLResponse, include_in_schema=False)
async def read_matches(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="matches.html"
    )

@app.get("/Team", response_class=HTMLResponse)
async def read_team(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="Team.html"
    )

@app.get("/table", response_class=HTMLResponse)
async def read_table(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="table.html"
    )

@app.get("/status", response_class=HTMLResponse)
async def read_status(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="status.html"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)