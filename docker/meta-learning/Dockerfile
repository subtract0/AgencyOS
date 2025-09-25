# MetaLearning Experiment Runner Container
# Secure, isolated container for running agent experiments

FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r experiment && useradd -r -g experiment experiment

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-meta.txt /tmp/requirements-meta.txt
RUN pip install --no-cache-dir -r /tmp/requirements-meta.txt

# Create data directory with proper permissions
RUN mkdir -p /workspace/data && \
    mkdir -p /workspace/logs && \
    chown -R experiment:experiment /workspace

# Set security options
USER experiment

# Default command (can be overridden)
CMD ["python", "-c", "print('MetaLearning Experiment Container Ready')"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; print('Container healthy'); sys.exit(0)"

# Labels for identification
LABEL maintainer="Agency MetaLearning System"
LABEL version="1.0.0"
LABEL description="Secure experiment execution environment"