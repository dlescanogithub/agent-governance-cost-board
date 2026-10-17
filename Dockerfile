FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY inventory ./inventory
COPY prompts ./prompts
COPY traces/generation.yaml ./traces/generation.yaml
COPY evals ./evals

RUN pip install --no-cache-dir .

USER nobody

ENTRYPOINT ["python", "-m", "governance_board"]
CMD ["--help"]
