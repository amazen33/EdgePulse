#!/usr/bin/env python3
"""Candidate-only, offline licence inventory and expiring evidence ratchet (WO-02)."""
import argparse
from collections import Counter
from datetime import date
import fnmatch
import json
import licence_ladder
import os
from pathlib import Path
import re
import sys

import jsonschema
import yaml

from licence_inventory import enumerate_inputs, identity, digest, objects


def expression(text):
    """Small strict SPDX expression parser: WITH > AND > OR; no eval or substring matching."""
    tokens = re.findall(r'\(|\)|[A-Za-z0-9][A-Za-z0-9.+:-]*', text)
    if ''.join(tokens) != re.sub(r'\s+', '', text):
        raise ValueError('Invalid SPDX expression: ' + text)
    position = 0

    def atom():
        nonlocal position
        if position >= len(tokens):
            raise ValueError('Incomplete SPDX expression')
        value = tokens[position]
        position += 1
        if value == '(':
            result = either()
            if position >= len(tokens) or tokens[position] != ')':
                raise ValueError('Unbalanced SPDX expression')
            position += 1
            return result
        if value in ('AND', 'OR', 'WITH', ')'):
            raise ValueError('Expected SPDX identifier')
        result = ('id', value)
        if position < len(tokens) and tokens[position] == 'WITH':
            position += 1
            if position >= len(tokens) or tokens[position] in ('AND', 'OR', 'WITH', '(', ')'):
                raise ValueError('Expected SPDX exception')
            result = ('WITH', result, tokens[position])
            position += 1
        return result

    def both():
        nonlocal position
        result = atom()
        while position < len(tokens) and tokens[position] == 'AND':
            position += 1
            result = ('AND', result, atom())
        return result

    def either():
        nonlocal position
        result = both()
        while position < len(tokens) and tokens[position] == 'OR':
            position += 1
            result = ('OR', result, both())
        return result

    result = either()
    if position != len(tokens):
        raise ValueError('Trailing SPDX tokens')
    return result


def evaluate(tree, permitted, exceptions):
    op = tree[0]
    if op == 'id':
        return any(fnmatch.fnmatchcase(tree[1], item) for item in permitted)
    if op == 'WITH':
        return evaluate(tree[1], permitted, exceptions) and tree[2] in exceptions
    left, right = (evaluate(x, permitted, exceptions) for x in tree[1:])
    return left and right if op == 'AND' else left or right


def identifiers(tree):
    if tree[0] == 'id':
        return {tree[1]}
    if tree[0] == 'WITH':
        return identifiers(tree[1])
    return identifiers(tree[1]) | identifiers(tree[2])


def expiry(entry, today, maximum=None):
    expires = date.fromisoformat(entry['expires'])
    recorded = date.fromisoformat(entry['recordedOn'])
    if expires <= today:
        raise ValueError('Expired: ' + entry.get('id', entry.get('name', '?')))
    if recorded > today or expires <= recorded or (maximum and (expires - recorded).days > maximum):
        raise ValueError('Invalid expiry window: ' + entry.get('id', entry.get('name', '?')))


def module_off(root, module):
    if module == 'module-5a/':
        config = yaml.safe_load((root / 'module-5a/config/rag.yaml').read_text())
        return config.get('enabled') is False
    if module == 'module-5b/':
        config = json.loads((root / 'module-5b/reference-profile.json').read_text())
        if config.get('offload_enabled') is not False or config.get('agent_batch_submission_enabled') is not False:
            return False
        # The profile drives generators; current quotas/replicas are in their output,
        # not numeric fields in reference-profile.json. Check both, fail closed.
        for path, field in [('module-5b/manifests/queues.yaml', 'nominalQuota'),
                            ('module-5b/manifests/workloads.yaml', 'replicas')]:
            values = [obj[field] for doc in yaml.safe_load_all((root / path).read_text())
                      for obj in objects(doc) if field in obj]
            if not values or any(value != 0 for value in values):
                return False
        return True
    return False


def observed_integrities(component):
    values = set()
    if component['ecosystem'] == 'oci-image' and component['version'].startswith('sha256:'):
        values.add(component['version'])
    for item in component['observations']:
        if item.get('integrity'):
            values.add(item['integrity'])
        if item.get('sha256'):
            values.add('sha256:' + item['sha256'])
        values.update('sha256:' + x for x in item.get('hashes', []))
    return sorted(values)


def check_component(entry, component, policy, root, today, baseline):
    kind = entry['class']
    tree = expression(entry['spdx'])
    permitted = list(policy['permitted'])
    exceptions = policy['permittedExceptions']
    if kind == 'blocked':
        raise ValueError('Blocked class')
    if entry.get('expires'):
        limit = 183 if entry.get('adr') == '0054' else 120
        expiry(entry, today, limit if kind == 'exception' else 60 if kind == 'pending-removal' else None)
    actual = observed_integrities(component)
    if entry.get('integrities', []) != actual:
        raise ValueError('Artifact integrity changed; reverify the registered release')
    if kind in ('build-tool', 'weak-copyleft', 'base-os') and entry.get('unmodified') is not True:
        raise ValueError('Class requires an unmodified component')
    if kind == 'build-tool':
        permitted += ['MPL-2.0', 'GPL-*', 'LGPL-*']
        if component['ecosystem'] == 'npm':
            if any(not x.get('dev') or x.get('production') for x in component['observations']):
                raise ValueError('Build-tool is reachable from production or is not dev-only')
        elif component['ecosystem'] == 'tool':
            if set(component['locations']) != {'tools/ci/toolchain.lock.json'}:
                raise ValueError('Build-tool binary occurs outside the CI tool lock')
        else:
            raise ValueError('Unsupported build-tool ecosystem')
    elif kind == 'weak-copyleft':
        permitted += ['MPL-2.0']
        if 'MPL-2.0' not in identifiers(tree) or entry.get('separateUnit') is not True:
            raise ValueError('Weak-copyleft is for separate unmodified MPL units only')
        if not actual and f'artifact-integrity:{entry["id"]}' not in baseline:
            raise ValueError('Weak-copyleft requires hash pin evidence')
        if not entry.get('notice') or not (root / entry['notice']).is_file():
            raise ValueError('Missing redistribution notice')
    elif kind == 'base-os':
        permitted += ['GPL-*', 'LGPL-*']
        distribution_image=component['ecosystem']=='oci-image' and any(fnmatch.fnmatchcase(entry['name'], name) for name in policy['baseOSRepositories'])
        cloud_image=component['ecosystem']=='manifest' and entry['name'] in policy.get('baseOSCloudImages',[]) and component['locations']==['deploy/hyperv/ubuntu-image.lock.json']
        if not (distribution_image or cloud_image):
            raise ValueError('base-os is restricted to distribution images')
    elif kind == 'operator-pulled':
        if entry['name'] not in policy['operatorPulledRepositories']:
            raise ValueError('Unapproved operator-pulled component')
        if any('Dockerfile' in path for path in component['locations']):
            raise ValueError('Operator-pulled image cannot be baked into a Twinfra image')
        text = (root / '00-setup-ubuntu-host.sh').read_text()
        if not re.search(r'\$\{GPU_SMOKE_TEST:=false\}', text):
            raise ValueError('CUDA smoke test must default to false')
        if not re.search(r'^GPU_SMOKE_TEST=false$', (root / 'host.env.example').read_text(), re.M):
            raise ValueError('Example environment must keep the CUDA smoke test off')
        if not (root / entry['notice']).is_file():
            raise ValueError('Missing operator EULA notice')
        return
    elif kind == 'disabled-module':
        module = entry.get('module')
        if module not in policy['disabledModules'] or not module_off(root, module):
            raise ValueError('Disabled module is enabled or its switch cannot be verified')
        if any(not path.startswith((module, 'tools/ci/')) for path in component['locations']):
            raise ValueError('Disabled component escapes its module/test-only scope')
        return
    elif kind == 'exception':
        authorized = policy['exceptions'].get(entry['name'])
        if not authorized or entry['spdx'] != authorized['spdx'] or entry['adr'] != authorized['adr']:
            raise ValueError('Exception is not authorized by the policy')
        if authorized.get('module') and not module_off(root, authorized['module']):
            raise ValueError('Module enabled with an open runtime exception')
        permitted.extend(identifiers(expression(authorized['spdx'])))
        if entry.get('adr')=='0054' and not (root/entry.get('notice','')).is_file():
            raise ValueError('Missing ADR-0054 notice/source offer')
    elif kind == 'pending-removal':
        if entry['name'] not in policy['pendingRemoval'] or not entry.get('expires'):
            raise ValueError('Pending removal is not named in the owner decision')
        return
    pending_source = entry.get('evidencePending') and entry['spdx'] == 'NOASSERTION' and f'licence-source:{entry["id"]}' in baseline
    if not pending_source and not evaluate(tree, permitted, exceptions):
        raise ValueError('SPDX expression is not permitted for ' + kind)
    for item in component['observations']:
        if item.get('spdx') and expression(item['spdx']) != tree:
            raise ValueError('npm lock licence changed from registered expression')


def audit(root, today=None, rendered=()):
    root, today = Path(root), today or date.today()
    policy = json.loads((root / 'security/licence-policy.json').read_text())
    register = json.loads((root / 'security/licence-register.json').read_text())
    baseline_doc = json.loads((root / 'security/licence-baseline.json').read_text())
    schema = json.loads((root / 'security/licence-register.schema.json').read_text())
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(register)
    components, findings = enumerate_inputs(root, rendered)
    errors, entries, baseline = [], {}, {}
    notice_lock = root / 'security/licences/rag-notices.lock.json'
    if notice_lock.exists():
        for path, expected in json.loads(notice_lock.read_text()).items():
            if not (root / path).is_file() or digest(root / path) != expected:
                errors.append('Missing/changed image licence text: ' + path)
        dockerfile = (root / 'module-5a/images/rag.Dockerfile').read_text()
        if 'COPY security/licences/rag/ /usr/share/licenses/vcloud-rag/' not in dockerfile:
            errors.append('RAG image omits the offline licence notices')
    else:
        errors.append('Missing image licence notice integrity lock')
    for item in register['components']:
        expected = identity(item['ecosystem'], item['name'], item['version'])
        if item['id'] != expected or expected in entries:
            errors.append('Invalid/duplicate register identity: ' + item['id'])
        entries[expected] = item
    for item in baseline_doc['findings']:
        try:
            if item['id'] in baseline or not all(item.get(k) for k in ('reason', 'owner', 'requiredEvidence')):
                raise ValueError('Duplicate/incomplete baseline entry')
            if item['kind'] not in policy['baselineKinds']:
                raise ValueError('Forbidden baseline kind')
            expiry(item, today, 90)
            baseline[item['id']] = item
        except (ValueError, KeyError) as error:
            errors.append(f'Baseline {item.get("id")}: {error}')
    for key, finding in findings.items():
        approved = baseline.get(key)
        if not approved or approved.get('fingerprint') != finding['fingerprint']:
            errors.append('New/changed evidence finding: ' + key)
    for key, component in components.items():
        entry = entries.get(key)
        if not entry:
            errors.append('Unregistered component: ' + key)
            continue
        try:
            check_component(entry, component, policy, root, today, baseline)
            if 'ladder' in policy:
                licence_ladder.validate(entry, policy, identifiers(expression(entry['spdx'])), today)
            if entry.get('evidencePending') and f'licence-source:{key}' not in baseline:
                raise ValueError('Unverified licence requires an explicit dated evidence baseline')
            if entry['ecosystem'] == 'oci-image' and entry['class'] != 'pending-removal':
                sbom = entry.get('imageSBOM')
                if sbom:
                    path = root / sbom['path']
                    if not path.is_file() or digest(path) != sbom['sha256']:
                        raise ValueError('Missing/changed reviewed image SBOM evidence')
                elif f'image-sbom:{key}' not in baseline:
                    raise ValueError('Missing image SBOM evidence or dated baseline')
        except (ValueError, KeyError, OSError) as error:
            errors.append(key + ': ' + str(error))
    for item in baseline.values():
        entry = entries.get(item.get('component'))
        if entry and entry['class'] not in ('disabled-module', 'operator-pulled'):
            forbidden = ['AGPL-*', 'SSPL-*', 'BUSL-*', 'Elastic-*', 'LicenseRef-*EULA*']
            known = identifiers(expression(entry['spdx']))
            if any(fnmatch.fnmatchcase(term, pattern) for term in known for pattern in forbidden):
                errors.append('Known prohibited deployed licence cannot enter baseline: ' + item['id'])
    for key in sorted(entries.keys() - components.keys()):
        errors.append('Stale register entry (remove with component): ' + key)
    # Baselines never override class validation, and cannot admit an unknown component.
    rows = [dict(component, **{k: entries[key].get(k) for k in
            ('class', 'spdx', 'adr', 'expires', 'module')}) for key, component in sorted(components.items()) if key in entries]
    return dict(status='failed' if errors else 'passed', checkedOn=today.isoformat(), errors=errors,
                countsByEcosystem=dict(sorted(Counter(x['ecosystem'] for x in rows).items())),
                countsByClass={kind: sum(x['class'] == kind for x in rows) for kind in policy['classes']}, components=rows,
                openBaseline=baseline_doc['findings'],
                legacyBackfill=[dict(id=e['id'], tier=e['tier'], due=e['enterpriseGrade']['due'])
                                for e in entries.values() if e.get('enterpriseGrade', {}).get('status') == 'legacy-pending'],
                pendingRemoval=[e for e in entries.values() if e['class'] == 'pending-removal'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--rendered', type=Path, action='append', default=[])
    args = parser.parse_args()
    try:
        report = audit(args.root, rendered=args.rendered)
    except (ValueError, KeyError, OSError, jsonschema.ValidationError) as error:
        report = dict(status='failed', errors=[str(error)])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Licence gate: ' + report['status'])
    for key in ('countsByEcosystem', 'countsByClass'):
        print(key + ': ' + json.dumps(report.get(key, {}), sort_keys=True))
    backfill = Counter(e['due'] for e in report.get('legacyBackfill', []))
    if backfill:
        print('ADR-0054 legacy-pending backfill: ' + json.dumps(dict(sorted(backfill.items()))))
    for kind in ('openBaseline', 'pendingRemoval'):
        for entry in report.get(kind, []):
            print(f'{kind}: {entry["id"]} expires {entry["expires"]}')
    for error in report['errors']:
        print(error, file=sys.stderr)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        lines = ['### Candidate licence gate: ' + report['status'], '',
                 'Ecosystems: `' + json.dumps(report.get('countsByEcosystem', {}), sort_keys=True) + '`', '',
                 'Classes: `' + json.dumps(report.get('countsByClass', {}), sort_keys=True) + '`', '']
        if backfill:
            lines += ['Legacy enterprise-grade backfill (Foundation 1.0):', '']
            lines += [f'- {count} entries due **{deadline}**' for deadline, count in sorted(backfill.items())]
            lines.append('')
        for kind in ('openBaseline', 'pendingRemoval'):
            lines.append('Open ' + kind + ':')
            lines.extend(f'- `{e["id"]}` — expires **{e["expires"]}**' for e in report.get(kind, []))
            lines.append('')
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n')
    return int(report['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())
