FROM python:3.14-slim

WORKDIR /app

COPY migration/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

CMD ["alembic"]