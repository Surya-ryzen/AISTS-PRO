"""Standalone Week 10 demo; uses the existing project's authentication and DB layer."""
from fastapi import FastAPI
from backend.app.api.auth import router as auth_router
from backend.app.api.week10 import router

app = FastAPI(title='AI Smart Traffic System', version='0.1.0')
app.include_router(auth_router)
app.include_router(router)


@app.get('/', include_in_schema=False)
def home():
    from fastapi.responses import RedirectResponse
    return RedirectResponse('/docs')
