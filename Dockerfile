# 1. BASE IMAGE
# We use Python 3.13 'slim' because it contains just enough OS libraries to run Python.
# It strips out hundreds of megabytes of unnecessary Debian utilities, keeping the image small.
FROM python:3.13-slim

# 2. ENVIRONMENT VARIABLES
# Prevents Python from writing .pyc files to disk (saving space and IO)
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures Python output goes straight to terminal without buffering, critical for Docker logs
ENV PYTHONUNBUFFERED=1

# 3. WORK DIRECTORY
# This is where all subsequent commands will run inside the container.
WORKDIR /app

# 4. SYSTEM DEPENDENCIES
# We need build-essential and libpq-dev because some Python packages (like asyncpg) 
# must compile C extensions to communicate with PostgreSQL.
# We clean up the apt lists in the same RUN command to keep the Docker image layer tiny.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. PYTHON DEPENDENCIES
# We COPY only requirements.txt first. 
# Docker caches this layer. If you change your code but NOT your requirements,
# Docker skips the 5-minute 'pip install' step and instantly uses the cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. SECURITY: NON-ROOT USER
# Running web servers as 'root' inside Docker is a severe security vulnerability.
# We create a generic 'appuser' with zero system privileges.
RUN addgroup --system appgroup && adduser --system --group appuser

# 7. COPY APPLICATION CODE
# Now we copy the rest of the application into the container.
COPY . .

# 8. PERMISSIONS
# Make the entrypoint script executable, and give 'appuser' ownership of the /app directory.
RUN chmod +x /app/entrypoint.sh
RUN chown -R appuser:appgroup /app

# 9. USER SWITCH
# From this line down, Docker runs everything as the unprivileged user.
USER appuser

# 10. EXPOSE PORT
# Informs Docker that the container listens on port 8000
EXPOSE 8000

# 11. ENTRYPOINT
# Instead of directly running Uvicorn, we run a shell script that handles migrations first.
ENTRYPOINT ["/app/entrypoint.sh"]
