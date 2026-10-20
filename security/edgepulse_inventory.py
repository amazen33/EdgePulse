"""Repository input adapters; the port's classes and evidence ratchet stay intact."""
import json
import re
from pathlib import Path


def enumerate_edgepulse(root, tracked, add, image):
    lock_path = 'security/toolchain.lock.json'
    lock = json.loads((root / lock_path).read_text(encoding='utf-8'))
    for tool in lock['tools']:
        add('tool', tool['name'], tool['version'], lock_path,
            hashes=tool.get('sha256', []))
    python = next(x['version'] for x in lock['tools'] if x['name'] == 'python')
    for path in tracked:
        if path.startswith('.github/workflows/'):
            text = (root / path).read_text(encoding='utf-8')
            for version in re.findall(r'python-version:\s*[\"\x27]?([0-9.]+)', text):
                if version != python:
                    raise ValueError('CI Python does not match the tool lock: ' + path)
    path = 'dev/kind/pins.json'
    pins = json.loads((root / path).read_text(encoding='utf-8'))
    for name in ('kind', 'kubectl', 'helm'):
        entry = pins[name]
        add('tool', name, entry['version'], path,
            hashes=sorted([entry['windowsSha256'], entry['linuxSha256']]))
    for name in ('cilium', 'cnpg'):
        entry = pins[name]
        eco, key = ('helm-chart', 'chartSha256') if name == 'cilium' else ('manifest', 'manifestSha256')
        add(eco, name, entry['version'], path, sha256=entry[key])
    for entry in pins.values():
        if not isinstance(entry, dict):
            continue
        if entry.get('image'):
            image(entry['image'], path)
        if entry.get('node'):
            image(entry['node'], path)
        for value in entry.get('images', {}).values():
            image(value, path)
