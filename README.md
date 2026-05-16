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
   Populates all core data, reference types, entities (Ambulances, Hospitals), Incidents, and Patients in the correct dependency order:
   ```bash
   PYTHONPATH=. ./venv/bin/python3 scripts/seed_all.py
   ```

   **Individual Seeders (Optimized & Resilient):**
   These scripts use batch processing and handle missing foreign keys gracefully:
   - **Incidents:** `PYTHONPATH=. ./venv/bin/python3 scripts/seed_incidents.py`
   - **Patients:** `PYTHONPATH=. ./venv/bin/python3 scripts/seed_patients.py`
   - **Ambulances:** `PYTHONPATH=. ./venv/bin/python3 scripts/seed_ambulances.py`
   - **Hospitals:** `PYTHONPATH=. ./venv/bin/python3 scripts/seed_hospitals.py`

   **Update Incident State IDs:**
   Syncs incident `state_id` based on `state_name` using `states.json`:
   ```bash
   PYTHONPATH=. ./venv/bin/python3 scripts/update_incident_state_ids.py
   ```

   **Monitor Progress:**
   Check the current record counts in the database:
   ```bash
   ./venv/bin/python3 scripts/check_counts.py
   ```

### Utility Scripts

**Update User Email:**
Finds a user by email and updates it to a new one (e.g., updating `ahmednu@datharm.com` to `ahmednu@texis.com`):
```bash
PYTHONPATH=. ./venv/bin/python3 scripts/update_user_email.py
```

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
