"""ADR 0028: EdgePulse-only test-harness classification and staleness guard.

The upstream scanners, evaluator, schemas and licence classes are unchanged.
Only tracked inputs are inspected; no harness image or cluster is executed.
"""
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re

import supply_chain as sc
import supply_chain_watch as watch
import edgepulse_kind_pause as kind_pause


def policy(root):
    value = sc.read(root/'security/supply-chain-policy.json')
    entries = value['testHarnessImages']
    names = [v['repository'] for v in entries]
    if value['authority'] != 'ADR 0028' or len(names) != 5 or len(set(names)) != 5:
        raise ValueError('ADR 0028 requires the five architect-reviewed harness images')
    return value


def mentions(text, repositories):
    return any(re.search(r'(?<![\w./-])(?:(?:docker\.io|index\.docker\.io|registry-1\.docker\.io)/)?' +
                         re.escape(repo.removeprefix('docker.io/')) + r'(?=[:@\s\x22\x27`,/]|$)', text)
               for repo in repositories)


def check_references(root, references, paths=None):
    """Fail closed for tracked shipped references and transitive script callers.

    Security/ADR/work-order records and the unchanged upstream watch mapping
    describe scan inputs rather than packaging them. Test sources may plant
    violations. None of these exclusions applies under charts/ or deploy/.
    """
    import yaml  # The checksum-only/tool-SBOM entrypoints remain stdlib-only.
    config = policy(root)
    repositories = {v['repository'] for v in config['testHarnessImages']}
    paused = kind_pause.record(root)
    inactive = {paused['repository']} if paused else set()
    for ref, origins in references.items():
        if ref.split('@')[0] in repositories and any(not p.startswith('dev/kind/') for p in origins):
            raise ValueError('ADR 0028 harness image in shipped input: '+', '.join(origins))
        if ref.split('@')[0] in inactive:
            raise ValueError('Paused kind node must not remain an active image input')
    paths = paths if paths is not None else sc.tracked(root)
    texts = {}
    permitted = ('dev/kind/', 'security/evidence/', 'docs/adr/', 'docs/work-orders/', 'tools/ci/tests/')
    records = {'security/licence-register.json', 'security/licence-policy.json',
               'security/vulnerability-exceptions.json', 'security/supply-chain-policy.json'}
    for path in paths:
        file = root/path
        if file.is_symlink():
            raise ValueError('ADR 0028 refuses symbolic input: '+path)
        try:
            text = file.read_text(encoding='utf-8')
        except UnicodeError:
            continue
        texts[path] = text
        if (path.startswith(('charts/', 'deploy/', 'argocd/', 'packaging/'))
                and Path(path).suffix != '.md' and 'dev/kind/' in text):
            raise ValueError('ADR 0028 harness input reused by packaging: '+path)
        if mentions(text, repositories) and not (path.startswith(permitted) or path in records or path in (
                'tools/ci/supply_chain_watch.py', 'tools/ci/edgepulse_harness.py', 'tools/ci/edgepulse_kind_pause.py')):
            if not path.startswith('.github/workflows/'):
                raise ValueError('ADR 0028 harness image reference outside harness/records: '+path)
    # A workflow can reach the harness through an intermediate script/action.
    # Conservatively follow literal tracked file names and harness directories.
    callers = {p for p in paths if p.startswith('dev/kind/')}
    def reached(text):
        return 'dev/kind/' in text or any(c in text or (Path(c).suffix in ('.ps1', '.py', '.sh')
                                                       and Path(c).name in text) for c in callers)
    changed = True
    while changed:
        added = {p for p, text in texts.items() if p not in callers and not p.startswith(
            ('security/', 'docs/', 'tools/ci/tests/'))
            and reached(text)}
        changed = bool(added)
        callers.update(added)
        callers.update(str(Path(p).parent).replace('\\', '/') for p in added
                       if Path(p).name in ('action.yml', 'action.yaml'))
    jobs = []
    for path, text in texts.items():
        if not path.startswith('.github/workflows/') or not path.endswith(('.yml', '.yaml')):
            continue
        flow = yaml.safe_load(text)
        for name, job in flow['jobs'].items():
            if paused and path == '.github/workflows/kind-rehearsal.yml' and name == 'kind-smoke':
                if job.get('if') not in (False, '${{ false }}'):
                    raise ValueError('Paused kind rehearsal job must be explicitly skipped')
            body = json.dumps(job)
            inherited = json.dumps(flow.get('env', {}))+' '+body
            if inactive and mentions(inherited, inactive):
                raise ValueError('Paused kind node cannot be executed by a workflow')
            if not (mentions(inherited, repositories) or reached(inherited)):
                continue
            permissions = job.get('permissions', flow.get('permissions'))
            if permissions != {'contents': 'read'}:
                raise ValueError('ADR 0028 harness job must have only contents: read: '+path+':'+name)
            if re.search(r'\bsecrets\b', inherited) or job.get('environment') is not None:
                raise ValueError('ADR 0028 harness job cannot receive secrets/environment: '+path+':'+name)
            jobs.append(path+':'+name)
    if not jobs:
        raise ValueError('ADR 0028 harness workflow coverage unexpectedly empty')
    targets = sorted(ref for ref in references if ref.split('@')[0] in repositories)
    if len(targets) != len(repositories-inactive) or {t.split('@')[0] for t in targets} != repositories-inactive:
        raise ValueError('ADR 0028 harness image inventory does not match class list')
    return dict(authority='ADR 0028', targets=targets, references={t:references[t] for t in targets},
                readOnlySecretlessJobs=sorted(jobs), pausedInputs=[paused] if paused else [])


def version(value):
    if not re.fullmatch(r'v?\d+\.\d+\.\d+', value):
        raise ValueError('Unverifiable harness release version')
    return tuple(map(int, value.removeprefix('v').split('.')))


def release_checks(root, targets, on=None):
    """Check live official release metadata on every gate/nightly/watch run.

    kind node publication is bound to kind's release notes for the locked
    Kubernetes minor. Cilium Envoy follows the locked Cilium chart bundle.
    Failure to retrieve/interpret provenance fails rather than resetting age.
    """
    on = on or sc.today()
    pins = sc.read(root/'dev/kind/pins.json')
    config = policy(root)
    memo, checks = {}, []
    for entry in config['testHarnessImages']:
        repository, family = entry['repository'], entry['pinFamily']
        paused = kind_pause.record(root)
        if paused and repository == paused['repository']:
            continue
        target = next(t for t in targets if t.split('@')[0] == repository)
        upstream = {'kind':'kubernetes-sigs/kind', 'cilium':'cilium/cilium',
                    'cnpg':'cloudnative-pg/cloudnative-pg'}[family]
        source = 'https://api.github.com/repos/'+upstream+'/releases?per_page=100'
        values = watch.releases(upstream, memo)
        current = pins[family]['version']
        candidates = []
        for release in values:
            if release.get('draft') or release.get('prerelease') or not re.fullmatch(r'v\d+\.\d+\.\d+', release['tag_name']):
                continue
            published = datetime.fromisoformat(release['published_at'].replace('Z', '+00:00'))
            age = (datetime.combine(on, datetime.min.time(), tzinfo=timezone.utc)-published).total_seconds()/86400
            if age < 14:
                continue
            tag = release['tag_name']
            if family == 'cilium' and version(tag)[:2] != version(current)[:2]:
                continue
            node = None
            if family == 'kind':
                minor = re.search(r'kindest/node:v(\d+\.\d+)\.', pins['kind']['node']).group(1)
                nodes = re.findall(r'kindest/node:v('+re.escape(minor)+r'\.\d+)@sha256:[a-f0-9]{64}', release['body'])
                if not nodes:
                    continue
                node = max(nodes, key=version)
            candidates.append((version(tag), published, release, node, age))
        if not candidates:
            raise ValueError('ADR 0028 no verifiable eligible harness release: '+repository)
        _, published, release, node, age = max(candidates, key=lambda v:v[:2])
        def is_newer(candidate):
            if family != 'kind':
                return candidate[0] > version(current)
            current_node = re.search(r'kindest/node:v([\d.]+)@', pins['kind']['node']).group(1)
            # A newer kind release can rebuild the same Kubernetes patch.
            return (version(candidate[3]) > version(current_node) or
                    (candidate[0] > version(current) and pins['kind']['node'] not in candidate[2]['body']))
        newer = any(is_newer(v) for v in candidates)
        overdue = []
        for candidate in candidates:
            if not is_newer(candidate) or candidate[4] <= 30:
                continue
            reason = next((v for v in config.get('ownerReasons', []) if v['repository'] == repository
                           and v['release'] == candidate[2]['tag_name']), None)
            if reason and (reason['owner'] != 'amazen33' or not reason['reason'].strip()
                           or date.fromisoformat(reason['date']) > on):
                raise ValueError('ADR 0028 invalid dated owner reason')
            overdue.append(dict(release=candidate[2]['tag_name'], publishedAt=candidate[2]['published_at'], ownerReason=reason))
        checks.append(dict(target=target, currentRelease=current, newestEligibleRelease=release['tag_name'],
                           publishedAt=release['published_at'], source=source, sourceSHA256=sc.sha(json.dumps(values,sort_keys=True).encode()),
                           eligibleAgeDays=int(age), newer=newer, nodeVersion=node,
                           blocked=any(v['ownerReason'] is None for v in overdue), overdueReleases=overdue))
    return checks


def apply(report, guard, checks):
    targets = set(guard['targets'])
    for value in report['findings']:
        if value['target'] not in targets:
            continue
        value['imageClass'] = 'test-harness'
        if value['kev']:
            value.update(blocked=True, blockReason='KEV')
        elif value['severity'] in ('Critical', 'High') and value['fixAvailable']:
            value.update(blocked=False, blockReason='')
            value['reportOnlyReason'] = 'ADR 0028 test-harness; KEV and staleness still block'
    report['testHarness'] = guard | dict(staleness=checks)
    report['status'] = 'failed' if any(v['blocked'] for v in report['findings']) or any(v['blocked'] for v in checks) else 'passed'
    return report


def markdown(report):
    lines = ['## ADR 0028 test-harness report-only findings', '',
             'Static scan evidence; residual developer/runner risk is owner-accepted by ADR 0028. KEV and staleness block.', '']
    for paused in report['testHarness'].get('pausedInputs', []):
        lines.append('- Kind rehearsal paused under '+paused['authority']+
                     '; node excluded from active inputs; weekly watch retains the 14-day restore duty.')
    for check in report['testHarness']['staleness']:
        lines.append('- `'+sc.safe(check['target'])+'`: newest eligible '+sc.safe(check['newestEligibleRelease'])+
                     ' ('+sc.safe(check['publishedAt'])+'); staleness '+('FAIL' if check['blocked'] else 'pass')+'.')
    for target in report['testHarness']['targets']:
        lines += ['', '### `'+sc.safe(target)+'`', '',
                  '| Package/version | Vulnerability | Severity | First seen |', '| --- | --- | --- | --- |']
        values = [v for v in report['findings'] if v['target'] == target and v.get('reportOnlyReason')]
        for v in sorted(values, key=lambda v:(v['package'], v['vulnerability'])):
            lines.append('| '+' | '.join(sc.safe(x) for x in (v['package']+' '+v['version'], v['vulnerability'], v['severity'], v['firstSeen']))+' |')
        if not values:
            lines.append('| None | | | |')
    return '\n'.join(lines)+'\n'
