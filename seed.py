"""Run once to populate the database with sample data."""
from database import engine, SessionLocal, Base
import models  # noqa
from models.account import Account, AccountType
from models.category import Category, CategoryType
from models.transaction import Transaction, TransactionType
from models.recurring import RecurringTransaction, RecurringType
from datetime import date, timedelta
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Accounts
conta_corrente = Account(name="Nubank", type=AccountType.checking, balance=0)
poupanca = Account(name="Caixa Poupança", type=AccountType.savings, balance=0)
carteira = Account(name="Carteira", type=AccountType.cash, balance=0)
db.add_all([conta_corrente, poupanca, carteira])
db.commit()

# Categories
cats = [
    Category(name="Salário", type=CategoryType.income, color="#198754"),
    Category(name="Freelance", type=CategoryType.income, color="#20c997"),
    Category(name="Investimentos", type=CategoryType.income, color="#0dcaf0"),
    Category(name="Alimentação", type=CategoryType.expense, color="#dc3545"),
    Category(name="Transporte", type=CategoryType.expense, color="#fd7e14"),
    Category(name="Moradia", type=CategoryType.expense, color="#6610f2"),
    Category(name="Saúde", type=CategoryType.expense, color="#d63384"),
    Category(name="Lazer", type=CategoryType.expense, color="#0d6efd"),
    Category(name="Assinaturas", type=CategoryType.expense, color="#6c757d"),
    Category(name="Educação", type=CategoryType.expense, color="#ffc107"),
]
db.add_all(cats)
db.commit()

cat = {c.name: c for c in cats}

# Recurring
recs = [
    RecurringTransaction(account_id=conta_corrente.id, category_id=cat["Salário"].id, type=RecurringType.income, amount=5000, description="Salário mensal", day_of_month=5),
    RecurringTransaction(account_id=conta_corrente.id, category_id=cat["Moradia"].id, type=RecurringType.expense, amount=1200, description="Aluguel", day_of_month=10),
    RecurringTransaction(account_id=conta_corrente.id, category_id=cat["Assinaturas"].id, type=RecurringType.expense, amount=55.90, description="Netflix + Spotify", day_of_month=15),
]
db.add_all(recs)
db.commit()

# Sample transactions for the last 3 months
today = date.today()
txs = []
for delta_month in range(2, -1, -1):
    m = today.month - delta_month
    y = today.year
    while m <= 0:
        m += 12
        y -= 1

    txs += [
        Transaction(account_id=conta_corrente.id, category_id=cat["Salário"].id, type=TransactionType.income, amount=5000, description="Salário mensal", date=date(y, m, 5)),
        Transaction(account_id=conta_corrente.id, category_id=cat["Moradia"].id, type=TransactionType.expense, amount=1200, description="Aluguel", date=date(y, m, 10)),
        Transaction(account_id=conta_corrente.id, category_id=cat["Alimentação"].id, type=TransactionType.expense, amount=round(random.uniform(600, 900), 2), description="Supermercado", date=date(y, m, random.randint(1,28))),
        Transaction(account_id=conta_corrente.id, category_id=cat["Transporte"].id, type=TransactionType.expense, amount=round(random.uniform(150, 300), 2), description="Combustível/Uber", date=date(y, m, random.randint(1,28))),
        Transaction(account_id=conta_corrente.id, category_id=cat["Lazer"].id, type=TransactionType.expense, amount=round(random.uniform(100, 350), 2), description="Restaurante/Cinema", date=date(y, m, random.randint(1,28))),
        Transaction(account_id=conta_corrente.id, category_id=cat["Assinaturas"].id, type=TransactionType.expense, amount=55.90, description="Netflix + Spotify", date=date(y, m, 15)),
    ]
    if delta_month == 1:
        txs.append(Transaction(account_id=conta_corrente.id, category_id=cat["Freelance"].id, type=TransactionType.income, amount=1500, description="Projeto freelance", date=date(y, m, random.randint(1,28))))

for tx in txs:
    db.add(tx)
    acct = db.query(Account).filter(Account.id == tx.account_id).first()
    if tx.type == TransactionType.income:
        acct.balance += tx.amount
    else:
        acct.balance -= tx.amount

db.commit()
db.close()
print("Dados de exemplo inseridos com sucesso!")
