from fastapi import FastAPI
from routers.users import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def root():
    return {"message": "success"}

@app.get("/test")
def root2():
    return {"message": "hello there"}