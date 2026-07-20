FROM python:3.11-slim

# Flush prints/logs immediately — buffered stdout made the Railway deploy
# failures look like silent hangs (no output for the whole boot window).
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# EXPOSE is documentation only. The platform (Railway/Render) injects $PORT and
# the app must bind to it; ${PORT:-8000} keeps local `docker run` working too.
# Host `::` binds dual-stack (IPv6 + IPv4-mapped): Railway's health prober and
# private network connect over IPv6, so an 0.0.0.0 (IPv4-only) bind is
# unreachable to them — the app runs but every probe gets connection refused.
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:app --host :: --port ${PORT:-8000}"]
