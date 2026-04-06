from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, MY_ENGINE
from app.routers import geometries, rules, missions

Base.metadata.create_all(bind=MY_ENGINE)

app = FastAPI(title="Mission Control Backend V2")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includes our refactored endpoints
app.include_router(missions.router)
app.include_router(geometries.router)
app.include_router(rules.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")