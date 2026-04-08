# NEMSAS Backend

The backend system for the National Emergency Medical Service and Ambulance System (NEMSAS). This system provides API endpoints for incident management, dispatching, and partner coordination.

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

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sydani-Tech/nemsas-backend.git
   cd nemsas-backend
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your configurations (refer to `src/core/config.py` for required variables).

4. **Run Database Migrations:**
   ```bash
   uv run alembic upgrade head
   ```

5. **Database Seeding:**
   The repository contains two seeding scripts, each serving a different purpose. You must run `seed.py` first, but `demo_data.py` is only for testing environments.
   
   **A. Master Reference Data (Required):**
   This populates the database with essential, non-test data like States, LGAs, Drugs, and core User Roles. It is safe and idempotent.
   ```bash
   PYTHONPATH=. uv run scripts/seed.py
   ```
   
   **B. Operational Demo Data (Development Only):**
   This populates the database with a simulated workflow including fake partners, ambulances, incidents, claims, and dummy users. **Do not run this in production.**
   ```bash
   PYTHONPATH=. uv run scripts/demo_data.py
   ```

## Test User Roles & Credentials

If you have run **both** seeding scripts locally, the following test accounts are available to help you test role-based access.

**Super Admin Account:**
- **Email:** `admin@nemsas.gov.ng`
- **Password:** `chibuike4u` *(Created during `seed.py`)*

**Dummy Testing Accounts (Created by `demo_data.py`):**
*The password for all accounts below is `password123`*

| Role | Email Login |
| :--- | :--- |
| **SEMSAS Admin** | `semsas_admin@demo.com` |
| **Ambulance Crew** | `crew@demo.com` |
| **Dispatcher** | `dispatcher@demo.com` |
| **Partner (Fleet Mgr)** | `partner@demo.com` |
| **Emergency Transport Provider** | `etp@demo.com` |
| **ETC Staff** | `etc_staff@demo.com` |
| **Claims Staff** | `claims_staff@demo.com` |
| **View-Only User** | `view_only@demo.com` |


## Development

### Running the server Locally

```bash
uv run uvicorn src.main:app --reload
```

The API will be accessible at `http://localhost:8000`.
Documentation is available at `http://localhost:8000/docs`.

### Running Tests

```bash
uv run pytest
```
