FROM python:3.10

WORKDIR /app
COPY ./app /app
COPY requirements.txt .
RUN pip install --default-timeout=100 -r requirements.txt


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

