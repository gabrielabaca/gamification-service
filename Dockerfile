FROM python:3.11-slim

ARG PORT=9004

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY envs/.env.main /app/.env

RUN if [ ! -f /app/.env ]; then echo "ERROR: .env file not found!" && exit 1; fi && \
    echo ".env copied successfully" && \
    echo ".env has $(wc -l < /app/.env) lines"

EXPOSE ${PORT}
ENV PORT=${PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
