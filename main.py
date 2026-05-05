from fastapi import FastAPI,WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from routers.users import router as user_router
from routers.chats import router as chat_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(user_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Whoyoo API."}

clients = []
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()  # accept immediately

    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for client in clients:
                await client.send_text(data)
    except WebSocketDisconnect:
        clients.remove(websocket)