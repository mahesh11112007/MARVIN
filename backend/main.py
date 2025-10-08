from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import create, upload, analyze, optimize

app = FastAPI(title="MARVIN API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create.router)
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(optimize.router)

@app.get("/")
def root():
    return {"message": "MARVIN backend is running"}
