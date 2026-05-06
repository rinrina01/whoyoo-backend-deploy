from fastapi import FastAPI,WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from routers.users import router as user_router
from routers.chats import router as chat_router
from routers.matches import router as matches_router
from routers.interests import  router as interest_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(user_router)
app.include_router(chat_router)
app.include_router(matches_router)
app.include_router(interest_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Whoyoo API."}