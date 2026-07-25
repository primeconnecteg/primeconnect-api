#!/bin/bash
# 'set -e' tells Bash to immediately exit if any command fails.
# This prevents the API from starting if the database migration crashes.
set -e

echo "Waiting for PostgreSQL to start..."
# Docker's 'depends_on' only ensures the postgres container is *running*.
# It does NOT guarantee PostgreSQL is actually ready to accept TCP connections.
# This inline Python script loops and attempts a real TCP socket connection until it succeeds.
python -c "
import socket, time, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        s.connect((os.environ['POSTGRES_SERVER'], int(os.environ.get('POSTGRES_PORT', 5432))))
        s.close()
        break
    except socket.error:
        time.sleep(1)
"
echo "PostgreSQL is online and accepting connections!"

echo "Running Alembic database migrations..."
# This applies any new table structures or columns safely.
alembic upgrade head

echo "Seeding the database..."
# This safely ensures the admin user exists (idempotent).
python -m app.scripts.seed_admin

echo "Starting FastAPI Server..."
# 'exec' replaces the current Bash process with Uvicorn.
# This is crucial! If we don't use 'exec', Docker sends shutdown signals (SIGTERM) to Bash, 
# not Uvicorn, resulting in harsh, ungraceful shutdowns.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
