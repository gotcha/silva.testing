*** Settings ***
Resource  silva/testing/selenium.robot

Library  Remote  ${ZOPE_URL}/RobotRemote

Suite Setup  Suite Setup
Suite Teardown  Close all browsers

*** Test cases ***

Silva
    Click link  Silva site

*** Keywords ***
