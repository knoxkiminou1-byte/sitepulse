import unittest
from unittest.mock import Mock, patch

from safe_http import guarded_request, is_public_url


class PublicAuditTargetsTests(unittest.TestCase):
    def test_rejects_local_ip_literals_and_credentials(self):
        for url in (
            "http://localhost", "http://127.0.0.1", "http://169.254.169.254/latest/meta-data",
            "http://10.1.2.3", "http://[::1]", "http://host.internal",
            "http://user:pass@example.com", "file:///etc/passwd",
            "http://example.com:99999",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_public_url(url))

    @patch("safe_http.socket.getaddrinfo")
    def test_rejects_mixed_public_private_dns(self, dns):
        dns.return_value = [
            (None, None, None, None, ("93.184.216.34", 443)),
            (None, None, None, None, ("127.0.0.1", 443)),
        ]
        self.assertFalse(is_public_url("https://example.com"))

    @patch("safe_http.socket.getaddrinfo")
    def test_accepts_public_addresses(self, dns):
        dns.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        self.assertTrue(is_public_url("https://example.com"))

    @patch("safe_http.requests.Session")
    @patch("safe_http.socket.getaddrinfo")
    def test_follows_public_redirects(self, dns, session_ctor):
        dns.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        redirect = Mock(status_code=302, headers={"Location": "https://www.example.com/"})
        final = Mock(status_code=200, headers={})
        session_ctor.return_value.request.side_effect = [redirect, final]
        response = guarded_request("GET", "https://example.com/")
        self.assertIs(response, final)
        self.assertEqual(response.history, [redirect])
        self.assertEqual(session_ctor.return_value.request.call_count, 2)

    @patch("safe_http.requests.Session")
    @patch("safe_http.socket.getaddrinfo")
    def test_never_fetches_internal_redirect_target(self, dns, session_ctor):
        dns.return_value = [(None, None, None, None, ("93.184.216.34", 443))]
        response = Mock(status_code=302, headers={"Location": "http://127.0.0.1/admin"})
        session_ctor.return_value.request.return_value = response
        with self.assertRaisesRegex(Exception, "public network addresses"):
            guarded_request("GET", "https://example.com/")
        self.assertEqual(session_ctor.return_value.request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
