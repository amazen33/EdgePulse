#!/usr/bin/env python
"""Install the registered Maven archive into owned target/ paths only."""
import hashlib
import json
import os
from pathlib import Path
import tarfile
import urllib.request

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / 'security/toolchain.lock.json').read_text(encoding='utf-8'))
pin = next(x for x in lock['tools'] if x['name'] == 'maven')
work = root / 'target/licence-tools'
work.mkdir(parents=True, exist_ok=True)
archive = work / ('apache-maven-' + pin['version'] + '-bin.tar.gz')
if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != pin['sha256'][0]:
    with urllib.request.urlopen(pin['archiveUrl'], timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != pin['sha256'][0]:
        raise ValueError('Maven archive SHA-256 mismatch')
    archive.write_bytes(data)
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
