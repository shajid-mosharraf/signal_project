from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api import dsp_routes
from api import dsp_routes, matcher_routes

app = FastAPI(title="Master Audio Lab API")

# Mount API routes
app.include_router(dsp_routes.router, prefix="/api")
app.include_router(matcher_routes.router, prefix="/api/matcher")

# Mount static files (Frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

