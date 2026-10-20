"""EdgePulse ADR 0014 adapter over the unchanged ADR-0049 scanner engine.

Registry inputs are public, digest-bound Linux/amd64 artifacts. No containers,
cluster commands, host configuration, or candidate application code are run.
"""
import argparse
import copy
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import supply_chain as sc
from stage_tools import verified

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'amazen33/EdgePulse'
BASE = 'ca6177636893b497fde6f58db2a917dbf4b216d6'


def canonical(reference):
    if not isinstance(reference, str) or not re.fullmatch(
            r'[a-z0-9][A-Za-z0-9._:/-]*@sha256:[a-f0-9]{64}', reference):
        raise ValueError('Image referenced without an immutable digest')
    repository, digest = reference.split('@')
    if ':' in repository.rsplit('/', 1)[-1]:
        repository = repository.rsplit(':', 1)[0]
    first = repository.split('/')[0]
    if '.' not in first and ':' not in first and first != 'localhost':
        repository = 'docker.io/' + (repository if '/' in repository else 'library/' + repository)
    return repository + '@' + digest


def image_references(root, revision=None):
    import yaml
    def content(path):
        return sc.git(root, 'show', revision + ':' + path) if revision else (root/path).read_text(encoding='utf-8')
    paths = (sc.git(root, 'ls-tree', '-r', '--name-only', revision).splitlines()
             if revision else sc.tracked(root))
    found = {}
    def add(value, path):
        ref = canonical(value)
        found.setdefault(ref, set()).add(path)
    pins = json.loads(content('dev/kind/pins.json'))
    for entry in pins.values():
        for key in ('image', 'node'):
            if entry.get(key):
                add(entry[key], 'dev/kind/pins.json')
        for value in entry.get('images', {}).values():
            add(value, 'dev/kind/pins.json')
    def walk(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'image' and isinstance(child, str):
                    add(child, path)
                else:
                    walk(child, path)
        elif isinstance(value, list):
            for child in value:
                walk(child, path)
    for path in paths:
        if path.startswith(('docs/', '.github/', 'tools/ci/tests/')):
            continue
        if path.endswith(('.yaml', '.yml')) and '/templates/' not in path:
            text = content(path)
            if '{{' not in text:
                for value in yaml.safe_load_all(text):
                    walk(value, path)
        if Path(path).name == 'Dockerfile':
            for value in re.findall(r'^FROM\s+(\S+)', content(path), re.M):
                add(value, path)
    return {ref: sorted(paths) for ref, paths in sorted(found.items())}


def inventory(root, base=None):
    if base and not re.fullmatch(r'[a-f0-9]{40}', base):
        raise ValueError('Immutable base required')
    current = image_references(root)
    old = image_references(root, base) if base else {}
    images, coverage = [], []
    for ref, origins in current.items():
        repository = ref.split('@')[0]
        components = [path+':'+repository for path in origins]
        previous = [dict(target=prior,source='registry:'+prior,digest=prior.split('@')[1],
                         platform='linux/amd64',component=path+':'+repository)
                    for prior, paths in old.items() if prior.split('@')[0] == repository
                    for path in origins if path in paths]
        images.append(dict(target=ref, source='registry:'+ref, digest=ref.split('@')[1],
                           platform='linux/amd64', origins=components, introduced=bool(base and ref not in old),
                           previousInputs=previous,historicalTargets=sorted({p['target'] for p in previous})))
        coverage.append(dict(entry=', '.join(origins), pinned=ref, mode='pinned-registry',
                             selected=True, scannedInputs=[ref]))
    return dict(version=1, base=base, full=True, images=images, coverage=coverage,
                lockfiles=[p for p in sc.tracked(root) if sc.is_lockfile(p) and not p.startswith('docs/')])


def scanner_metadata(root):
    lock = sc.read(root/'security/toolchain.lock.json')
    return {name: {key: lock['artifacts'][name][key] for key in
                   ('version', 'sha256', 'binarySHA256', 'published')}
            for name in sc.TOOLS}


def verify_manifests(root):
    """Verify the pinned upstream checksum documents before staging binaries."""
    owned_lock = sc.read(root/'security/toolchain.lock.json')
    lock = owned_lock['artifacts']
    for name in sc.TOOLS:
        entry = lock[name]
        manifest = verified(sc.fetch(entry['checksumURL']), entry['checksumSHA256'])
        filename = entry['url'].rsplit('/', 1)[1]
        if not re.search(r'^' + re.escape(entry['sha256']) + r'\s+\*?' + re.escape(filename) + r'\s*$',
                         manifest.decode('utf-8'), re.M):
            raise ValueError('Official checksum document does not bind ' + name)
        if (sc.today() - date.fromisoformat(entry['published'])).days < 14:
            raise ValueError('Scanner is younger than the 14-day cool-off')
    # An ignored, mechanically generated compatibility view. The unchanged
    # upstream stager/verifier reads this path; the licence inventory reads the
    # authoritative tracked security/toolchain.lock.json and its tool records.
    sc.write(root/'tools/ci/toolchain.lock.json', dict(platform='linux-amd64', artifacts=lock))


def maven_inputs(root, out):
    """Check Part A's resolved scopes/BOM agreement before scanning every scope."""
    sys.path.insert(0, str(root/'security'))
    from maven_inventory import enumerate_maven
    observations = []
    register = sc.read(root/'security/licence-register.json')
    enumerate_maven(root, register, lambda *args, **kwargs: observations.append((args, kwargs)))
    evidence = sc.read(root/'target/licence/maven-evidence.json')
    inputs = []
    for pom, module in evidence['modules'].items():
        if module['packaging'] != 'pom':
            inputs.append((pom, root/module['allBom'], root/module['resolvedTree']))
    for number, module in enumerate(evidence['pluginModules']):
        inputs.append(('executed-plugin-'+str(number), root/module['sbom'], None))
    destination = out/'maven'
    destination.mkdir(parents=True, exist_ok=True)
    documents = []
    for index, (module, path, tree) in enumerate(inputs):
        target = destination/(str(index)+'.cdx.json')
        target.write_bytes(path.read_bytes())
        documents.append(dict(module=module, path=str(target.resolve()), sbomSHA256=sc.sha(path.read_bytes()),
                              resolvedTreeSHA256=sc.sha(tree.read_bytes()) if tree else None))
    sc.write(out/'maven-inputs.json', documents)
    return documents


def scan_maven(root, tools, out):
    inputs = maven_inputs(root, out)
    if not inputs:
        raise ValueError('Maven reactor scan unexpectedly empty')
    command = [tools['osv-scanner'], 'scan', 'source', '--no-resolve', '--no-call-analysis=go', '--format=json']
    for item in inputs:
        command.extend(['--sbom', item['path']])
    sc.run(command, out/'osv-maven.json', allowed=(0, 1))
    aliases = {}
    for item in inputs:
        aliases[item['path']] = item['module']
        aliases[Path(item['path']).relative_to(root).as_posix()] = item['module']
    normalized = normalize_maven_result(sc.read(out/'osv-maven.json'), inputs)
    values = sc.osv_findings(normalized, root, aliases)
    results = []
    for value in values:
        module = value['target'].removeprefix('lockfile:')
        finding = sc.finding('maven:'+module, value['package'], value['version'], value['aliases'],
                             value['severity'], value['fixAvailable'], 'osv',
                             fix_versions=value['fixVersions'])
        finding['packageClass'] = 'java-archive (Maven)'
        results.append(finding)
    sc.write(out/'maven-findings.json', results)
    return results


def normalize_maven_result(data, inputs):
    """OSV's SBOM output uses artifactId; advisories use groupId:artifactId.

    Resolve this join through the exact scanned BOM, never through a guessed
    group or a vulnerable advisory's list of other affected artifacts. Preserve
    the raw scanner JSON separately for audit.
    """
    value = copy.deepcopy(data)
    if not isinstance(value.get('results'), list):
        raise ValueError('Invalid OSV Maven result')
    for source in value['results']:
        path = source['source']['path']
        matches = [item for item in inputs if path in (item['path'], Path(item['path']).as_posix())]
        if len(matches) != 1:
            raise ValueError('OSV source is not one of the scanned Maven BOMs')
        components = sc.read(Path(matches[0]['path']))['components']
        for item in source.get('packages', []):
            package = item['package']
            if package.get('ecosystem') != 'Maven':
                raise ValueError('Unexpected ecosystem in Maven SBOM results')
            candidates = {component.get('group','')+':'+component['name'] for component in components
                          if component['version']==package['version'] and package['name'] in
                          (component['name'], component.get('group','')+':'+component['name'])}
            if len(candidates) != 1:
                raise ValueError('Ambiguous or absent Maven package identity in scanned BOM')
            package['name'] = candidates.pop()
    return value


def classify_maven_findings(findings, root, base):
    if not base:
        return findings
    previous = json.loads(sc.git(root, 'show', base+':security/licence-register.json'))
    components = {(entry['name'],entry['version']):entry for entry in previous['components']
                  if entry['ecosystem']=='maven'}
    for value in findings:
        entry = components.get((value['package'],value['version']))
        module = value['target'].removeprefix('maven:')
        # Per-module runtime/test dependencies must already belong to that
        # module. Executed plugin dependencies are inventoried at the root POM.
        location = 'pom.xml' if module.startswith('executed-plugin-') else module
        value['introduced'] = not (entry and location in entry['locations'])
    return findings


def initial_list_context():
    """Port ADR-0049's initial-list PR mechanism to this one owner branch.

    A green bootstrap PR is not owner approval. Main and ordinary pushes
    reject pending-owner; the owner must approve the concrete list in review.
    """
    if os.environ.get('GITHUB_EVENT_NAME') != 'pull_request':
        return False
    event = sc.read(Path(os.environ['GITHUB_EVENT_PATH']))['pull_request']
    head = event['head']
    return (head['ref'] == 'codex/iot-wo-02-b'
            and head['repo']['full_name'] == REPOSITORY
            and event['base']['ref'] == 'main'
            and event['base']['repo']['full_name'] == REPOSITORY)


def validate_exception_evidence(exceptions, root, on):
    sc.validate_exceptions(exceptions, root, on, bootstrap=initial_list_context())
    for entry in exceptions['exceptions']:
        evidence = entry.get('controls', [])
        if not evidence:
            raise ValueError('Exception requires evidence references in controls')
        for path in evidence:
            if not re.fullmatch(r'security/evidence/vulnerability-exceptions/[a-z0-9-]+\.md', path):
                raise ValueError('Exception evidence must be a reviewed repository record')
            file = root/path
            if not file.is_file() or file.is_symlink() or len(file.read_text(encoding='utf-8').strip()) < 40:
                raise ValueError('Missing exception evidence')
            if entry['target'].startswith('maven:') or entry.get('package', '').startswith('org.'):
                if 'Reachability:' not in file.read_text(encoding='utf-8'):
                    raise ValueError('JVM exception requires recorded call-path/classpath evidence')


def evaluate(result, exceptions, kev, root, state=None, on=None):
    on = on or sc.today()
    validate_exception_evidence(exceptions, root, on)
    kev_ids = {v['cveID'] for v in kev['vulnerabilities']}
    for value in result['findings']:
        if not value['fixAvailable'] and not (set(value['aliases']) & kev_ids):
            if any(all(e[k] == value[k] for k in ('target','package','version','vulnerability'))
                   for e in exceptions['exceptions']):
                raise ValueError('No-fix findings are report-only and cannot have exceptions')
    report = sc.evaluate(result, exceptions, kev, state, on, bootstrap=initial_list_context(), root=root)
    for value in report['findings']:
        if value['kev']:
            value['blocked'] = True
            value['blockReason'] = 'KEV'
    report['status'] = 'failed' if any(v['blocked'] for v in report['findings']) else 'passed'
    report['ownerApprovalPending'] = any(e['approvedBy']=='pending-owner' for e in exceptions['exceptions'])
    # No automatically invented exceptions, mitigations or environment claims.
    report['proposedExceptions'] = dict(version=1, exceptions=[])
    return report


def evidence_only(old, new, old_policy, new_policy):
    """IOT-WO-02 ruling: the ONLY permissible backfill change is imageSBOM."""
    if 'imageSBOM' in old or set(new) != set(old) | {'imageSBOM'}:
        raise ValueError('Evidence backfill must only add imageSBOM')
    if {k:v for k,v in new.items() if k != 'imageSBOM'} != old:
        raise ValueError('Non-evidence field changed alongside imageSBOM')
    if {k:v for k,v in new_policy.items() if k != 'sha256'} != {k:v for k,v in old_policy.items() if k != 'sha256'}:
        raise ValueError('Legacy tier or due date changed')
    sys.path.insert(0, str(ROOT/'security'))
    from licence_ladder import fingerprint
    if old_policy['sha256'] != fingerprint(old) or new_policy['sha256'] != fingerprint(new):
        raise ValueError('Evidence backfill fingerprint mismatch')


def verify_backfill(root):
    """Compare the seven authorized transitions against immutable pre-Part-B Git objects."""
    before = json.loads(sc.git(root, 'show', BASE+':security/licence-register.json'))
    policy = json.loads(sc.git(root, 'show', BASE+':security/licence-policy.json'))
    baseline = json.loads(sc.git(root, 'show', BASE+':security/licence-baseline.json'))
    old = {entry['id']:entry for entry in before['components']}
    new = {entry['id']:entry for entry in sc.read(root/'security/licence-register.json')['components']}
    old_legacy = policy['ladder']['legacy']
    new_legacy = sc.read(root/'security/licence-policy.json')['ladder']['legacy']
    approved = {entry['component'] for entry in baseline['findings'] if entry['kind']=='image-sbom'}
    # Amendment 5 explicitly authorizes supported-line remediation. Replacing
    # an input retires its legacy admission; the new input needs full records,
    # never a rewritten legacy fingerprint. Unchanged images use evidence_only.
    replacements = {
        'maven|org.apache.tomcat.embed:'+name+'|10.1.30':
        'maven|org.apache.tomcat.embed:'+name+'|10.1.60'
        for name in ('tomcat-embed-core','tomcat-embed-el','tomcat-embed-websocket')}
    replacements['oci-image|ghcr.io/cloudnative-pg/postgresql|sha256:5efb66993894055f0aa50bd94337c6c4ff2e2129f4d433c527151aebbf283fb0'] = (
        'oci-image|ghcr.io/cloudnative-pg/postgresql|sha256:37ade18dbdddba430858c72725aceeec66f33fa5333e82ea1df4942f6c1c83a3')
    retired = {key for key in replacements if key not in new}
    if len(approved) != 7 or old_legacy.keys()-retired != new_legacy.keys():
        raise ValueError('Legacy set changed outside the approved remediation')
    remaining = {entry['id'] for entry in sc.read(root/'security/licence-baseline.json')['findings']}
    fingerprints = []
    for key, original in old_legacy.items():
        if key in retired:
            replacement = new.get(replacements[key], {})
            if (replacement.get('class') != old[key]['class']
                    or replacement.get('electedSpdx') != old[key]['electedSpdx']
                    or replacement.get('tier') != old[key]['tier']
                    or replacement.get('enterpriseGrade',{}).get('status') not in ('pending','verified')):
                raise ValueError('Remediated runtime needs full ADR-0054 records: '+key)
            if key in approved:
                if 'imageSBOM' in replacement:
                    if 'image-sbom:'+key in remaining:
                        raise ValueError('Completed replacement still has an open baseline')
                    from licence_ladder import fingerprint
                    fingerprints.append(dict(id=key,replacement=replacements[key],old=original['sha256'],
                        new=fingerprint(replacement),mode='Amendment 5 replacement; full ADR-0054 record'))
                elif 'image-sbom:'+key not in remaining:
                    raise ValueError('Replacement baseline removed without reviewed imageSBOM')
            continue
        if key in approved and 'imageSBOM' in new[key]:
            evidence_only(old[key], new[key], original, new_legacy[key])
            if 'image-sbom:'+key in remaining:
                raise ValueError('Completed image backfill still has an open baseline')
            fingerprints.append(dict(id=key, old=original['sha256'], new=new_legacy[key]['sha256'],
                                     tier=original['tier'], due=original['due']))
        elif old[key] != new[key] or original != new_legacy[key]:
            raise ValueError('Unapproved legacy change: '+key)
        elif key in approved and 'image-sbom:'+key not in remaining:
            raise ValueError('Baseline removed without reviewed imageSBOM')
    return fingerprints


def canonical_sboms(plan, out):
    destination = out/'reviewed'
    destination.mkdir(parents=True, exist_ok=True)
    result = {}
    for image in plan['images']:
        digest = image['digest'].split(':')[1]
        document = sc.read(out/'sboms'/(digest+'.cdx.json'))
        # Preserve all components, licences, relationships and provenance. Only
        # the document-instance UUID and creation clock are excluded for hashing.
        document.pop('serialNumber', None)
        document.get('metadata', {}).pop('timestamp', None)
        path = destination/(digest+'.cdx.json')
        path.write_text(json.dumps(document, sort_keys=True, separators=(',', ':'))+'\n', encoding='utf-8', newline='\n')
        result[image['target']] = dict(path=path.relative_to(ROOT).as_posix(), sha256=sc.sha(path.read_bytes()))
    sc.write(out/'reviewed-sboms.json', result)
    return result


def image_sboms(root, tools_path, out, cache):
    """Materialize real reviewed-byte inputs for the unchanged licence gate.

    Rebuild/cache through pinned Syft; never fetch an unbound fallback SBOM.
    The licence checker independently compares each file to its reviewed hash.
    """
    out.mkdir(parents=True, exist_ok=True)
    plan = inventory(root)
    tools = sc.verify_tools(tools_path, root)
    sc.sboms(plan, tools, cache, out)
    return canonical_sboms(plan, out)


def run(root, tools_path, out, cache, base=None):
    out.mkdir(parents=True, exist_ok=True)
    plan = inventory(root, base)
    if not plan['images']:
        raise ValueError('Image inventory unexpectedly empty')
    sc.write(out/'inventory.json', plan)
    tools = sc.verify_tools(tools_path, root)
    maven = classify_maven_findings(scan_maven(root, tools, out), root, base)
    result = sc.scan(plan, tools, cache, out, root)
    for image in plan['images']:
        raw = sc.read(out/(image['digest'].split(':')[1]+'.grype.json'))
        classes = {(m['artifact']['name'], m['artifact']['version']):m['artifact']['type'] for m in raw['matches']}
        for value in result['findings']:
            if value['target'] == image['target']:
                value['packageClass'] = classes.get((value['package'], value['version']), 'unknown')
    result['findings'].extend(maven)
    result['toolVersions'] = scanner_metadata(root)
    result['gitCommit'] = sc.git(root, 'rev-parse', 'HEAD')
    result['scanConfiguration'] = dict(platform='linux/amd64', scope='all referenced images, all Maven scopes and executed plugin classpaths, lockfiles')
    raw = sc.fetch('https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json')
    (out/'kev.json').write_bytes(raw)
    state, link = sc.previous_state(REPOSITORY)
    report = evaluate(result, sc.read(root/'security/vulnerability-exceptions.json'), json.loads(raw), root,
                      state if link else None)
    report['trackingIssue'] = link
    report['kev']['downloadSHA256'] = sc.sha(raw)
    report['reviewedSBOMs'] = canonical_sboms(plan, out)
    sc.report_files(report, out)
    print('Supply-chain: '+report['status']+'; '+str(len(plan['images']))+' images; '+str(len(report['findings']))+' findings')
    return int(report['status'] != 'passed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['verify-manifests', 'inventory', 'image-sboms', 'run', 'watch'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, default=ROOT/'target/supply-chain')
    parser.add_argument('--cache', type=Path, default=ROOT/'target/supply-chain-cache')
    parser.add_argument('--tools', type=Path, default=ROOT/'target/scan-tools/bin')
    parser.add_argument('--base')
    args = parser.parse_args()
    try:
        if args.action == 'verify-manifests':
            verify_manifests(args.root)
        elif args.action == 'inventory':
            sc.write(args.out/'inventory.json', inventory(args.root, args.base))
        elif args.action == 'image-sboms':
            image_sboms(args.root, args.tools, args.out, args.cache)
        elif args.action == 'watch':
            import supply_chain_watch as upstream_watch
            # The upstream public API takes its inventory from the scanner
            # module. Adapt that one repository seam in this single-purpose
            # process; restore it even when the blocking pinned scan fails.
            original = sc.inventory
            try:
                sc.inventory = lambda root, **kwargs: inventory(root)
                args.out.mkdir(parents=True, exist_ok=True)
                value = upstream_watch.watch(args.root, sc.verify_tools(args.tools, args.root), args.out, args.cache)
                sc.write(args.out/'watch.json', value)
                (args.out/'watch.md').write_text(value['markdown'], encoding='utf-8')
            finally:
                sc.inventory = original
        else:
            return run(args.root, args.tools, args.out, args.cache, args.base)
        return 0
    except (ValueError, KeyError, OSError) as error:
        print('Supply-chain failure: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
