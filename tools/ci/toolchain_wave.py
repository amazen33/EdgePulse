"""ADR-0049 Amendments 1/1a: evidence-bound proposals, never self-approval. MIT."""
from datetime import date, timedelta
import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]


def policy(root=ROOT):
    return json.loads((root / 'security/toolchain-wave-policy.json').read_text(encoding='utf-8'))


def version(value, go=False):
    prefix = 'go' if go else 'v?'
    match = re.fullmatch(prefix + r'(\d+)\.(\d+)\.(\d+)', value)
    return tuple(map(int, match.groups())) if match else None


def module_version(value):
    """SemVer ordering includes the pseudo-versions used by Go-team modules."""
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?', value)
    if not match:
        return None
    major, minor, patch = map(int, match.groups()[:3])
    prerelease = match[4]
    identifiers = tuple((0, int(v)) if v.isdigit() else (1, v) for v in (prerelease or '').split('.'))
    return major, minor, patch, int(prerelease is None), identifiers


def qualifies(finding, rules):
    """Match the affected package and scanner fix; advisory IDs grant nothing."""
    if finding.get('kev') is not False or finding['severity'] not in ('Critical', 'High'):
        return False
    fixes = finding.get('fixVersions', [])
    if not finding.get('fixAvailable', bool(fixes)) or not fixes:
        return False
    if finding['package'] == 'stdlib':
        built = version(finding['version'], go=True)
        if not built:
            return False
        latest = rules['stdlibLatestPatches'].get('.'.join(map(str, built[:2])))
        patched = version(latest or '')
        # Other supported lines may also have fixes. The built line's newest
        # patch must be explicitly among the scanner-reported fixed versions.
        return bool(patched and patched[:2] == built[:2] and patched > built
                    and latest in [v.removeprefix('v') for v in fixes])
    if finding['package'] not in rules['goTeamModules']:
        return False
    built = module_version(finding['version'])
    parsed = [module_version(v) for v in fixes]
    return bool(built and all(v and v > built for v in parsed))


def isolation(controls):
    return (controls.get('clusterOrLanOnly') is True
            and controls.get('noExternalService') is True
            and isinstance(controls.get('externalEgress'), str)
            and bool(controls['externalEgress'].strip()))


def validate_entry(entry, finding, rules, on, *, proposal=False):
    """The normal gate additionally checks exact identity, owner and lifetime."""
    wave = entry['toolchainWave']
    if entry['approvedBy'] != ('' if proposal else 'amazen33'):
        raise ValueError('Toolchain-wave batch needs the owner approval')
    if not re.fullmatch(r'[a-z0-9./:_-]+@sha256:[a-f0-9]{64}', entry['target']):
        raise ValueError('Toolchain-wave entries require one immutable image digest')
    if not re.fullmatch(r'CVE-\d{4}-\d+', entry['vulnerability']):
        raise ValueError('Toolchain-wave entries require one canonical CVE')
    if not qualifies(finding, rules):
        raise ValueError('Non-qualifying toolchain-wave exception: ' + finding['vulnerability'])
    if sorted(wave['fixVersions']) != sorted(finding.get('fixVersions', [])):
        raise ValueError('Toolchain-wave scanner fixes changed; refresh evidence')
    if wave['noEligibleFixedRelease'] is not True or not isolation(wave['isolation']):
        raise ValueError('Toolchain-wave upstream/isolation conditions not met')
    if not entry.get('controls') or not entry.get('workOrder'):
        raise ValueError('Toolchain-wave controls and refresh work order required')
    checked = date.fromisoformat(wave['checkedOn'])
    if checked > on:
        raise ValueError('Toolchain-wave upstream eligibility evidence date is in the future')
    url = urlparse(wave['upstreamEvidence'])
    if url.scheme != 'https' or not url.netloc:
        raise ValueError('Toolchain-wave upstream evidence must be HTTPS')
    scanner = wave['requiredScanner']
    admitted = json.loads((ROOT / 'tools/ci/toolchain.lock.json').read_text(encoding='utf-8'))['artifacts']['grype']
    if scanner != {'name': 'grype', 'version': '0.119.0', 'binarySHA256': admitted['binarySHA256']}:
        raise ValueError('Toolchain-wave evidence needs the pinned Grype scanner')


def review(findings, *, eligible_fixed_release, controls, upstream_evidence,
           rules=None, on=None):
    """Prepare a per-image/package/CVE batch outside the active exception registry."""
    on = on or date.today()
    rules = rules or policy()
    blocking = [v for v in findings if v.get('blocked', bool(v.get('blockReason')))]
    reasons = []
    if eligible_fixed_release is not False:
        reasons.append('No verified absence of an eligible fixed upstream release')
    if not isolation(controls):
        reasons.append('Missing component isolation controls')
    if any(v.get('kev') for v in findings):
        reasons.append('KEV cannot use the toolchain-wave rule')
    unqualified = [v for v in blocking if not qualifies(v, rules)]
    if unqualified:
        reasons.append('Blocking findings outside the package/fix-version rule')
    entries = []
    if blocking and not reasons:
        admitted = json.loads((ROOT / 'tools/ci/toolchain.lock.json').read_text(encoding='utf-8'))['artifacts']['grype']
        for value in blocking:
            entry = {k: value[k] for k in ('target', 'package', 'version', 'vulnerability', 'severity')}
            if not re.fullmatch(r'CVE-\d{4}-\d+', entry['vulnerability']):
                raise ValueError('One canonical CVE required per proposed image/package entry')
            entry.update(owner='amazen33', approvedBy='', createdOn=on.isoformat(),
                         expires=(on + timedelta(days=30 if value['severity'] == 'Critical' else 60)).isoformat(),
                         workOrder='WO-34', controls=[
                             'Cluster-internal; no Service exposed outside the namespace.',
                             'External egress only to ' + controls['externalEgress'] + '.',
                             'Refresh within 14 days of an eligible fixed upstream release; immediate KEV escalation.'],
                         reason='ADR-0049 Amendment 1a: scanner fixes ' + ', '.join(value['fixVersions'])
                         + '; no eligible fixed upstream release; not KEV. Owner batch approval required.',
                         toolchainWave={'fixVersions': value['fixVersions'], 'noEligibleFixedRelease': True,
                             'checkedOn': on.isoformat(), 'upstreamEvidence': upstream_evidence,
                             'isolation': dict(controls), 'requiredScanner': {'name': 'grype', 'version': '0.119.0',
                                 'binarySHA256': admitted['binarySHA256']}})
            validate_entry(entry, value, rules, on, proposal=True)
            entries.append(entry)
    return {'status': 'blocked' if reasons else 'owner-review-required' if entries else 'no-exception-needed',
            'blockers': reasons, 'nonQualifying': unqualified, 'proposedExceptions': entries}
