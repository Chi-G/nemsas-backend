# NEMSAS Backend

The backend system for the National Emergency Medical Service and Ambulance System (NEMSAS). This system provides API endpoints for incident management, dispatching, partner coordination, and claims processing.

## Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
- **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **Database:** PostgreSQL (via `asyncpg`)
- **Package Manager:** [UV](https://github.com/astral-uv/uv)
- **Validation:** [Pydantic v2](https://docs.pydantic.dev/)

## Installation

### Prerequisites

- Python 3.12+
- [UV package manager](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/goodnessaig1/nemsas-backend.git
   cd nemsas-backend
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory based on the parameters in `app/core/config.py`. Be sure to configure:
   - `DATABASE_URL` (e.g., `postgresql+asyncpg://user:password@localhost/nemsas`)
   - `SECRET_KEY`
   - `JWT_ALGORITHM`

4. **Run Database Migrations:**
   ```bash
   uv run alembic upgrade head
   ```

5. **Database Seeding:**
   You can populate the reference tables and test data using our hydration scripts located in the `scripts/` directory.
   
   **Bulk Hydration:**
   Populates core data such as States, LGAs, Wards, Users, Roles, and Hospitals:
   ```bash
   PYTHONPATH=. uv run scripts/seed_all.py
   ```

   *Alternatively, you can run individual seeds if needed:*
   - `PYTHONPATH=. uv run scripts/seed_states.py`
   - `PYTHONPATH=. uv run scripts/seed_users.py`

## Development

### Running the server Locally

Start the Uvicorn development server with auto-reload enabled:
```bash
PYTHONPATH=. uv run uvicorn app.main:app --reload
```

Alternatively, use the helper script:
```bash
./scripts/start.sh
```

The API will be accessible at `http://localhost:8000` (or the configured port).
Interactive API Documentation is available at `/docs`.

### Running Tests

```bash
PYTHONPATH=. uv run pytest
```
