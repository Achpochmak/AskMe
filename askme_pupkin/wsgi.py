"""
WSGI config for askme_pupkin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'askme_pupkin.settings')

application = get_wsgi_application()


def app(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)

    params = environ.get('QUERY_STRING', '')
    params_list = params.split('&')
    output = '\n'.join(params_list)

    return [output.encode()]
