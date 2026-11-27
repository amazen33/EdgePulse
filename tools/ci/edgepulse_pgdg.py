"""IOT-WO-02 Amendment 7 (proposed): report-only PGDG PostgreSQL coverage probe.

Grype's dpkg matcher looks an OS package up only in the image distro's
namespace. Debian trixie ships PostgreSQL 17, so PGDG ``postgresql-18``
packages in a trixie image have no records there, and PostgreSQL server CVEs
never reach the gate. Evidence:
security/evidence/supply-chain/pgdg-coverage-gap-2026-11-23.md.

For each scanned image this probe records where coverage is lost and what the
same pinned Grype binary and database snapshot report through two candidate
routes. It never adds findings, exceptions or blocking and never updates the
database. The gate's status is unchanged until the owner approves Amendment 7.
"""
import os
from pathlib import Path
import re

import supply_chain as sc

AUTHORITY = 'IOT-WO-02 Amendment 7 (proposed), report-only probe'
PGDG = re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)-[0-9A-Za-z.]+\.pgdg\d+\+\d+')
SERVER = re.compile(r'postgresql-(?P<major>\d+)')
DEBIAN_ROUTE = 'debian:14'
ERRORS = (ValueError, OSError, KeyError, TypeError)


def cpe(version):
    return 'cpe:2.3:a:postgresql:postgresql:'+version+':*:*:*:*:*:*:*'


def version_key(value):
    return tuple(int(x) if x.isdigit() else -1 for x in re.split(r'[.-]', value))


def packages(sbom):
    """Return PGDG server-source groups and every other PGDG package."""
    groups, other = {}, []
    for artifact in sbom.get('artifacts', []):
        version = artifact.get('version', '')
        if artifact.get('type') != 'deb' or '.pgdg' not in version:
            continue
        source = (artifact.get('metadata') or {}).get('source') or artifact['name']
        server, match = SERVER.fullmatch(source), PGDG.fullmatch(version)
        if server and match and server['major'] == match['major']:
            group = groups.setdefault((source, version), dict(
                source=source, version=version, upstream=match['major']+'.'+match['minor'],
                packages=[], ids=[]))
            group['packages'].append(artifact['name'])
            group['ids'].append(artifact['id'])
        else:
            other.append(dict(name=artifact['name'], version=version, source=source))
    result = [groups[key] for key in sorted(groups)]
    for group in result:
        group['packages'].sort()
    return result, sorted(other, key=lambda v: v['name'])


def grype(tools, out, target, args, name):
    """Run the pinned Grype on the scan's own database snapshot only."""
    env = dict(os.environ, GRYPE_DB_CACHE_DIR=str((out/'database').resolve()), GRYPE_DB_AUTO_UPDATE='false')
    path = out/'pgdg'/name
    path.parent.mkdir(parents=True, exist_ok=True)
    sc.run([tools['grype'], *args], path, env=env, target=target)
    return sc.read(path)


def matches(data):
    rows = {}
    for match in data.get('matches', []):
        vulnerability = match['vulnerability']
        fix = vulnerability.get('fix') or {}
        row = rows.setdefault(vulnerability['id'], dict(
            severity=str(vulnerability.get('severity') or 'Unknown').title(),
            namespaces=[], fixState=fix.get('state', 'unknown'), fixVersions=[], matchTypes=[]))
        row['namespaces'] = sorted(set(row['namespaces']) | {vulnerability.get('namespace', '')})
        row['fixVersions'] = sorted(set(row['fixVersions']) | set(fix.get('versions') or []))
        row['matchTypes'] = sorted(set(row['matchTypes']) | {d.get('type', '') for d in match.get('matchDetails', [])})
        if fix.get('state') == 'fixed':
            row['fixState'] = 'fixed'
    return rows


def database_rows(data):
    """Count distinct vulnerability IDs per OS (or CPE) in `grype db search` output."""
    counts = {}
    for row in data if isinstance(data, list) else []:
        vulnerability = row.get('vulnerability') or {}
        identifier = vulnerability.get('id') or vulnerability.get('ID') or ''
        for package in row.get('packages') or []:
            system = package.get('os') or {}
            key = (system.get('name', '')+':'+str(system.get('version', '')) if system
                   else 'cpe' if package.get('cpe') else package.get('namespace') or 'unknown')
            counts.setdefault(key, set()).add(identifier)
    return {key: len(values) for key, values in sorted(counts.items())}


def severities(rows):
    result = {}
    for row in rows.values():
        result[row['severity']] = result.get(row['severity'], 0)+1
    return dict(sorted(result.items()))


def attempt(entry, key, action):
    try:
        entry[key] = action()
    except ERRORS as error:
        entry[key] = dict(error=str(error))


def upstream_route(tools, out, target, digest, group):
    affected = matches(grype(tools, out, target, [cpe(group['upstream']), '-o', 'json'],
                             digest+'.'+group['source']+'.cpe-'+group['upstream']+'.grype.json'))
    major = group['upstream'].split('.')[0]
    fixes = sorted({v for row in affected.values() for v in row['fixVersions']
                    if v.split('.')[0] == major and version_key(v) > version_key(group['upstream'])},
                   key=version_key)
    if not fixes:
        major, minor = group['upstream'].split('.')
        fixes = [major+'.'+str(int(minor)+1)]
    controls = []
    for version in fixes[:3]:
        found = matches(grype(tools, out, target, [cpe(version), '-o', 'json'],
                              digest+'.'+group['source']+'.cpe-'+version+'.grype.json'))
        controls.append(dict(version=version, matches=len(found),
                             stillAffected=sorted(set(found) & set(affected))))
    return dict(input=cpe(group['upstream']), matches=len(affected), severities=severities(affected),
                vulnerabilities=affected, fixedControls=controls)


def debian_route(tools, out, target, digest, sbom, group):
    ids = set(group['ids'])
    subset = dict(sbom, artifacts=[a for a in sbom['artifacts'] if a['id'] in ids], files=[],
                  artifactRelationships=[r for r in sbom.get('artifactRelationships', [])
                                         if r.get('parent') in ids and r.get('child') in ids])
    path = out/'pgdg'/(digest+'.'+group['source']+'.syft.json')
    sc.write(path, subset)
    affected = matches(grype(tools, out, target, ['sbom:'+str(path.resolve()), '--distro', DEBIAN_ROUTE, '-o', 'json'],
                             digest+'.'+group['source']+'.'+DEBIAN_ROUTE.replace(':', '-')+'.grype.json'))
    return dict(distro=DEBIAN_ROUTE, matches=len(affected), severities=severities(affected),
                vulnerabilities=affected)


def image_probe(tools, out, image, searches):
    digest = image['digest'].split(':')[1]
    sbom = sc.read(out/'sboms'/(digest+'.syft.json'))
    scanned = sc.read(out/(digest+'.grype.json'))
    distro = scanned.get('distro') or {}
    namespace = str(distro.get('name', ''))+':'+str(distro.get('version', '')).split('.')[0]
    dpkg = {}
    for match in scanned.get('matches', []):
        dpkg[match['artifact']['name']] = dpkg.get(match['artifact']['name'], 0)+1
    groups, other = packages(sbom)
    entries = []
    for group in groups:
        entry = {k: v for k, v in group.items() if k != 'ids'}
        entry['dpkgPassMatches'] = {name: dpkg.get(name, 0) for name in group['packages']}
        rows = searches.get(group['source'], {'error': 'database search not run'})
        entry['databaseRows'] = rows
        lost = not any(entry['dpkgPassMatches'].values())
        entry['status'] = 'lost in the dpkg pass' if lost else 'matched by the dpkg pass'
        if lost:
            known = 'error' not in rows
            present = ', '.join(k+' '+str(v) for k, v in rows.items() if k != namespace and v) if known else ''
            entry['lossPoint'] = ('Grype dpkg-matcher searches only '+namespace+', which holds '+
                                  (str(rows.get(namespace, 0)) if known else 'an unknown number of')+
                                  ' vulnerability records for source package '+group['source']+
                                  ('; records exist for: '+present if present else ''))
        attempt(entry, 'upstreamCpeRoute', lambda: upstream_route(tools, out, image['target'], digest, group))
        attempt(entry, 'debianRoute', lambda: debian_route(tools, out, image['target'], digest, sbom, group))
        entries.append(entry)
    for value in other:
        value['dpkgPassMatches'] = dpkg.get(value['name'], 0)
    return dict(target=image['target'], distroNamespace=namespace, groups=entries, otherPgdgPackages=other)


def probe(plan, tools, out):
    """Report-only. Callers must not merge any of this into findings or status."""
    result = dict(authority=AUTHORITY, reportOnly=True, routeDistro=DEBIAN_ROUTE, images=[], databaseSearches={})
    images, sources = [], set()
    for image in plan['images']:
        try:
            groups, other = packages(sc.read(out/'sboms'/(image['digest'].split(':')[1]+'.syft.json')))
        except ERRORS as error:
            result['images'].append(dict(target=image['target'], error=str(error)))
            continue
        if groups or other:
            images.append(image)
            sources |= {g['source'] for g in groups}
    for source in sorted(sources):
        attempt(result['databaseSearches'], source, lambda: database_rows(grype(
            tools, out, images[0]['target'], ['db', 'search', '--pkg', source, '--limit', '0', '-o', 'json'],
            'db-search.'+source+'.json')))
    for image in images:
        try:
            result['images'].append(image_probe(tools, out, image, result['databaseSearches']))
        except ERRORS as error:
            result['images'].append(dict(target=image['target'], error=str(error)))
    sc.write(out/'pgdg-coverage.json', result)
    # Readable even when a later gate step fails before report.md is written.
    (out/'pgdg-coverage.md').write_text(markdown(dict(pgdgCoverage=result)), encoding='utf-8', newline='\n')
    return result


def markdown(report):
    value = report.get('pgdgCoverage')
    if not value:
        return ''
    lines = ['## PGDG PostgreSQL coverage probe (report-only)', '',
             AUTHORITY+'. Not part of the gate status: it adds no finding, exception or block.', '']
    if value.get('error'):
        return '\n'.join(lines+['Probe error: '+sc.safe(value['error']), ''])+'\n'
    lines += ['| Target | Source package/version | Upstream | dpkg pass | Image distro records | Upstream CPE route | Fixed control | '+
              sc.safe(value['routeDistro'])+' route |', '| --- | --- | --- | ---: | --- | --- | --- | --- |']
    def route(item):
        if 'error' in item:
            return 'error: '+sc.safe(item['error'])
        return str(item['matches'])+' ('+', '.join(k+' '+str(v) for k, v in item['severities'].items())+')'
    notes = []
    for image in value['images']:
        if image.get('error'):
            notes.append('- `'+sc.safe(image['target'])+'`: probe error: '+sc.safe(image['error']))
            continue
        for group in image['groups']:
            rows = group['databaseRows']
            records = ('error' if 'error' in rows else str(rows.get(image['distroNamespace'], 0)))+' ('+sc.safe(image['distroNamespace'])+')'
            upstream = group.get('upstreamCpeRoute', {})
            controls = '; '.join(c['version']+': '+str(len(c['stillAffected']))+' still affected'
                                 for c in upstream.get('fixedControls', [])) if 'error' not in upstream else 'n/a'
            lines.append('| '+' | '.join([
                '`'+sc.safe(image['target'])+'`', sc.safe(group['source']+' '+group['version']), sc.safe(group['upstream']),
                str(sum(group['dpkgPassMatches'].values())), records, route(upstream), sc.safe(controls),
                route(group.get('debianRoute', {}))])+' |')
            if group.get('lossPoint'):
                notes.append('- Coverage loss for `'+sc.safe(group['source']+' '+group['version'])+'`: '+sc.safe(group['lossPoint'])+'.')
        for other in image.get('otherPgdgPackages', []):
            notes.append('- Other PGDG package `'+sc.safe(other['name']+' '+other['version'])+'`: dpkg pass only, '+
                         str(other['dpkgPassMatches'])+' matches.')
    return '\n'.join(lines+['']+notes)+'\n\n'
