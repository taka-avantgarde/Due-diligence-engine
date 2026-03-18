FROM python:3.11-slim

WORKDIR /app

# Install git for repo cloning
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY templates/ templates/

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["uvicorn", "src.saas.app:app", "--host", "0.0.0.0", "--port", "8080"]
