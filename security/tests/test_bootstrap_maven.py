"""Bounded Maven download retry; synthetic bytes, mocked urlopen, no network."""
import email.message
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error

SECURITY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SECURITY))
import bootstrap_maven

URL = 'https://repo.example.invalid/SYNTHETIC-maven-bin.tar.gz'
DATA = b'SYNTHETIC maven archive bytes'
DIGEST = hashlib.sha256(DATA).hexdigest()


def http_error(code, retry_after=None):
    headers = email.message.Message()
    if retry_after is not None:
        headers['Retry-After'] = retry_after
    return urllib.error.HTTPError(URL, code, 'synthetic', headers, io.BytesIO())


def body(data=DATA):
    return io.BytesIO(data)


class FetchRetryTest(unittest.TestCase):
    def fetch(self, *outcomes, clock=lambda: 0.0):
        self.sleeps = []
        with mock.patch.object(bootstrap_maven.urllib.request, 'urlopen',
                               side_effect=list(outcomes)) as urlopen, \
                mock.patch('sys.stderr', new_callable=io.StringIO):
            self.urlopen = urlopen
            return bootstrap_maven.fetch(URL, DIGEST, sleep=self.sleeps.append, clock=clock)

    def test_success_after_transient_errors(self):
        data = self.fetch(http_error(429, '7'), http_error(503),
                          urllib.error.URLError(TimeoutError('timed out')), body())
        self.assertEqual(DATA, data)
        self.assertEqual(4, self.urlopen.call_count)
        self.assertEqual([7.0, 4.0, 8.0], self.sleeps)
        self.urlopen.assert_called_with(URL, timeout=60)

    def test_read_timeout_and_reset_are_retried(self):
        self.assertEqual(DATA, self.fetch(TimeoutError('read'), ConnectionResetError(), body()))
        self.assertEqual([2.0, 4.0], self.sleeps)

    def test_single_404_is_retried(self):
        self.assertEqual(DATA, self.fetch(http_error(404), body()))
        self.assertEqual([2.0], self.sleeps)

    def test_second_404_gives_up(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.fetch(http_error(404), http_error(404), body())
        self.assertEqual(404, caught.exception.code)
        self.assertEqual(2, self.urlopen.call_count)

    def test_gives_up_after_last_attempt(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.fetch(*[http_error(502)] * bootstrap_maven.ATTEMPTS, body())
        self.assertEqual(502, caught.exception.code)
        self.assertEqual(bootstrap_maven.ATTEMPTS, self.urlopen.call_count)
        self.assertEqual([2.0, 4.0, 8.0], self.sleeps)

    def test_other_client_errors_are_not_retried(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.fetch(http_error(403), body())
        self.assertEqual(1, self.urlopen.call_count)
        self.assertEqual([], self.sleeps)

    def test_hash_mismatch_fails_without_retry(self):
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            self.fetch(body(b'SYNTHETIC tampered bytes'), body())
        self.assertEqual(1, self.urlopen.call_count)
        self.assertEqual([], self.sleeps)

    def test_retry_after_date_and_cap(self):
        self.fetch(http_error(503, 'Thu, 01 Jan 1970 00:00:20 GMT'),
                   http_error(429, '600'), body(), clock=lambda: 5.0)
        self.assertEqual([15.0, bootstrap_maven.MAX_DELAY], self.sleeps)

    def test_invalid_retry_after_uses_backoff(self):
        self.fetch(http_error(429, 'soon'), body())
        self.assertEqual([2.0], self.sleeps)


class MainFailsClosedTest(unittest.TestCase):
    def test_mismatch_writes_no_archive(self):
        work = SECURITY.parent / 'target'
        work.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix='bootstrap-maven-test-', dir=work)
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / 'security').mkdir()
        (root / 'security/toolchain.lock.json').write_text(json.dumps({'tools': [
            {'name': 'maven', 'version': '0.0.0-SYNTHETIC', 'archiveUrl': URL, 'sha256': [DIGEST]}]}))
        with mock.patch.object(bootstrap_maven.urllib.request, 'urlopen',
                               side_effect=[body(b'SYNTHETIC tampered bytes')]):
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                bootstrap_maven.main(root)
        self.assertEqual([], list((root / 'target/licence-tools').iterdir()))


if __name__ == '__main__':
    unittest.main()
