FROM python:3.10 as python

ENV PYTHONUNBUFFERED 1

FROM python as dependencies

RUN pip install poetry
COPY poetry.lock pyproject.toml ./

RUN poetry export --format requirements.txt --output requirements.txt --without-hashes


FROM python as app

WORKDIR /btecify-server
LABEL application=btecify
EXPOSE 8000
COPY --from=dependencies /requirements.txt ./
RUN pip install -r requirements.txt

COPY ./ ./

CMD ["bash", "start-app.sh"]
