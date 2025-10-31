from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import routes


app = FastAPI(
    title="Fakestore API - FastAPI - IA", 
    version="0.0.1"
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

app.include_router(routes)
