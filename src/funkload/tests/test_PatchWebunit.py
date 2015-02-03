#! /usr/bin/env python

import unittest
import httplib
from cStringIO import StringIO
from funkload.PatchWebunit import decodeCookies, FixedCookie

EXAMPLE_DOMAIN = "www.example.com"


class TestPatchWebUnit(unittest.TestCase):
    """
    Testing the patched-in methods from PatchUnitTest, to the extent that
    they are amenable to unit testing without a lot of infrastructure.
    """
    def test_FixedCookie_applies(self):
        self.assertTrue(FixedCookie.applies(python_version=0x020704F0),
            msg="FixedCookie should apply to 2.7.4")
        self.assertTrue(FixedCookie.applies(python_version=0x020607F0),
            msg="FixedCookie should apply to 2.6.7")
        self.assertFalse(FixedCookie.applies(python_version=0x020705F0),
            msg="FixedCookie should not apply to 2.7.5")
        self.assertFalse(FixedCookie.applies(python_version=0x020801F0),
            msg="FixedCookie should not apply to 2.8.1")

    def test_decodeCookies_sessionCookie_parsedOK(self):
        cookieName = "CookieSupportChecker.probe"
        messageHeaders = self.createCookieHeader(
            "CookieSupportChecker.probe=dummyValue; Secure; HttpOnly")
        cookies = {}
        decodeCookies("/", EXAMPLE_DOMAIN, messageHeaders, cookies)

        self.assertTrue("/" in cookies[EXAMPLE_DOMAIN])
        self.assertTrue(cookieName in cookies[EXAMPLE_DOMAIN]["/"])
        parsedCookie = cookies[EXAMPLE_DOMAIN]["/"][cookieName]
        self.assertEquals("dummyValue", parsedCookie.value)

        messageHeaders = self.createCookieHeader("CookieSupportChecker.probe=newValue")
        decodeCookies("/", EXAMPLE_DOMAIN, messageHeaders, cookies)

        self.assertTrue("/" in cookies[EXAMPLE_DOMAIN])
        self.assertTrue(cookieName in cookies[EXAMPLE_DOMAIN]["/"])
        parsedCookie = cookies[EXAMPLE_DOMAIN]["/"][cookieName]
        self.assertEquals("newValue", parsedCookie.value)

    def createCookieHeader(self, *cookie_headers):
        # well, that's dumb:
        messageHeaders = httplib.HTTPMessage(StringIO(""))
        for cookie in cookie_headers:
            messageHeaders['set-cookie'] = cookie
        return messageHeaders


if __name__ == '__main__':
    unittest.main()
