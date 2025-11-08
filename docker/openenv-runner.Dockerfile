FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace \
    AGENCY_ENV_SPEC=/workspace/envs/agency_env_spec.json

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install pytest-json-report

COPY . /workspace

ENTRYPOINT ["python", "scripts/run_in_env.py"]
CMD ["--", "pytest", "tests/orchestrator", "-q"]
