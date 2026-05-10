# nemsas-backend
# NEMSAS Backend

This is the backend service for the National Emergency Medical Services and Ambulance System (NEMSAS), built with FastAPI and SQLAlchemy.

## 🚀 Features

- **FastAPI Framework**: High-performance, easy-to-learn, fast-to-code, ready-for-production.
- **SQLAlchemy ORM**: Robust database toolkit and Object Relational Mapper.
- **Alembic**: Database migration tool.
- **JWT Authentication**: Secure user authentication and authorization.
- **Password Security**: Password hashing with bcrypt.
- **Comprehensive Health Data Management**: Centralized management for hospitals, emergency treatment centers, ambulances, and their medical personnel.

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis (optional, for caching/background tasks)

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd nemsas-backend
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🔄 Database Setup

1.  **Apply migrations:**
    ```bash
    alembic upgrade head
    ```

## 🏃‍♂️ Running the Server

Start the development server with hot-reload:

```bash
uvicorn app.main:app --reload --host [IP_ADDRESS] --port 8000
```

The API will be available at `http://[IP_ADDRESS]`.

## 📊 API Documentation

Documentation is available at:
- **Swagger UI**: `http://[IP_ADDRESS]/docs`
- **ReDoc**: `http://[IP_ADDRESS]/redoc`

## 📁 Project Structure

```
nemsas-backend/
├── app/
│   ├── api/
│   │   └── v1/               # API endpoints organized by version
│   │       ├── endpoints/      # Route handlers for different resources
│   │       └── deps.py         # Dependency injection utilities
│   ├── core/                 # Core application configuration
│   ├── crud/                 # Database CRUD operations
│   ├── models/               # SQLAlchemy database models
│   ├── schemas/              # Pydantic data validation schemas
│   ├── services/             # Business logic services
│   └── tests/                # Unit and integration tests
├── alembic/                  # Alembic migration scripts
├── scripts/                  # Utility scripts (e.g., data seeding)
└── tests/                    # Full test suite
```