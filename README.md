# National Emergency Medical Service and Ambulance System (NEMSAS) Backend

A robust, enterprise-grade backend API powered by **FastAPI** to drive the NEMSAS ecosystem. This system facilitates real-time incident logging, intelligent ambulance dispatch, emergency treatment center coordination, multi-tier claims processing, and electronic runsheet management.

---

### 🌐 Interactive API Documentation
* **Live OpenAPI Docs**: [https://nemsas-api.65.108.209.25.sslip.io/docs#/](https://nemsas-api.65.108.209.25.sslip.io/docs#/)

---

## 🚀 Architectural & System Highlights

1. **Fully Asynchronous Runtime**: Engineered on FastAPI and SQLAlchemy asynchronously utilizing `asyncpg` for maximum throughput and concurrent performance.
2. **Fine-Grained Role-Based Access Control (RBAC)**: Multi-tenant security patterns supporting system actors including Super Administrators, Nemsas Admins, Dispatchers, Ambulance Crews, Treatment Centers, and Observers.
3. **Geographic Information Services (GIS)**: Built-in support for geographic layers (State -> LGA -> Ward) enabling precise geographic routing and incident tracking.
4. **Resilient Seed Data Pipeline**: Batch-oriented seeding scripts designed to parse and load thousands of records, automatically handling missing references and foreign key lookups gracefully.
5. **Enterprise-Grade Security**: Secure JWT-based stateless authentication with token rotation mechanisms.
6. **Real-time Event Architecture**: Websocket manager enabling instant notification dispatch and live status synchronization.

---

## 🛠️ Technology Stack

* **API Engine**: [FastAPI](https://fastapi.tiangolo.com/) (Pydantic v2 validation)
* **Database & ORM**: PostgreSQL, [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async engine)
* **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
* **Package Management**: [Astral UV](https://github.com/astral-uv/uv) (Ultra-fast resolver)
* **Testing Framework**: [Pytest](https://pytest.org/) (Async integration test suites)

---

## 📦 Installation & Local Setup

### Prerequisites
* Python 3.12+
* [UV Package Manager](https://docs.astral.sh/uv/)
* PostgreSQL Database

### Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Sydani-Tech/nemsas-backend.git
   cd nemsas-backend
   ```

2. **Synchronize Dependencies:**
   ```bash
   uv sync
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

4. **Execute Database Migrations:**
   ```bash
   uv run alembic upgrade head
   ```

5. **Hydrate Reference & Metadata Tables:**
   Seed core reference data including LGAs, Wards, States, and Medical Interventions:
   ```bash
   PYTHONPATH=. uv run scripts/seed_all.py
   ```
   
   *Or using python directly:*
   ```bash
   PYTHONPATH=. ./venv/bin/python3 scripts/seed_all.py
   ```

---

## 📡 Running the Server

Start the Uvicorn development server with live reload:
```bash
PYTHONPATH=. uv run uvicorn app.main:app --reload --port 8000
```
The server will start at `http://127.0.0.1:8000`. You can access the local Swagger documentation at `http://127.0.0.1:8000/docs`.

---

## 🧪 Testing

Execute the comprehensive Pytest integration and unit test suites:
```bash
PYTHONPATH=. uv run pytest
```
