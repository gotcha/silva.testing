*** Settings ***

Documentation  This file should be required only using
...            ``Resource  plone/app/robotframework/variables.robot``.
...
...            The fancy import order is required for backwards
...            compatibility with robotframework 2.7.7.

*** Variables ***

${ZOPE_URL}  http://${ZOPE_HOST}:${ZOPE_PORT}

${SILVA_SITE_ID}  silva
${SILVA_URL}  ${ZOPE_URL}/${SILVA_SITE_ID}

${START_URL}  ${SILVA_URL}
