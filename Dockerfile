FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir '.[dashboard]'
ENV PYTHONUNBUFFERED=1
CMD ["mobility-etl"]
