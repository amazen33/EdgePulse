#!/usr/bin/env python
"""Install the registered Maven archive into owned target/ paths only."""
from datetime import timezone
import email.utils
import hashlib
import http.client
import json
import os
from pathlib import Path
import ssl
import sys
import tarfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
# Bounded retry for transient upstream errors; the SHA-256 pin is never relaxed.
ATTEMPTS = 4
TIMEOUT = 60
BASE_DELAY = 2.0
MAX_DELAY = 30.0
# Maven Central's CDN has returned a transient 404 for the pinned archive.
NOT_FOUND_RETRIES = 1


def retry_after(headers, now):
    """Return the Retry-After delay in seconds, or None when absent or invalid."""
    value = headers.get('Retry-After') if headers is not None else None
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, when.timestamp() - now)


def transient(error, not_found):
    """Classify a download error; return (reason, server delay) or None if fatal."""
    if isinstance(error, urllib.error.HTTPError):
        if error.code == 404 and not_found <= NOT_FOUND_RETRIES:
            return 'HTTP 404', None
        if error.code == 429 or 500 <= error.code <= 599:
            return 'HTTP ' + str(error.code), error.headers
        return None
    if isinstance(error, urllib.error.URLError):
        reason = error.reason
        if isinstance(reason, OSError) and not isinstance(reason, ssl.SSLCertVerificationError):
            return type(reason).__name__, None
        return None
    return type(error).__name__, None


def fetch(url, digest, sleep=time.sleep, clock=time.time):
    """Download url and return its bytes only when the SHA-256 matches digest."""
    not_found = 0
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
                data = response.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError,
                http.client.IncompleteRead) as error:
            if isinstance(error, urllib.error.HTTPError) and error.code == 404:
                not_found += 1
            retry = transient(error, not_found)
            if retry is None or attempt == ATTEMPTS:
                raise
            reason, headers = retry
            wait = retry_after(headers, clock())
            if wait is None:
                wait = BASE_DELAY * 2 ** (attempt - 1)
            wait = min(wait, MAX_DELAY)
            print('Maven download attempt %d/%d failed (%s); retrying in %gs'
                  % (attempt, ATTEMPTS, reason, wait), file=sys.stderr)
            sleep(wait)
            continue
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Maven archive SHA-256 mismatch')
        return data
    raise AssertionError('unreachable')


def main(root=ROOT):
    lock = json.loads((root / 'security/toolchain.lock.json').read_text(encoding='utf-8'))
    pin = next(x for x in lock['tools'] if x['name'] == 'maven')
    work = root / 'target/licence-tools'
    work.mkdir(parents=True, exist_ok=True)
    archive = work / ('apache-maven-' + pin['version'] + '-bin.tar.gz')
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != pin['sha256'][0]:
        archive.write_bytes(fetch(pin['archiveUrl'], pin['sha256'][0]))
    with tarfile.open(archive, 'r:gz') as source:
        prefix = 'apache-maven-' + pin['version'] + '/'
        if any(not m.name.startswith(prefix) for m in source.getmembers()):
            raise ValueError('Unexpected Maven archive root')
        source.extractall(work, filter='data')
    binary = (work / ('apache-maven-' + pin['version']) / 'bin').resolve()
    assert binary.is_relative_to(work.resolve())
    if os.environ.get('GITHUB_PATH'):
        with open(os.environ['GITHUB_PATH'], 'a', encoding='utf-8') as output:
            output.write(str(binary) + '\n')
    print('Verified Maven ' + pin['version'] + ' at ' + str(binary))


if __name__ == '__main__':
    main()
