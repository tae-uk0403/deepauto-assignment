FROM python:3.10-slim

RUN pip install --no-cache-dir kubernetes

WORKDIR /app

COPY hello_kube.py /app/hello_kube.py

ENTRYPOINT ["python", "/app/hello_kube.py"]
