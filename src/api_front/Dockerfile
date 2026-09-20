FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    addgroup --system appuser && adduser --system --ingroup appuser --home /app appuser

COPY --chown=root:root main.py start.sh ./
RUN chmod 0444 main.py && chmod 0555 start.sh

USER appuser

EXPOSE 8001

CMD ["./start.sh"]
