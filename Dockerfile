ARG WORKDIR=.

FROM python:3.11-alpine AS builder

ARG WORKDIR

ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    STAGE=prod

ADD pyproject.toml poetry.lock ${WORKDIR}/

RUN apk add build-base libffi-dev

RUN pip install poetry
RUN poetry config virtualenvs.in-project true

WORKDIR ${WORKDIR}
COPY . .

RUN poetry install

FROM python:3.11-alpine as runtime

ARG WORKDIR
WORKDIR ${WORKDIR}

COPY --from=builder ${WORKDIR} .
ADD . .

ENTRYPOINT ["poetry", "run", "python", "-m", "src.run"]
