FROM python:3.12-slim

WORKDIR /app

COPY services/alert-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY services/common ./common
COPY services/alert-service/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
