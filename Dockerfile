FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN DJANGO_SECRET_KEY=build-only-placeholder python manage.py collectstatic --noinput && mkdir -p /data && chown -R 1001:0 /app /data && chmod -R g+rwX /app /data
USER 1001
EXPOSE 8000
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
CMD ["gunicorn", "django_concert.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4"]
