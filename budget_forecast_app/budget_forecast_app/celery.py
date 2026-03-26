import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_forecast_app.settings')

# Create the Celery app instance
app = Celery('budget_forecast_app')
app.conf.timezone = 'Asia/Kolkata'

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix in settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps (this will find your tasks.py)
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    'clean-old-uploads-every-midnight': {
        'task': 'forecast.tasks.delete_old_files_task',
        'schedule': crontab(minute=0, hour=0), # Runs at midnight
        'args': (24,) # Deletes files older than 24 hours
    },
}
