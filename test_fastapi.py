from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI(root_path="/api")

@app.get("/test")
def test():
    return {"ok": True}

client = TestClient(app)
print("Root path behavior:")
print("Request /test:", client.get("/test").status_code)
print("Request /api/test:", client.get("/api/test").status_code)
