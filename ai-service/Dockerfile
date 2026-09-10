FROM python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534
WORKDIR /app
ARG MODEL_REVISION=c9745ed1d9f207416be6d2e6f8de32d1f16199bf
COPY ai-service/requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', revision='${MODEL_REVISION}').save('/models/all-MiniLM-L6-v2')"
COPY ai-service /app
COPY teammate-ai /teammate-ai
ENV MODEL_PATH=/models/all-MiniLM-L6-v2 TEAMMATE_AI_SRC=/teammate-ai/src MODEL_VERSION=${MODEL_REVISION}
RUN python /teammate-ai/tests/eval_against_ground_truth.py --output /app/evaluation/latest.json
ENV EVALUATION_REPORT_PATH=/app/evaluation/latest.json
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
