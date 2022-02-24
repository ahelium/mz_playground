FROM python:3.8-slim

COPY requirements.txt .

RUN set -ex; \
  	pip install --no-cache-dir -r requirements.txt

ADD events.py .

CMD ["python", "-u", "./events.py"]
