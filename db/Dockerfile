FROM postgres:10

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    iputils-ping && \
    mkdir buzz && \
    rm -rf /var/lib/apt/lists/*

ENV POSTGRES_PASSWORD="notwaterloo"
ENV POSTGRES_USER="root"
ENV POSTGRES_DB="buzzdb"

COPY . buzz

WORKDIR buzz

EXPOSE 5432
