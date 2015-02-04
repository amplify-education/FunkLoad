#! /usr/bin/env python

import time
import unittest
import httplib
from cStringIO import StringIO
from funkload.PatchWebunit import decodeCookies, FixedCookie

EXAMPLE_DOMAIN = "www.example.com"

# Example dates for further parsing adventures, if desired:
# rfc822 = "Sun, 06 Nov 1994 08:49:37 GMT"  # RFC 822, updated by RFC 1123
# rfc850 = "Sunday, 06-Nov-94 08:49:37 GMT"  # RFC 850, obsoleted by RFC 1036
# ansiC = "Sun Nov  6 08:49:37 1994"  # ANSI C's asctime() format
# rfc822epoch = "Thu, 01 Jan 1970 00:00:00 GMT"

FORMAT_RFC1123 = "%a, %d %b %Y %H:%M:%S GMT"
FORMAT_NETSCAPE = "%a, %d-%b-%y %H:%M:%S GMT"

past_time = time.gmtime(time.time() - 86400)    # yesterday
future_time = time.gmtime(time.time() + 86400)  # tomorrow


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

    def test_decodeCookies_unexpiredCookies_cookiesFound(self):
        cookieName = "my.cookie.name"
        cookie_template = cookieName + '=;Path=/;Expires=%s'
        for time_format in [FORMAT_RFC1123, FORMAT_NETSCAPE]:
            cookies = {}
            example_date = time.strftime(time_format, future_time)
            messageHeaders = self.createCookieHeader(cookie_template % example_date)
            decodeCookies("/", EXAMPLE_DOMAIN, messageHeaders, cookies)
            self.assertTrue("/" in cookies[EXAMPLE_DOMAIN], msg="Cookie store is sane")
            self.assertTrue(cookieName in cookies[EXAMPLE_DOMAIN]["/"],
                            msg="cookie stored correctly by name")
            self.assertEquals("", cookies[EXAMPLE_DOMAIN]["/"][cookieName].value)

    def test_decodeCookies_expiredCookies_cookiesNotFound(self):
        cookieName = "my.cookie.name"
        cookie_template = cookieName + '=;Path=/;Expires=%s'
        for time_format in [FORMAT_RFC1123, FORMAT_NETSCAPE]:
            cookies = {}
            example_date = time.strftime(time_format, past_time)
            messageHeaders = self.createCookieHeader(cookie_template % example_date)
            decodeCookies("/", EXAMPLE_DOMAIN, messageHeaders, cookies)
            self.assertTrue("/" in cookies[EXAMPLE_DOMAIN], msg="Cookie store is sane")
            self.assertFalse(cookieName in cookies[EXAMPLE_DOMAIN]["/"],
                            msg="cookie deleted correctly by name")

    def test_decodeCookies_deletedCookies_cookiesNotFound(self):
        cookieName = "my.cookie.name"
        cookie_template = cookieName + '=;Path=/;Expires=%s'
        for time_format in [FORMAT_RFC1123, FORMAT_NETSCAPE]:
            cookies = {}

            future_expiry = time.strftime(time_format, future_time)
            past_expiry = time.strftime(time_format, past_time)

            messageHeaders = self.createCookieHeader(cookie_template % future_expiry)
            decodeCookies("/", EXAMPLE_DOMAIN, messageHeaders, cookies)
            self.assertTrue("/" in cookies[EXAMPLE_DOMAIN], msg="Cookie store is sane")
            self.assertTrue(cookieName in cookies[EXAMPLE_DOMAIN]["/"],
                            msg="cookie deleted correctly by name")
            messageHeaders = self.createCookieHeader(cookie_template % past_expiry)
            decodeCookies("/", EXAMPLE_DOMAIN, messageHeaders, cookies)
            self.assertTrue("/" in cookies[EXAMPLE_DOMAIN], msg="Cookie store is sane")
            self.assertFalse(cookieName in cookies[EXAMPLE_DOMAIN]["/"],
                            msg="cookie deleted correctly by name")

    def createCookieHeader(self, *cookie_headers):
        # well, that's dumb:
        messageHeaders = httplib.HTTPMessage(StringIO(""))
        for cookie in cookie_headers:
            messageHeaders['set-cookie'] = cookie
        return messageHeaders


if __name__ == '__main__':
    unittest.main()
