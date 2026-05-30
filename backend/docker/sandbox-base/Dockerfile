# AI-Edu Code Sandbox Base Image
# Secure Python execution environment

FROM python:3.9-slim

LABEL maintainer="AI-Edu Team"
LABEL description="Secure code execution sandbox for AI-Edu platform"
LABEL version="1.0.0"

# Create non-root user and group
RUN groupadd -r sandbox && useradd -r -g sandbox sandbox

# Install minimal system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /sandbox

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/sandbox/.local/bin:$PATH"

# Create temporary directories
RUN mkdir -p /sandbox/tmp && chmod 777 /sandbox/tmp

# Security: Set proper permissions
RUN chown -R sandbox:sandbox /sandbox

# Switch to non-root user
USER sandbox

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "print('OK')" || exit 1

# Default command
CMD ["python", "-c", "import sys; print(f'Python {sys.version}')"]
