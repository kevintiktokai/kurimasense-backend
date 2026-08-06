FROM python:3.11-slim

# Flush prints/logs immediately — buffered stdout made the Railway deploy
# failures look like silent hangs (no output for the whole boot window).
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# WeasyPrint renders text through Pango, which is a system library rather than a
# wheel. Without these, `import weasyprint` raises at runtime — and because the
# import is lazy (services/documents/render.py), it would raise on the first
# request for a document rather than at boot, i.e. in front of whoever was
# generating an evidence pack. The brand faces ship in the repo, so no font
# packages are needed here.
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

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
