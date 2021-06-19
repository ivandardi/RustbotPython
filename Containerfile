FROM python:3.9-slim-buster

WORKDIR /app

RUN python3 -m venv .venv \
 && . .venv/bin/activate

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "runner.py"]
