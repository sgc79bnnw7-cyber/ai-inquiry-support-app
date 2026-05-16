# ai-inquiry-support-app

AI inquiry support application.

## Phase 1

This phase provides the minimum backend foundation:

- FastAPI application startup
- PostgreSQL startup with Docker Compose
- PostgreSQL connection from the application
- `GET /health`
- `POST /inquiries`

## Files

- `app/main.py`: FastAPI routes
- `app/database.py`: SQLAlchemy engine and session setup
- `app/models.py`: SQLAlchemy models
- `app/schemas.py`: Pydantic schemas
- `app/crud.py`: Database write operations
- `docker-compose.yml`: PostgreSQL service
- `.env.example`: Example database connection URL
- `requirements.txt`: Python dependencies

## Setup

Create a virtual environment and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
pip --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start PostgreSQL:

```bash
docker compose up -d
```

Set the database URL:

```bash
export DATABASE_URL=postgresql+psycopg://app_user:app_password@localhost:5432/ai_inquiry_support
```

Start the API:

```bash
uvicorn app.main:app --reload
```

## Check

Health check:

```bash
curl http://localhost:8000/health
```

Create an inquiry:

```bash
curl -X POST http://localhost:8000/inquiries \
  -H "Content-Type: application/json" \
  -d '{"body":"問い合わせ本文のサンプルです"}'
```
