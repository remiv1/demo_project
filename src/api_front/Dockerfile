FROM node:24-alpine AS assets

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY static/scss ./static/scss
RUN mkdir -p static/css static/js && npm run build

FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    addgroup --system appuser && adduser --system --ingroup appuser --home /app appuser

COPY --chown=root:root main.py start.sh ./
COPY --chown=root:root blueprints ./blueprints
COPY --chown=root:root templates ./templates
COPY --chown=root:root static/js/events.js ./static/js/events.js
COPY --from=assets --chown=root:root /app/static/css ./static/css
COPY --from=assets --chown=root:root /app/static/js/htmx.min.js ./static/js/htmx.min.js
RUN chmod 0444 main.py && chmod 0555 start.sh

USER appuser

EXPOSE 8001

CMD ["./start.sh"]
