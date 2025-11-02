# Multi-stage Dockerfile for Koyeb deployment
# This Dockerfile builds both frontend and backend and serves them together

# ============================================================================
# Stage 1: Build Frontend
# ============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies (including dev dependencies needed for build)
# Using npm install instead of npm ci since package-lock.json may not exist
# For production, consider committing package-lock.json and using: npm ci
RUN npm install --legacy-peer-deps

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# ============================================================================
# Stage 2: Build Backend and Serve Everything
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code as a package (preserves relative imports)
COPY backend/ ./backend/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./static

# Create workspace directory for MCP tools
RUN mkdir -p /app/workspace

# Set PYTHONPATH to include /app so backend package can be imported
ENV PYTHONPATH=/app

# Expose port (Koyeb will set PORT environment variable)
EXPOSE 8000

# Health check (using curl or wget)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
# Koyeb sets PORT environment variable, default to 8000
CMD ["sh", "-c", "uvicorn backend.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

