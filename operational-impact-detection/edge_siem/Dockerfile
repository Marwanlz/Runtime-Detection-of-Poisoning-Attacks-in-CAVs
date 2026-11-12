FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY edge_siem /app
COPY shared /app/shared

EXPOSE 5000

CMD ["python", "app.py"]