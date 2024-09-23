FROM python:3.10-bookworm

ARG VERSION

LABEL org.label-schema.version=$VERSION

WORKDIR /app

COPY . /app/

RUN pip install -r requirements.txt

CMD ["python", "-m", "src.engineering.github.collector", "collect-repository", "-o", "apache", "-r", "kafka"]

