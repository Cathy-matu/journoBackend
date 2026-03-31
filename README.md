# JournoMind Connect Backend

FastAPI + PostgreSQL backend for the JournoMind psychosocial support platform.

## Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- pip

### Installation Steps

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate           # macOS/Linux
   # OR
   venv\Scripts\activate              # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your actual credentials:
   # - DATABASE_URL: PostgreSQL connection string
   # - ANTHROPIC_API_KEY: Claude API key (optional, but recommended)
   # - FRONTEND_URL: Your frontend development/production URL
   ```

4. **Initialize the database:**
   ```bash
   # Create database tables
   alembic upgrade head
   ```

5. **Run the development server:**
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   
   The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - API health check
- `GET /api/health` - Detailed health status
- `GET /api/experts` - List available trauma specialists
- `POST /api/chat` - Send a message to a specialist
- `POST /api/assessment` - Submit wellbeing assessment

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "your migration name"
```

Apply migrations:
```bash
alembic upgrade head
```

## Environment Variables

See `.env.example` for all available configuration options.

**Important**: Never commit `.env` containing real credentials. Always use `.env.example` as a template.