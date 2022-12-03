FROM python:3.10-slim

RUN apt-get update && apt-get install -y git

WORKDIR /opt/app

COPY ./pyproject.toml ./poetry.lock ./

RUN pip install poetry

RUN poetry config virtualenvs.create false && poetry install

COPY . .

CMD ["poetry", "run", "celery", "-A", "app.tasks", "worker", "-B"]
