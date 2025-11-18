# Secure Docker container for Treasure Hunt Agent
# Uses non-root user and minimal permissions

FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create non-root user for running the agent
RUN groupadd -r agentuser && useradd -r -g agentuser -u 1000 agentuser

# Set up working directory
WORKDIR /app

# Copy dependency files first (for better caching)
COPY --chown=agentuser:agentuser pyproject.toml uv.lock ./

# Install dependencies as root (for system-level packages)
RUN uv sync --frozen

# Copy application code
COPY --chown=agentuser:agentuser . .

# Create directories for treasure hunts with proper permissions
RUN mkdir -p /app/treasure_hunt && \
    chown -R agentuser:agentuser /app/treasure_hunt

# Switch to non-root user
USER agentuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command (can be overridden)
CMD ["/bin/bash"]
