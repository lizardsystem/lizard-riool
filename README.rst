lizard-riool
==========================================

This App also uses Celery, and needs some Celery-specific configuration:

Add 'djcelery' and 'kombu.transport.django' to INSTALLED_APPS.

In settings.py, add:

    import djcelery
    djcelery.setup_loader()

    BROKER_URL = 'django://'

Then run bin/django syncdb, bin/django migrate.

(this assumes you want to use Django's database as Celery message
broker. If you use something else, like RabbitMQ, kombu isn't needed
and you need different settings).
