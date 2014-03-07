import unittest

from silva.testing.layers import SILVA_INTEGRATION_TESTING


class FixtureTestCase(unittest.TestCase):

    layer = SILVA_INTEGRATION_TESTING

    def test_silva(self):
        from Products.Silva.Root import Root
        silva = self.layer['silvaroot']
        self.assertTrue(isinstance(silva, Root))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FixtureTestCase))
    return suite
