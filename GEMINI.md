# Gemini / Antigravity AI Agent Guidelines for NEMSAS

This document serves as the primary system prompt extension for Gemini when working on the **NEMSAS (National Emergency Medical Service and Ambulance System) Backend**.

## Project Overview
NEMSAS is an enterprise emergency medical response platform handling the entire lifecycle of an emergency:
1. **Incident Logging:** Multi-channel (App, USSD, SMS).
2. **Dispatch:** Real-time distance calculation (Google Maps) and WebSocket-based ambulance assignment.
3. **Electronic Run Sheets:** Progressively saved patient care records signed by the ambulance crew and co-signed by the destination ETC.
4. **Claims & Billing:** Automated fee calculation (BLS fixed, ALS variable) and approval workflows.
5. **Fleet & Partner Management:** Ambulance tracking, bulk registration, and health facility pledges.
6. **Gap Analysis GIS:** Population vs. Ambulance coverage mapping at State and LGA levels.

## Core Directives for the AI Agent

### 1. Technology & Standards
- **Strictly Asynchronous:** The project is built on FastAPI and SQLAlchemy 2.0 with `asyncpg`. When writing CRUD operations, you **must** use `AsyncSession` and async syntax (e.g., `await session.execute(select(Model))`). Do not introduce synchronous blocking code.
- **Package Management:** The project uses `uv`. Do not suggest `pip install`. If dependencies are needed, execute `uv add <package_name>`.
- **Validation:** Rely on Pydantic v2. Ensure clear segregation between Database Models (`app/models/`) and API Schemas (`app/schemas/`).

### 2. Implementation Workflow
- **Understand the Schema:** Before making changes, always inspect the relevant `app/models/` and `app/crud/` files. Reference data (States, LGAs, Drugs) is pre-seeded and heavily relied upon via Foreign Keys.
- **Alembic Migrations:** Whenever you modify an SQLAlchemy model, you must generate a migration (`uv run alembic revision --autogenerate -m "your message"`) and apply it (`uv run alembic upgrade head`).
- **RBAC Enforcement:** Ensure that endpoints respect Role-Based Access Control. E.g., SEMSAS Admins can only see data for their specific State. Validate these constraints in the API or CRUD layers.
- **Real-Time Consistency:** When an incident status changes or an ambulance moves, remember to invoke the Socket.IO manager (`app.core.socket_manager.sio`) and push notifications (`app.core.notifications`) to broadcast updates.

### 3. File Structure Navigation
- `app/api/v1/endpoints/`: Controllers and routers.
- `app/services/`: Core business logic (e.g., dispatch algorithm, fee calculations).
- `app/crud/`: Reusable database query logic.
- `tests/`: Integration and unit tests using `pytest` and `httpx.AsyncClient`.

### 4. Error Handling
- The application uses custom exception handlers (defined in `main.py`) that expect a specific JSON structure. When raising an `HTTPException`, use:
  ```python
  raise HTTPException(
      status_code=400,
      detail={"message": "Human readable message", "error": "Technical details or code"}
  )
  ```

### 5. Security & SecureCoder Compliance
- Never log plain text passwords. Ensure bcrypt hashing (cost >= 12).
- Follow all mandatory secure web skills (prevent SQL injection by always using SQLAlchemy ORM, no raw string formatting in SQL).
- Audit trails must be maintained for user actions, status changes, and claims processing.

**Agent Objective:** Build resilient, high-performance, and secure endpoints that align strictly with the NEMSAS architectural blueprints.
