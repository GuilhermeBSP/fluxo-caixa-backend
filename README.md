# Fluxo de Caixa

Sistema pessoal de controle financeiro com FastAPI + SQLite.

## Instalação

```bash
cd fluxo-caixa
pip install -r requirements.txt
```

## Executar

```bash
# Popular o banco com dados de exemplo (opcional, só na primeira vez)
python seed.py

# Iniciar o servidor
uvicorn main:app --reload
```

Acesse: http://localhost:8000

## Funcionalidades

| Página | URL |
|--------|-----|
| Dashboard | `/` |
| Transações | `/transactions` |
| Recorrentes | `/recurring` |
| Contas | `/accounts` |
| Categorias | `/categories` |
| Relatórios | `/reports` |
| API Docs | `/api/docs` |

## Estrutura

```
fluxo-caixa/
├── main.py              # App FastAPI + rotas de páginas
├── database.py          # Configuração SQLAlchemy
├── models/              # ORM: Account, Category, Transaction, Recurring
├── schemas/             # Pydantic: validação de entrada/saída
├── routers/             # Endpoints REST da API
├── services/            # Lógica de negócio (recorrências)
├── templates/           # HTML com Jinja2
└── static/              # CSS customizado
```

## Modelos de dados

- **Account** — Contas (corrente, poupança, carteira, cartão)
- **Category** — Categorias de receita ou despesa com cor customizável
- **Transaction** — Transação avulsa (receita ou despesa)
- **RecurringTransaction** — Modelo para lançamentos recorrentes mensais
