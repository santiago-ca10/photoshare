FROM python:3.12-slim
WORKDIR /app
COPY notifications/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY notifications/main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
