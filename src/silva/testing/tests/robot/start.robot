*** Settings ***
Resource  silva/testing/selenium.robot

Library  Remote  ${ZOPE_URL}/REMOTE_LIBRARY_FIXTURE

Suite Setup  Suite Setup
Suite Teardown  Close all browsers

*** Test cases ***

Silva edit
    Go to  ${SILVA_URL}/first-folder
    Page should not contain  First folder
    Go to  ${SILVA_URL}/edit
    Select from list  id=meta_type  Silva Folder
    Input text  id=object_id  first-folder
    Input text  id=object_title  First folder
    Click button  name=add_submit
    Go to  ${SILVA_URL}/first-folder
    Page should contain  First folder
#    Debug

Silva
    Go to  ${SILVA_URL}
    Click link  Silva site
    Go to  ${SILVA_URL}/first-folder
#    Reload Page
    Page should not contain  First folder

*** Keywords ***
Suite Setup
    Open test browser
    Enable autologin as  Manager

Debug
    [Documentation]  Pause test execution with interactive debugger (REPL)
    ...              in the current shell.
    ...
    ...              This keyword is based on ``roboframework-debuglibrary``
    ...              and requires that the used Python is compiled with
    ...              ``readline``-support.
    Import library  DebugLibrary  WITH NAME  DebugLibrary
    DebugLibrary.Debug
