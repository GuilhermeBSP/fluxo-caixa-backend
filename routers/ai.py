import os
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.transaction import Transaction, TransactionType
from models.account import Account
from models.category import Category
from groq import Groq
from datetime import date

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str


def _financial_context(db: Session) -> str:
    today = date.today()
    start = today.replace(day=1)

    txs = db.query(Transaction).filter(
        Transaction.date >= start, Transaction.date <= today
    ).all()

    income  = sum(t.amount for t in txs if t.type == TransactionType.income)
    expense = sum(t.amount for t in txs if t.type == TransactionType.expense)

    accounts = db.query(Account).all()

    recent = (
        db.query(Transaction)
        .order_by(Transaction.date.desc())
        .limit(10)
        .all()
    )

    cat_expense = (
        db.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(Transaction.type == TransactionType.expense, Transaction.date >= start)
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )

    lines = [
        f"DADOS FINANCEIROS ({today.strftime('%B/%Y')}):",
        f"- Receitas do mês: R$ {income:,.2f}",
        f"- Despesas do mês: R$ {expense:,.2f}",
        f"- Saldo do período: R$ {income - expense:,.2f}",
        "",
        "SALDO DAS CONTAS:",
    ] + [f"- {a.name}: R$ {a.balance:,.2f}" for a in accounts] + [
        "",
        "TOP DESPESAS POR CATEGORIA (mês atual):",
    ] + ([f"- {c}: R$ {t:,.2f}" for c, t in cat_expense] if cat_expense else ["- Sem dados"]) + [
        "",
        "ÚLTIMAS 10 TRANSAÇÕES:",
    ] + [
        f"- {t.date} | {t.description} | "
        f"{'+ R$ ' if t.type == TransactionType.income else '- R$ '}{t.amount:,.2f}"
        for t in recent
    ]

    return "\n".join(lines)


@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        def err():
            yield "data: " + json.dumps({"text": "⚠️ GROQ_API_KEY não configurada. Crie um arquivo .env com sua chave da Groq."}) + "\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(err(), media_type="text/event-stream")

    ctx = _financial_context(db)
    system = (
        "Você é um assistente financeiro pessoal inteligente e empático. "
        "Você tem acesso aos dados financeiros reais do usuário e deve usá-los para dar conselhos personalizados. "
        "Responda sempre em português brasileiro, de forma clara e objetiva. "
        "Quando relevante, cite números específicos dos dados do usuário. "
        "Dê conselhos práticos e acionáveis. Seja conciso.\n\n"
        + ctx
    )

    def stream():
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": req.message},
            ],
            stream=True,
            max_tokens=1024,
        )
        for chunk in response:
            text = chunk.choices[0].delta.content or ""
            if text:
                yield "data: " + json.dumps({"text": text}) + "\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
