FROM python:3.12-alpine3.19

# Metadata
LABEL maintainer="DCC FCFM Universidad de Chile"
LABEL description="Repositorio Académicos - Development"

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY ./requirements.txt .

# install dependencies
RUN \
    apk add --no-cache postgresql-libs netcat-openbsd && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    apk add --no-cache g++ libxml2-dev libxslt-dev libffi-dev openssl-dev make && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt --no-cache-dir && \
    apk --purge del .build-deps

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh && \
    chmod +x /usr/src/app/entrypoint.sh

# copy project
COPY . .

# create necessary directories
RUN mkdir -p /usr/src/app/staticfiles_collected && \
    mkdir -p /usr/src/app/uploads

# expose port
EXPOSE 8000

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

# default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]