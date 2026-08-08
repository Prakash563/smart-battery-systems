"""
ASGI config for Battery_Performance_in_Electric_vechiles project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Battery_Performance_in_Electric_vechiles.settings')

application = get_asgi_application()
