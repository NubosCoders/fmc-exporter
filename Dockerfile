FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

COPY collector/* ./collector/

USER root

RUN apk add --no-cache ca-certificates

COPY certs/fmc-ca.crt /usr/local/share/ca-certificates/

RUN update-ca-certificates

CMD ["python", "-u", "app.py"]