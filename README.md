# PrimeConnect API - Local Development Setup

Welcome to the PrimeConnect API. This document will guide you through setting up the project on your local machine for development.

## Prerequisites

Before you begin, ensure you have the following installed on your laptop:
- [Git](https://git-scm.com/)
- [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/) (Recommended for easy setup)
- Python 3.8+ (If running without Docker)
- PostgreSQL (If running without Docker)

---

## Getting Started

First, clone the repository and navigate into the backend directory:

```bash
git clone <your-repo-url>
cd primeconnect/primeconnect-api
```

### 1. Configure Environment Variables

The project requires environment variables to run. We have provided a template file.

Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
*Note: The default values in `.env.example` are generally fine for local development.*

---

### Option A: Running with Docker (Recommended)

Using Docker is the easiest way to run the API and PostgreSQL database together without installing PostgreSQL natively.

1. **Start the containers** in the background:
   ```bash
   docker-compose up -d --build
   ```

2. **Verify everything is running**:
   ```bash
   docker-compose logs -f
   ```
   *The container will automatically wait for the DB to start, run Alembic migrations, seed the admin user, and start the FastAPI server.*

3. **Stop the containers** when you are done:
   ```bash
   docker-compose down
   ```

---

### Option B: Running Locally (Without Docker)

If you prefer to run the application directly on your machine, follow these steps:

1. **Start your local PostgreSQL server** and create a database matching the credentials in your `.env` file.

2. **Create a virtual environment** and activate it:
   ```bash
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Seed the initial admin user**:
   ```bash
   python -m app.scripts.seed_admin
   ```

6. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Accessing the API

Once the server is running (either via Docker or locally), you can access the API at:
- **Base URL**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs` (Interactive API docs)
- **ReDoc Documentation**: `http://localhost:8000/redoc`

Use the interactive Swagger documentation at `/docs` to explore endpoints and test requests. You can log in using the `ADMIN_USERNAME` and `ADMIN_PASSWORD` from your `.env` file.