import os

# DEFAULT_ZSERVER_PORT is not defined until plone.testing == 4.0.8
DEFAULT_ZSERVER_PORT = 55001

# plone.testing checks environment to allow overriding DEFAULT_ZSERVER_PORT
ZSERVER_PORT = os.environ.get('ZSERVER_PORT', DEFAULT_ZSERVER_PORT)

# Allow specifying HOST and PORT through environment variables for instance,
# if tests should go through a proxy
ZOPE_HOST = os.environ.get('ZOPE_HOST', 'localhost')
ZOPE_PORT = os.environ.get('ZOPE_PORT', ZSERVER_PORT)
