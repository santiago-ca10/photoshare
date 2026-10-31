FROM python:3.12-slim
WORKDIR /app
COPY social/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
COPY social/main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
