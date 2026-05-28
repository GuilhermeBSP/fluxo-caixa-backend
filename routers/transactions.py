from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date
from database import get_db
from models.account import Account
from models.transaction import Transaction, TransactionType
from models.recurring import RecurringTransaction
from schemas.transaction import TransactionCreate, TransactionOut, RecurringCreate, RecurringOut

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _enrich(tx: Transaction) -> dict:
    d = {c.name: getattr(tx, c.name) for c in tx.__table__.columns}
    d["account_name"] = tx.account.name if tx.account else None
    d["category_name"] = tx.category.name if tx.category else None
    d["category_color"] = tx.category.color if tx.category else None
    return d


@router.get("/", response_model=List[TransactionOut])
def list_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    type: Optional[TransactionType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Transaction).options(
        joinedload(Transaction.account),
        joinedload(Transaction.category),
    )
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if type:
        q = q.filter(Transaction.type == type)
    if start_date:
        q = q.filter(Transaction.date >= start_date)
    if end_date:
        q = q.filter(Transaction.date <= end_date)
    txs = q.order_by(Transaction.date.desc()).all()
    return [TransactionOut(**_enrich(tx)) for tx in txs]


@router.post("/", response_model=TransactionOut, status_code=201)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == data.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    tx = Transaction(**data.model_dump())
    db.add(tx)

    if data.type == TransactionType.income:
        account.balance += data.amount
    else:
        account.balance -= data.amount

    db.commit()
    db.refresh(tx)
    db.refresh(account)
    return TransactionOut(**_enrich(tx))


@router.put("/{tx_id}", response_model=TransactionOut)
def update_transaction(tx_id: int, data: TransactionCreate, db: Session = Depends(get_db)):
    tx = db.query(Transaction).options(
        joinedload(Transaction.account),
        joinedload(Transaction.category),
    ).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    old_account = db.query(Account).filter(Account.id == tx.account_id).first()
    new_account = db.query(Account).filter(Account.id == data.account_id).first()
    if not new_account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")

    if tx.type == TransactionType.income:
        old_account.balance -= tx.amount
    else:
        old_account.balance += tx.amount

    for key, val in data.model_dump().items():
        setattr(tx, key, val)

    if tx.type == TransactionType.income:
        new_account.balance += tx.amount
    else:
        new_account.balance -= tx.amount

    db.commit()
    db.refresh(tx)
    return TransactionOut(**_enrich(tx))


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    tx = db.query(Transaction).options(joinedload(Transaction.account)).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    account = tx.account
    if tx.type == TransactionType.income:
        account.balance -= tx.amount
    else:
        account.balance += tx.amount

    db.delete(tx)
    db.commit()


# --- Recurring ---

router_recurring = APIRouter(prefix="/api/recurring", tags=["recurring"])


def _enrich_rec(rec: RecurringTransaction) -> dict:
    d = {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
    d["account_name"] = rec.account.name if rec.account else None
    d["category_name"] = rec.category.name if rec.category else None
    return d


@router_recurring.get("/", response_model=List[RecurringOut])
def list_recurring(db: Session = Depends(get_db)):
    recs = db.query(RecurringTransaction).options(
        joinedload(RecurringTransaction.account),
        joinedload(RecurringTransaction.category),
    ).order_by(RecurringTransaction.description).all()
    return [RecurringOut(**_enrich_rec(r)) for r in recs]


@router_recurring.post("/", response_model=RecurringOut, status_code=201)
def create_recurring(data: RecurringCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == data.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    rec = RecurringTransaction(**data.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return RecurringOut(**_enrich_rec(rec))


@router_recurring.patch("/{rec_id}/toggle", response_model=RecurringOut)
def toggle_recurring(rec_id: int, db: Session = Depends(get_db)):
    rec = db.query(RecurringTransaction).options(
        joinedload(RecurringTransaction.account),
        joinedload(RecurringTransaction.category),
    ).filter(RecurringTransaction.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recorrência não encontrada")
    rec.active = not rec.active
    db.commit()
    db.refresh(rec)
    return RecurringOut(**_enrich_rec(rec))


@router_recurring.delete("/{rec_id}", status_code=204)
def delete_recurring(rec_id: int, db: Session = Depends(get_db)):
    rec = db.query(RecurringTransaction).filter(RecurringTransaction.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recorrência não encontrada")
    db.delete(rec)
    db.commit()
