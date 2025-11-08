FROM mcr.microsoft.com/devcontainers/python:3.12

# Install base tooling required by AgencyOS
default_packages="build-essential curl git libpq-dev"
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $default_packages \
    && rm -rf /var/lib/apt/lists/*

# Pre-install uv for faster Python dependency management (optional for local use)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV UV_NO_COLOR=1
ENV UV_PYTHON_DOWNLOADS=disable

# Create workspace directory to match VS Code expectations
RUN mkdir -p /workspace
WORKDIR /workspace
