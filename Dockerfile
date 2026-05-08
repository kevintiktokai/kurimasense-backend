FROM python:3.11-slim

WORKDIR /app

# Install cron alongside the app so the daily ingestion worker can run on
# schedule when the container is the only host. App-server-only deployments
# (Render etc.) ignore the cron daemon and just exec the CMD below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends cron tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install the daily ingestion crontab. Cron picks up files in /etc/cron.d
# automatically; the file must be 0644 and must end with a newline (already
# enforced in the source).
COPY deployment/cron/daily_ingestion.cron /etc/cron.d/kurima_daily_ingestion
RUN chmod 0644 /etc/cron.d/kurima_daily_ingestion \
    && touch /var/log/kurima_ingestion.log

EXPOSE 8000

# tini reaps zombies for the cron + uvicorn pair when both run in-container.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
