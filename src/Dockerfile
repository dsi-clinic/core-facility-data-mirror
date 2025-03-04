FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app
# Create a virtual environment with uv inside the container
RUN /usr/local/bin/uv venv

# We need to set this environment variable so that uv knows where
# the virtual environment is to install packages
ENV VIRTUAL_ENV=/app/.venv
ENV PYTHONUNBUFFERED=1
# Make sure that the virtual environment is in the PATH so
# we can use the binaries of packages that we install such as pip
# without needing to activate the virtual environment explicitly
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src

COPY pyproject.toml /app/

# TODO: determine if `uv venv` and `uv sync` are both needed, or is `sync` alone enough
RUN /usr/local/bin/uv venv
RUN /usr/local/bin/uv sync
