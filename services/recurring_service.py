from sqlalchemy.orm import Session
from datetime import date
from models.recurring import RecurringTransaction
from models.transaction import Transaction, TransactionType


def apply_recurring_for_month(db: Session, year: int, month: int):
    """Generates transactions from active recurring entries for the given month/year."""
    recurrings = db.query(RecurringTransaction).filter(RecurringTransaction.active == True).all()
    created = []

    for rec in recurrings:
        day = min(rec.day_of_month, _last_day_of_month(year, month))
        target_date = date(year, month, day)

        already_exists = db.query(Transaction).filter(
            Transaction.recurring_id == rec.id,
            Transaction.date == target_date,
        ).first()

        if already_exists:
            continue

        tx = Transaction(
            account_id=rec.account_id,
            category_id=rec.category_id,
            recurring_id=rec.id,
            type=TransactionType(rec.type.value),
            amount=rec.amount,
            description=rec.description,
            date=target_date,
        )
        db.add(tx)
        _update_account_balance(db, rec.account_id, rec.type.value, rec.amount)
        created.append(tx)

    db.commit()
    return created


def _update_account_balance(db: Session, account_id: int, tx_type: str, amount: float):
    from models.account import Account
    account = db.query(Account).filter(Account.id == account_id).first()
    if account:
        if tx_type == "income":
            account.balance += amount
        else:
            account.balance -= amount


def _last_day_of_month(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]
