"""ADR-0054 runtime admission and owner-approved dated legacy backfill. MIT."""
from datetime import date
import calendar
import fnmatch
import hashlib
import json
from urllib.parse import urlparse

CRITERIA = ('maturity', 'governance', 'activitySupport', 'securityProcess', 'supplyChain', 'adoption')


def fingerprint(entry):
    core = {k: v for k, v in entry.items() if k not in ('tier', 'enterpriseGrade')}
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def runtime(entry):
    return entry['ecosystem'] != 'github-action' and entry['class'] not in (
        'build-tool', 'disabled-module', 'operator-pulled')


def due(value, today):
    if date.fromisoformat(value) <= today:
        raise ValueError('ADR-0054 evidence/re-evaluation overdue: ' + value)


def evidence(record, today):
    if record.get('result') != 'pass':
        raise ValueError('Enterprise-grade criterion does not pass')
    url = urlparse(record.get('evidence', ''))
    if url.scheme != 'https' or not url.netloc:
        raise ValueError('Enterprise-grade criterion needs an HTTPS evidence link')
    if date.fromisoformat(record['date']) > today:
        raise ValueError('Enterprise-grade evidence date is in the future')


def tier_for(identifiers, policy):
    for term in identifiers:
        if any(fnmatch.fnmatchcase(term, p) for p in policy['ladder']['never']):
            raise ValueError('Never licence cannot be admitted: ' + term)
    tiers = []
    for term in identifiers:
        matches = [int(t) for t, names in policy['ladder']['tiers'].items()
                   if any(fnmatch.fnmatchcase(term, p) for p in names)]
        if not matches:
            raise ValueError('No ADR-0054 tier for ' + term)
        tiers.append(min(matches))
    return max(tiers)


def climbing(entry, today):
    record = entry.get('climbing', {})
    candidates = record.get('rejectedCandidates', [])
    if not candidates or not record.get('reviewAtMinorUpgrade'):
        raise ValueError('Tier 3/4 requires a climbing record and minor-upgrade review')
    for candidate in candidates:
        if not all(candidate.get(k) for k in ('name', 'tier', 'failedCriterion', 'evidence')):
            raise ValueError('Incomplete rejected candidate')
        if candidate['tier'] >= entry['tier']:
            raise ValueError('Climbing candidate must be more permissive')
    reviewed = date.fromisoformat(record['reviewedOn'])
    revisit = date.fromisoformat(record['reevaluateOn'])
    month = reviewed.month + 6
    year = reviewed.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    maximum = date(year, month, min(reviewed.day, calendar.monthrange(year, month)[1]))
    if reviewed > today or not reviewed < revisit <= maximum:
        raise ValueError('Climbing review must occur within six months')
    due(record['reevaluateOn'], today)


def validate(entry, policy, identifiers, today):
    legacy = policy['ladder'].get('legacy', {}).get(entry['id'])
    if not runtime(entry):
        if legacy and fingerprint(entry) != legacy['sha256']:
            raise ValueError('Changed legacy runtime requires full ADR-0054 records')
        return
    for term in identifiers:
        if any(fnmatch.fnmatchcase(term, p) for p in policy['ladder']['never']):
            raise ValueError('Never licence cannot enter a legacy baseline: ' + term)
    grade = entry.get('enterpriseGrade', {})
    if legacy and grade.get('status') == 'legacy-pending':
        if fingerprint(entry) != legacy['sha256'] or entry.get('tier') != legacy['tier']:
            raise ValueError('Changed legacy runtime requires full ADR-0054 records')
        if grade.get('due') != legacy['due']:
            raise ValueError('Legacy backfill deadline cannot be extended')
        due(grade['due'], today)
        return
    expected = tier_for(identifiers, policy)
    if entry.get('tier') != expected:
        raise ValueError('Missing/incorrect ADR-0054 runtime tier')
    if grade.get('status')=='pending':
        raise ValueError('Enterprise-grade qualification pending: '+', '.join(k for k,v in grade.get('criteria',{}).items() if v.get('result')!='pass'))
    if grade.get('status') != 'verified' or set(grade.get('criteria', {})) != set(CRITERIA):
        raise ValueError('Runtime entry requires all enterprise-grade criteria')
    for record in grade['criteria'].values():
        evidence(record, today)
    if expected >= 3:
        if entry.get('approvedBy') != 'amazen33':
            raise ValueError('Tier 3/4 requires component owner approval')
        if not entry.get('unmodified') or not entry.get('separateUnit') or not entry.get('notice'):
            raise ValueError('Tier 3/4 must be unmodified, separate and carry notices/source offer')
        if expected == 4 and entry['class'] != 'exception':
            raise ValueError('Tier 4 requires an exception')
        climbing(entry, today)
