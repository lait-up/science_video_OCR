FROM python:3.11-slim


WORKDIR /app


COPY . /app


RUN chmod +x /app/scripts/*.sh


ENTRYPOINT ["./scripts/entrypoint.sh"]