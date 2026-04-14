# -- scripts imports --
from app.routers import geometries, rules, missions
from app.database import Base, MY_ENGINE
# -- fastapi imports --
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from fastapi import FastAPI, Request
from datetime import datetime
import uvicorn
import json

# create db tables
Base.metadata.create_all(bind=MY_ENGINE)
# create app
app = FastAPI(title="Mission Control Backend V2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# include the routers
app.include_router(missions.router)
app.include_router(geometries.router)
app.include_router(rules.router)


@app.middleware("http")
async def log_with_response(request: Request, call_next):
    request_body = await request.body()  # get the request body if exist

    async def receive():
        return {"type": "http.request", "body": request_body}

    request._receive = receive
    response = await call_next(request)  # send the request and capture the response data
    response_body = b''
    async for chunk in response.body_iterator:
        response_body += chunk

    path_parts = request.url.path.rstrip("/").split("/")
    resource = path_parts[-2] if len(path_parts) > 1 and path_parts[-1].isdigit() else path_parts[-1]
    timestamp = str(datetime.now())[:-3]
    log_msg = f"--- {timestamp} | {request.method} {resource} ---"

    if request_body:
        # get in only if a REQUEST was sent! - not GET route
        try:
            data_json = json.loads(request_body)
            log_msg += f" INPUT DATA: {data_json}"
        except:
            log_msg += f" INPUT DATA: {request_body.decode()}"
    log_msg += f" STATUS: {response.status_code}"
    if response.status_code != 200:
        log_msg += f" !!! ERROR DETAILS: {response_body.decode()}"
    print(log_msg)

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type
    )


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug", access_log=False)