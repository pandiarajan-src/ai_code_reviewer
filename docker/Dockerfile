# Multi-stage Dockerfile for Code Reviewer (Frontend + Backend)

# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

# Copy package files
COPY src/ai_code_reviewer/api/frontend/package*.json ./

# Install dependencies (include dev dependencies for build)
RUN npm ci

# Copy frontend source
COPY src/ai_code_reviewer/api/frontend/ ./

# Build frontend (output to /app/frontend/dist)
RUN npm run build

# Stage 2: Prepare Python Backend
FROM python:3.12-slim AS backend-build
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src ./src
COPY pyproject.toml README.md ./

# Install the package
RUN pip install --no-cache-dir -e .

# Stage 3: Production Image
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (nginx, supervisor, curl for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx \
        supervisor \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment and backend code from backend-build stage
COPY --from=backend-build /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=backend-build /usr/local/bin /usr/local/bin
COPY --from=backend-build /app /app

# Copy frontend build from frontend-build stage
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/nginx.conf

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create non-root user and setup directories
RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /app/data /app/logs /var/log/supervisor && \
    chown -R app:app /app && \
    chown -R www-data:www-data /usr/share/nginx/html && \
    chown -R www-data:www-data /var/log/nginx && \
    chown -R www-data:www-data /var/lib/nginx

# Expose ports
ARG BACKEND_PORT=8000
ARG FRONTEND_PORT=3000
ENV BACKEND_PORT=${BACKEND_PORT}
ENV FRONTEND_PORT=${FRONTEND_PORT}
EXPOSE ${BACKEND_PORT} ${FRONTEND_PORT}

# Health check (check frontend nginx)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${FRONTEND_PORT} || exit 1

# Run supervisor to manage both nginx and uvicorn
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
