FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py renderer.py validators.py ./

# Run as non-root; /app/output must be writable for rendered files.
# USER must be numeric: Kubernetes runAsNonRoot cannot verify a named
# user and rejects the container with CreateContainerConfigError.
RUN useradd --uid 10001 --no-create-home appuser \
    && mkdir -p /app/output \
    && chown appuser /app/output
USER 10001

ENV OUTPUT_DIR=/app/output
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:create_app()"]