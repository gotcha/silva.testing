# Layers setting up fixtures with a Silva site. Also importable from
# plone.app.testing directly

from plone.testing import Layer
from plone.testing import zodb, zca, z2

from silva.testing.interfaces import (
    SILVA_SITE_ID,
    SILVA_SITE_TITLE,

    # TEST_USER_ID,
    # TEST_USER_NAME,
    # TEST_USER_PASSWORD,
    # TEST_USER_ROLES,

    SITE_OWNER_NAME,
    SITE_OWNER_PASSWORD
)


class SilvaFixture(Layer):
    """This layer sets up a basic Silva site, with:

    * No content
    * No default workflow
    * One user, as found in the constant ``TEST_USER_ID``, with login name
      ``TEST_USER_NAME``, the password ``TEST_USER_PASSWORD``, and a single
      role, ``Member``.
    """

    defaultBases = (z2.STARTUP,)

    # Products that will be installed, plus options
    products = (
        ('Products.PythonScripts', {'loadZCML': False},),
        ('Products.PageTemplates', {'loadZCML': False},),
        ('Products.ProxyIndex', {'loadZCML': False},),
        ('Products.ZCatalog', {'loadZCML': False},),
        ('Products.ZCTextIndex', {'loadZCML': False}, ),
        ('Products.Formulator', {'loadZCML': True}, ),

        ('Products.SilvaMetadata', {'loadZCML': True}, ),
        ('Products.SilvaViews', {'loadZCML': False}, ),
        ('Products.XMLWidgets', {'loadZCML': False}, ),
        ('Products.Silva', {'loadZCML': True}, ),

    )

    # Layer lifecycle

    def setUp(self):

        # Stack a new DemoStorage on top of the one from z2.STARTUP.
        self['zodbDB'] = zodb.stackDemoStorage(
            self.get('zodbDB'), name='SilvaFixture'
        )

        self.setUpZCML()

        from zope.app.component.hooks import setHooks
        setHooks()

        # Set up products and the default content
        for app in z2.zopeApp():
            self.setUpProducts(app)
            self.setUpDefaultContent(app)

    def tearDown(self):

        # Tear down products
        for app in z2.zopeApp():
            # note: content tear-down happens by squashing the ZODB
            self.tearDownProducts(app)

        from zope.app.component.hooks import resetHooks
        resetHooks()

        self.tearDownZCML()

        # Zap the stacked ZODB
        self['zodbDB'].close()
        del self['zodbDB']

    def setUpZCML(self):
        """Stack a new global registry and load ZCML configuration of Silva
        and the core set of add-on products into it. Also set the
        ``disable-autoinclude`` ZCML feature so that Silva does not attempt to
        auto-load ZCML using ``z3c.autoinclude``.
        """

        # Create a new global registry
        zca.pushGlobalRegistry()

        from zope.configuration import xmlconfig
        self['configurationContext'] = context = zca.stackConfigurationContext(
            self.get('configurationContext')
        )

        # Load dependent products's ZCML - Silva doesn't specify dependencies
        # on Products.* packages fully

        from zope.dottedname.resolve import resolve

        def loadAll(filename):
            for p, config in self.products:
                if not config['loadZCML']:
                    continue
                try:
                    package = resolve(p)
                except ImportError:
                    continue
                try:
                    xmlconfig.file(filename, package, context=context)
                except IOError:
                    pass

        loadAll('meta.zcml')
        loadAll('configure.zcml')
        loadAll('overrides.zcml')

    def tearDownZCML(self):
        """Pop the global component registry stack, effectively unregistering
        all global components registered during layer setup.
        """
        # Pop the global registry
        zca.popGlobalRegistry()

        # Zap the stacked configuration context
        del self['configurationContext']

    def setUpProducts(self, app):
        """Install all old-style products listed in the the ``products`` tuple
        of this class.
        """

        for p, config in self.products:
            z2.installProduct(app, p)

    def tearDownProducts(self, app):
        """Uninstall all old-style products listed in the the ``products``
        tuple of this class.
        """
        for p, config in reversed(self.products):
            z2.uninstallProduct(app, p)

    def setUpDefaultContent(self, app):

        """Add the site owner user to the root user folder and log in as that
        user. Create the Silva site.
        Note: There is no explicit tear-down of this setup operation, because
        all persistent changes are torn down when the stacked ZODB
        ``DemoStorage`` is popped.
        """

        # Create the owner user and "log in" so that the site object gets
        # the right ownership information
        app['acl_users'].userFolderAddUser(
            SITE_OWNER_NAME,
            SITE_OWNER_PASSWORD,
            ['Manager'],
            []
        )

        z2.login(app['acl_users'], SITE_OWNER_NAME)

        from Products.Silva.Root import manage_addRoot

        manage_addRoot(
            app, SILVA_SITE_ID,
            title=SILVA_SITE_TITLE,
        )

        # Log out again
        z2.logout()

# Silva fixture layer instance. Should not be used on its own, but as a base
# for other layers.

SILVA_FIXTURE = SilvaFixture()


class SilvaTestLifecycle(object):
    """Mixin class for Silva test lifecycle. This exposes the ``silvaroot``
    resource and resets the environment between each test.

    This class is used as a mixing for the IntegrationTesting and
    FunctionalTesting classes below, which also mix in the z2 versions of
    the same.
    """

    defaultBases = (SILVA_FIXTURE,)

    def testSetUp(self):
        super(SilvaTestLifecycle, self).testSetUp()

        self['silvaroot'] = silvaroot = self['app'][SILVA_SITE_ID]
        self.setUpEnvironment(silvaroot)

    def testTearDown(self):
        self.tearDownEnvironment(self['silvaroot'])
        del self['silvaroot']

        super(SilvaTestLifecycle, self).testTearDown()

    def setUpEnvironment(self, silvaroot):
        """Set up the local component site, reset skin data and log in as
        the test user.
        """

        # Pseudo-login as the test user
        from silva.testing import helpers
        helpers.login(silvaroot, SITE_OWNER_NAME)

    def tearDownEnvironment(self, silvaroot):
        """Log out, invalidate standard RAM caches, and unset the local
        component site to clean up after tests.
        """

        # Clear the security manager
        from silva.testing import helpers
        helpers.logout()


class IntegrationTesting(SilvaTestLifecycle, z2.IntegrationTesting):
    """Silva version of the integration testing layer
    """


class FunctionalTesting(SilvaTestLifecycle, z2.FunctionalTesting):
    """Silva version of the functional testing layer
    """

#
# Layer instances
#

# Note: SILVA_FIXTURE is defined above

SILVA_INTEGRATION_TESTING = IntegrationTesting(
    bases=(SILVA_FIXTURE,), name='Silva:Integration'
)
SILVA_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(SILVA_FIXTURE,), name='Silva:Functional'
)

SILVA_ZSERVER = FunctionalTesting(
    bases=(SILVA_FIXTURE, z2.ZSERVER_FIXTURE), name='Silva:ZServer'
)
SILVA_FTP_SERVER = FunctionalTesting(
    bases=(SILVA_FIXTURE, z2.FTP_SERVER_FIXTURE), name='Silva:FTPServer'
)


from plone.robotframework.layers import REMOTE_LIBRARY_FIXTURE


SILVA_ROBOT_TESTING = FunctionalTesting(
    bases=(SILVA_FIXTURE, REMOTE_LIBRARY_FIXTURE, z2.ZSERVER_FIXTURE),
    name="Plone:Robot"
)
