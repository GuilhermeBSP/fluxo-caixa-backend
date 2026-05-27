from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import date
from database import get_db
from models.transaction import Transaction, TransactionType
from models.category import Category
from models.account import Account

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary")
def monthly_summary(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month),
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Transaction).filter(
        extract("year", Transaction.date) == year,
        extract("month", Transaction.date) == month,
    )
    if account_id:
        q = q.filter(Transaction.account_id == account_id)

    transactions = q.all()

    total_income = sum(t.amount for t in transactions if t.type == TransactionType.income)
    total_expense = sum(t.amount for t in transactions if t.type == TransactionType.expense)

    return {
        "year": year,
        "month": month,
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "balance": round(total_income - total_expense, 2),
        "transaction_count": len(transactions),
    }


@router.get("/by-category")
def expenses_by_category(
    year: int = Query(default=date.today().year),
    month: int = Query(default=date.today().month),
    type: TransactionType = TransactionType.expense,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.type == type,
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
        )
    )
    if account_id:
        q = q.filter(Transaction.account_id == account_id)

    rows = q.group_by(Category.id).order_by(func.sum(Transaction.amount).desc()).all()

    return [{"category": r.name, "color": r.color, "total": round(r.total, 2)} for r in rows]


@router.get("/monthly-evolution")
def monthly_evolution(
    months: int = Query(default=6, ge=1, le=24),
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    today = date.today()
    result = []

    for i in range(months - 1, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1

        q = db.query(Transaction).filter(
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
        )
        if account_id:
            q = q.filter(Transaction.account_id == account_id)

        txs = q.all()
        income = sum(t.amount for t in txs if t.type == TransactionType.income)
        expense = sum(t.amount for t in txs if t.type == TransactionType.expense)

        result.append({
            "label": f"{month:02d}/{year}",
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(income - expense, 2),
        })

    return result


@router.get("/account-balances")
def account_balances(db: Session = Depends(get_db)):
    accounts = db.query(Account).order_by(Account.name).all()
    return [{"name": a.name, "type": a.type.value, "balance": round(a.balance, 2)} for a in accounts]
