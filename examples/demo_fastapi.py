"""
Example FastAPI integration with envsmith
"""
from fastapi import FastAPI, Depends
from envsmith.integrations.fastapi import get_settings

app = FastAPI()

@app.get("/env")
def get_env(settings = Depends(get_settings)):
    return {"env": settings["ENV"]}
