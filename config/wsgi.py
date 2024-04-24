"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv
import os

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.getenv('DJANGO_SETTINGS_MODULE'))

application = get_wsgi_application()
