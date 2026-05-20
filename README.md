# ai-inquiry-support-app

AI inquiry support application.

## Phase 1

This phase provides the minimum backend foundation:

- FastAPI application startup
- PostgreSQL startup with Docker Compose
- PostgreSQL connection from the application
- `GET /health`
- `POST /inquiries`

## Phase 2

AI classification will use OpenAI API settings from environment variables:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=your_model_name_here
```

Do not commit a real `.env` file or API key.

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
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=your_model_name_here
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

Classify an inquiry:

```bash
curl -X POST http://localhost:8000/inquiries/1/classify
```
