from fastapi import FastAPI
from app.routers import mappings, materials

app = FastAPI(
    title="Mock CPSE SAP/ERP API",
    version="1.0.0",
)

app.include_router(materials.router)
app.include_router(mappings.router)

@app.get("/")
def root():
    return {"service": "Mock SAP/ERP", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}
