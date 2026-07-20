FROM python:3.11-slim

# Flush prints/logs immediately — buffered stdout made the Railway deploy
# failures look like silent hangs (no output for the whole boot window).
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# EXPOSE is documentation only. The platform (Railway/Render) injects $PORT
# and main.py binds to it (default 8000 for local `docker run`). main.py also
# picks the bind host at runtime — dual-stack `::` where IPv6 exists (Railway's
# health prober connects over IPv6; an 0.0.0.0 bind is unreachable to it),
# falling back to 0.0.0.0 in IPv4-only environments where a hard-coded `::`
# crashes at boot. Neither family can be hard-coded portably.
EXPOSE 8000

CMD ["python", "main.py"]
