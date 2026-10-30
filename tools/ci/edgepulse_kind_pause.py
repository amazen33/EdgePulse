"""IOT-WO-08 Amendment 2: a non-executable kind pause and restoration watch.

This is EdgePulse wiring. No KEV exception, upstream checker change or new
legacy admission is granted. Only the paused node leaves active inventory.
"""
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re

import supply_chain as sc
import supply_chain_watch as watch

RECORD = 'dev/kind/rehearsal-pause.json'
REPOSITORY = 'docker.io/kindest/node'


def record(root):
    path = root/RECORD
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
        raise ValueError('Invalid kind pause record')
    value = sc.read(path)
    if (value.get('authority') != 'IOT-WO-08 Amendment 2 E-2(a)' or value.get('paused') is not True
            or value.get('pausedOn') != '2026-10-30'
            or value.get('repository') != REPOSITORY or value.get('restoreWithinDays') != 14
            or value.get('package') != 'libbrotli1' or value.get('minimumVersion') != '1.1.0-2+deb13u1'
            or value.get('kubernetesMinor') != '1.36'
            or not re.fullmatch(r'sha256:[a-f0-9]{64}', value.get('lastDigest', ''))
            or date.fromisoformat(value['pausedOn']) > sc.today()):
        raise ValueError('Kind pause must match the exact owner-approved scope and restore duty')
    return value


def debian_at_least(value, minimum):
    """Debian Policy 5.6.12 ordering; no additional executable or dependency.

    https://www.debian.org/doc/debian-policy/ch-controlfields.html#version
    """
    def split(text):
        if not re.fullmatch(r'[0-9A-Za-z.+:~\-]+', text):
            raise ValueError('Unverifiable Debian package version')
        epoch, rest = text.split(':', 1) if ':' in text else ('0', text)
        if not epoch.isdigit():
            raise ValueError('Invalid Debian epoch')
        upstream, revision = rest.rsplit('-', 1) if '-' in rest else (rest, '0')
        return int(epoch), upstream, revision
    def compare(a, b):
        def order(c):
            return -1 if c == '~' else 0 if not c or c.isdigit() else ord(c) if c.isalpha() else ord(c)+256
        while a or b:
            while (a and not a[0].isdigit()) or (b and not b[0].isdigit()):
                left, right = order(a[:1]), order(b[:1])
                if left != right:
                    return 1 if left > right else -1
                a, b = a[1:], b[1:]
            da, db = re.match(r'\d*', a)[0], re.match(r'\d*', b)[0]
            a, b = a[len(da):], b[len(db):]
            da, db = da.lstrip('0'), db.lstrip('0')
            if len(da) != len(db):
                return 1 if len(da) > len(db) else -1
            if da != db:
                return 1 if da > db else -1
        return 0
    ea, ua, ra = split(value)
    eb, ub, rb = split(minimum)
    return (ea > eb) if ea != eb else (compare(ua, ub) or compare(ra, rb)) >= 0


def candidates(config, values):
    found = {}
    for release in values:
        if release.get('draft') or release.get('prerelease'):
            continue
        published = datetime.fromisoformat(release['published_at'].replace('Z', '+00:00'))
        pattern = r'kindest/node:v('+re.escape(config['kubernetesMinor'])+r'\.\d+)@(sha256:[a-f0-9]{64})'
        for version, digest in re.findall(pattern, release.get('body', '')):
            target = REPOSITORY+'@'+digest
            item = dict(target=target, source='registry:'+target, digest=digest, platform='linux/amd64',
                        origins=[], introduced=False, nodeVersion=version, release=release['tag_name'],
                        publishedAt=release['published_at'])
            if target not in found or published < datetime.fromisoformat(found[target]['publishedAt'].replace('Z', '+00:00')):
                found[target] = item
    if not found:
        raise ValueError('No verifiable published kind node on the paused Kubernetes line')
    # Scan all releases since the pause, plus the newest existing candidate.
    # An older fixed publication must never lose its restoration clock.
    latest = max(found.values(), key=lambda v: (tuple(map(int,v['nodeVersion'].split('.'))), v['publishedAt']))
    return [v for v in found.values() if v == latest or v['publishedAt'][:10] >= config['pausedOn']]


def run_watch(root, tools, out, cache, database, on=None):
    config = record(root)
    if not config:
        return None
    on = on or sc.today()
    values = watch.releases('kubernetes-sigs/kind', {})
    raw = sc.fetch('https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json')
    catalogue = json.loads(raw)
    kev_ids = {v['cveID'] for v in catalogue['vulnerabilities']}
    observations = []
    for item in candidates(config, values):
        destination = out/item['digest'].split(':')[1]
        try:
            result = sc.scan(dict(images=[item], lockfiles=[], coverage=[], base=None),
                             tools, cache, destination, root, database=database)
        except sc.ScannerCommandError as error:
            observations.append(item | dict(fixed=False, scanFailed=True,
                                           reason='Candidate scan failed: '+error.tool))
            continue
        sbom = sc.read(destination/'sboms'/(item['digest'].split(':')[1]+'.syft.json'))
        versions = {v['version'] for v in sbom['artifacts'] if v['type']=='deb' and v['name']=='libbrotli1'}
        kev = sorted({v['vulnerability'] for v in result['findings'] if set(v['aliases']) & kev_ids})
        fixed = bool(versions) and all(debian_at_least(v, config['minimumVersion']) for v in versions) and not kev
        observations.append(item | dict(fixed=fixed, scanFailed=False, brotliVersions=sorted(versions),
                                       kev=kev, findings=len(result['findings']), database=result['database']))
    dates = [date.fromisoformat(v['publishedAt'][:10]) for v in observations if v['fixed']]
    available = min(dates) if dates else None
    due = available+timedelta(days=14) if available else None
    value = dict(authority=config['authority'], paused=True, scope='Watch only; not an active gated image or approval',
                 checkedOn=on.isoformat(), source='https://api.github.com/repos/kubernetes-sigs/kind/releases?per_page=100',
                 sourceSHA256=sc.sha(json.dumps(values, sort_keys=True).encode()),
                 kevCatalogueSHA256=sc.sha(raw), candidates=observations,
                 fixedAvailableSince=available.isoformat() if available else None,
                 restoreBy=due.isoformat() if due else None,
                 blocked=bool(due and on > due) or any(v['scanFailed'] for v in observations))
    sc.write(out/'watch.json', value)
    return value


def markdown(value):
    if not value:
        return ''
    lines = ['## Paused kind rehearsal — IOT-WO-08 Amendment 2', '',
             'No kind node is an active gated or executable input. No KEV exception is granted.',
             'Restore within 14 days of verified fixed upstream image availability.', '',
             '| Candidate | Published | Brotli | Fixed and no KEV |', '| --- | --- | --- | --- |']
    for item in value['candidates']:
        lines.append('| '+sc.safe(item['target'])+' | '+sc.safe(item['publishedAt'])+' | '+
                     sc.safe(', '.join(item.get('brotliVersions', [])) or 'unverified')+' | '+str(item['fixed'])+' |')
    lines += ['', 'Restore by: '+str(value['restoreBy'] or 'no verified fixed image yet')+
              '; restoration watch '+('FAIL' if value['blocked'] else 'pass')+'.', '']
    return '\n'.join(lines)
