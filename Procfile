web: gunicorn config.wsgi --log-file -
worker: celery -A config worker -l info --concurrency=1 --max-tasks-per-child=50
release: python manage.py migrate
