# Helper functions for Silva testing. Also importable from plone.app.testing
# directly

#import contextlib

from zope.configuration import xmlconfig

from plone.testing import z2, zodb, zca, security, Layer

from silva.testing import layers
from silva.testing.interfaces import (
    SILVA_SITE_ID,
    SITE_OWNER_NAME,
    # TEST_USER_NAME,
)

# User management


def login(silvaroot, userName):
    """Log in as the given user in the given Silva site
    """

    z2.login(silvaroot.acl_users, userName)


def logout():
    """Log out, i.e. become anonymous
    """

    z2.logout()


def setRoles(silvaroot, userId, roles):
    """Set the given user's roles to a tuple of roles.
    """

    userFolder = silvaroot.acl_users
    z2.setRoles(userFolder, userId, roles)


# Component architecture
def pushGlobalRegistry(silvaroot, new=None, name=None):
    """Set a new global component registry that uses the current registry as
    a base. If you use this, you *must* call ``popGlobalRegistry()`` to
    restore the original state.

    If ``new`` is not given, a new registry is created. If given, you must
    provide a ``zope.component.globalregistry.BaseGlobalComponents`` object.

    Returns the new registry.

    Also ensure that the persistent component registry at ``silvaroot`` has the
    new global registry as its base.
    """
    from zope.app.component.hooks import setSite, getSite, setHooks
    site = getSite()

    current = zca.pushGlobalRegistry(new=new)

    if site is not None:
        setHooks()
        setSite(site)

    return current


def popGlobalRegistry(silvaroot):
    """Restore the global component registry form the top of the stack, as
    set with ``pushGlobalRegistry()``.

    Also ensure that the persistent component registry at ``silvaroot`` has the
    new global registry as its base.
    """

    from zope.app.component.hooks import setSite, getSite, setHooks
    site = getSite()

    # Now pop the registry. We need to do it in this somewhat convoluted way
    # to avoid the risk of unpickling errors

    previous = zca.popGlobalRegistry()

    if site is not None:
        setHooks()
        setSite(site)

    return previous


def silvaRoot(db=None, connection=None, environ=None):
    """Context manager for working with the Silva root during layer setup::

        with silvaRoot() as silvaroot:
            ...

    This is based on the ``z2.zopeApp()`` context manager. See the module
     ``plone.testing.z2`` for details.

    Do not use this in a test.
    Use the 'silvaroot' resource from the SilvaFixture layer instead!

    Pass a ZODB handle as ``db`` to use a specificdatabase. Alternatively,
    pass an open connection as ``connection`` (the connection will not be
    closed).
    """

    from zope.app.component.hooks import setHooks
    setHooks()

    for app in z2.zopeApp(db, connection, environ):
        silvaroot = app[SILVA_SITE_ID]

        login(silvaroot, SITE_OWNER_NAME)

        try:
            yield silvaroot
        # the finally is replaced by the pair except else
        # 2.4 does not accept yield in a try...finally
        except:
            logout()
        else:
            logout()

# Layer base class


class SilvaSandboxLayer(Layer):
    """Layer base class managing the common pattern of having a stacked ZODB
    ``DemoStorage`` and a stacked global component registry for the layer.

    Base classes must override and implemented ``setUpSilvaSite()``. They
    may also implement ``tearDownSilvaSite()``, and can optionally change
    the ``defaultBases`` tuple.
    """

    # The default list of bases.

    defaultBases = (layers.SILVA_FIXTURE, )

    # Hooks

    def setUpZope(self, app, configurationContext):
        """Set up Zope.

        ``app`` is the Zope application root.

        ``configurationContext`` is the ZCML configuration context.

        This is the most appropriate place to load ZCML or install Zope 2-
        style products, using the ``plone.testing.z2.installProduct`` helper.
        """
        pass

    def tearDownZope(self, app):
        """Tear down Zope.

        ``app`` is the Zope application root.

        This is the most appropriate place to uninstall Zope 2-style products
        using the ``plone.testing.z2.uninstallProduct`` helper.
        """
        pass

    def setUpSilvaSite(self, silvaroot):
        """Set up the Silva site.

        ``silvaroot`` is the Silva site.
        Provided no exception is raised, changes
        to this site will be committed (into a newly stacked ``DemoStorage``).

        Concrete layer classes should implement this method at a minimum.
        """
        pass

    def tearDownSilvaSite(self, silvaroot):
        """Tear down the Silva site.

        Implementing this is optional. If the changes made during the
        ``setUpSilvaSite()`` method were confined to the ZODB and the global
        component regsitry, those changes will be torn down automatically.
        """

        pass

    # Boilerplate

    def setUp(self):

        # Push a new database storage so that database changes
        # commited during layer setup can be easily torn down
        self['zodbDB'] = zodb.stackDemoStorage(
            self.get('zodbDB'), name=self.__name__
        )

        # Push a new configuration context so that it's possible to re-import
        # ZCML files after tear-down
        if self.__name__ is not None:
            name = self.__name__
        else:
            name = 'not-named'
        contextName = "SilvaSandboxLayer-%s" % name
        self['configurationContext'] = configurationContext = (
            zca.stackConfigurationContext(
                self.get('configurationContext'),
                name=contextName
            )
        )

        for silvaroot in silvaRoot():
            from zope.app.component.hooks import setHooks
            setHooks()

            # Push a new component registry so that ZCML registations
            # and other global component registry changes are sandboxed
            pushGlobalRegistry(silvaroot)

            # Make sure zope.security checkers can be set up and torn down
            # reliably

            security.pushCheckers()

            # Allow subclass to load ZCML and products
            self.setUpZope(silvaroot.getPhysicalRoot(), configurationContext)

            self.setUpSilvaSite(silvaroot)

    def tearDown(self):

        for app in z2.zopeApp():

            silvaroot = app[SILVA_SITE_ID]

            from zope.app.component.hooks import setHooks
            setHooks()

            # Allow subclass to tear down persistent fixture
            self.tearDownSilvaSite(silvaroot)

            # Make sure zope.security checkers can be set up and torn down
            # reliably

            security.popCheckers()

            # Pop the component registry, thus removing component
            # architecture registrations
            popGlobalRegistry(silvaroot)

            # Allow subclass to tear down products
            self.tearDownZope(app)

        # Zap the configuration context
        del self['configurationContext']

        # Pop the demo storage, thus restoring the database to the
        # previous state
        self['zodbDB'].close()
        del self['zodbDB']

    # Helpers
    def loadZCML(self, name='configure.zcml', **kw):
        kw.setdefault('context', self['configurationContext'])
        return xmlconfig.file(name, **kw)
