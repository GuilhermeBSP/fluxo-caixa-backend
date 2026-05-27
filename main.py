from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models  # noqa: F401 — registers all models before table creation

from routers.accounts import router as accounts_router
from routers.categories import router as categories_router
from routers.transactions import router as transactions_router, router_recurring
from routers.reports import router as reports_router
from routers.ai import router as ai_router
from services.recurring_service import apply_recurring_for_month
from database import SessionLocal

app = FastAPI(title="Fluxo de Caixa", docs_url="/api/docs")

Base.metadata.create_all(bind=engine)

_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(router_recurring)
app.include_router(reports_router)
app.include_router(ai_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/recurring/apply")
def apply_recurring(year: int = Query(default=None), month: int = Query(default=None)):
    from datetime import date
    today = date.today()
    y = year or today.year
    m = month or today.month
    db = SessionLocal()
    try:
        created = apply_recurring_for_month(db, y, m)
        return {"created": len(created), "year": y, "month": m}
    finally:
        db.close()
