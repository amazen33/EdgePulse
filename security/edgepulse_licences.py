"""EdgePulse extensions to the unchanged port: ADRs 0024, 0025 and 0026."""
from itertools import product
import fnmatch
import re


# ADR 0026 Decision 1. No family permission is applied to shipped components.
BUILD_FAMILIES = [
    'MPL-1.1', 'MPL-2.0', 'EPL-1.0', 'EPL-2.0', 'CDDL-1.0', 'CDDL-1.1',
    'LGPL-2.1', 'LGPL-2.1-only', 'LGPL-2.1-or-later',
    'LGPL-3.0', 'LGPL-3.0-only', 'LGPL-3.0-or-later',
    'GPL-2.0', 'GPL-2.0-only', 'GPL-2.0-or-later',
    'GPL-3.0', 'GPL-3.0-only', 'GPL-3.0-or-later',
]
BUILD_EXCEPTIONS = ['Classpath-exception-2.0', 'GCC-exception-3.1', 'LLVM-exception']
# IOT-WO-02 architect ruling, 2026-10-20: known permissive build forms only.
KNOWN_BUILD_REFS = {
    'LicenseRef-public-domain-aopalliance': ('aopalliance:aopalliance', '1.0'),
    'LicenseRef-public-domain-xz-1.9': ('org.tukaani:xz', '1.9'),
}
BLOCKED = ['AGPL-*', 'SSPL-*', 'BUSL-*', 'Elastic-*', '*Commons-Clause*',
           '*Proprietary*', '*proprietary*', '*EULA*', '*Account-Gated*',
           'NOASSERTION', 'NONE', 'UNKNOWN']


def options(tree):
    """Resolve OR only; an AND's obligations and a WITH exception stay intact."""
    if tree[0] in ('id', 'WITH'):
        return [tree]
    left, right = options(tree[1]), options(tree[2])
    if tree[0] == 'OR':
        return left + right
    return [('AND', a, b) for a, b in product(left, right)]


def render(tree):
    if tree[0] == 'id':
        return tree[1]
    if tree[0] == 'WITH':
        return render(tree[1]) + ' WITH ' + tree[2]
    return '(' + render(tree[1]) + ' ' + tree[0] + ' ' + render(tree[2]) + ')'


def election(entry, policy, parse, evaluate, identifiers):
    """ADR 0026: require an explicit, admissible election from declared options."""
    declared = parse(entry['spdx'])
    selected = parse(entry['electedSpdx'])
    if selected not in options(declared):
        raise ValueError('Elected SPDX is not an option of the declared expression')
    if any(fnmatch.fnmatchcase(term, pattern)
           for term in identifiers(selected) for pattern in BLOCKED):
        raise ValueError('ADR 0026 blocked or unknown licence')
    permitted = list(policy['permitted'])
    exceptions = list(policy['permittedExceptions'])
    if entry['class'] == 'build-tool':
        permitted += BUILD_FAMILIES + ['Apache-1.1'] + list(KNOWN_BUILD_REFS) + list(policy.get('knownPermissiveBuildLicences', {}))
        exceptions += BUILD_EXCEPTIONS
    elif entry['class'] == 'exception':
        authorized = policy['exceptions'].get(entry['name'], {})
        if (authorized.get('spdx') != entry['electedSpdx']
                or authorized.get('adr') != entry.get('adr')):
            raise ValueError('Exception is not authorized by the policy')
        permitted += list(identifiers(selected))
    elif entry['class'] == 'weak-copyleft':
        permitted += ['MPL-2.0']
    elif entry['class'] == 'base-os':
        permitted += ['GPL-*', 'LGPL-*']
    if not evaluate(selected, permitted, exceptions):
        raise ValueError('Elected SPDX expression is not permitted for ' + entry['class'])
    return selected


def stored_build_licence(entry, tree, root, identifiers, policy):
    for term in identifiers(tree):
        if term.startswith('LicenseRef-'):
            record = policy.get('knownPermissiveBuildLicences', {}).get(term, {})
            authorized = KNOWN_BUILD_REFS.get(term) == (entry['name'], entry['version']) or (
                record.get('name') == entry['name'] and record.get('version') == entry['version'])
            if entry['class'] != 'build-tool' or not authorized:
                raise ValueError('Unapproved build-tool LicenseRef')
            path = root / entry.get('notice', '')
            if not path.is_file() or not path.read_text(encoding='utf-8').strip():
                raise ValueError('LicenseRef build-tool requires stored full licence text')
            from licence_inventory import digest
            if digest(path) != entry.get('licenceTextSHA256'):
                raise ValueError('Stored LicenseRef text changed; reverify source')


def maven_build_tool(component):
    """ADRs 0024/0025: the collector supplies independently checked reachability."""
    observations = component['observations']
    if not observations:
        raise ValueError('Missing Maven build-tool evidence')
    if any(x.get('shippedReachable') or x.get('packaged') for x in observations):
        raise ValueError('Build-tool is reachable from a shipped classpath or packaged')
    if any(not (x.get('testOnlyModule') or x.get('scope') == 'test'
                # IOT-WO-06 ruling 2026-10-21: mechanically inventoried POM imports.
                or (x.get('kind') == 'bom-import' and x.get('type') == 'pom' and x.get('scope') == 'import')
                or x.get('kind') in ('plugin', 'plugin-dependency', 'build-extension', 'code-generator'))
           for x in observations):
        raise ValueError('Maven build-tool is neither test-scoped nor a build plugin')


def named_jakarta(entry):
    """ADR 0025's exception is exact-name, elected EPL, unmodified and versioned."""
    if entry.get('adr') != '0025':
        return
    if (entry['name'] != 'jakarta.annotation:jakarta.annotation-api'
            or entry['electedSpdx'] != 'EPL-2.0' or not entry.get('unmodified')):
        raise ValueError('ADR 0025 exception is restricted to unmodified Jakarta Annotations')
    version = re.escape(entry['version'])
    if not re.fullmatch(
            r'https://repo\.maven\.apache\.org/maven2/jakarta/annotation/jakarta\.annotation-api/'
            + version + r'/jakarta\.annotation-api-' + version + r'-sources\.jar',
            entry.get('upstreamSource', '')):
        raise ValueError('Jakarta exception requires upstream source for the exact version')
