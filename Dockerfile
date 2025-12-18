FROM python:3.12.7-bookworm AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /static /logs /media /backup

COPY app/ .

RUN pip install --upgrade pip
RUN pip install -r _requirements/base.txt

FROM base AS production

ARG UID
ARG GID

RUN pip install -r _requirements/production.txt

RUN groupadd -r instalar
RUN useradd -m instalar -u ${UID} -g ${GID} -s /sbin/nologin
RUN chown -R instalar:instalar /static /logs /media /backup /app
USER instalar

# Command to prepare and start the Django service with WSGI
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000"]

FROM base AS develop

ENV PYDEVD_DISABLE_FILE_VALIDATION=1

RUN apt-get update
RUN apt-get -y install --no-install-recommends graphviz graphviz-dev
RUN pip install -r _requirements/develop.txt