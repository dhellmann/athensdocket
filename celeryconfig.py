BROKER_URL = 'amqp://docket:docket@localhost:5672/dockethost'

CELERY_RESULT_BACKEND = 'amqp'

CELERY_IMPORTS = ('docket.tasks',)
