"""IOT-WO-08 Amendments 2/3: Linux-only TB comparison; no exception activation.

The reviewed record names the exact candidate and baseline digests and the
exact-digest package proof. A record is evidence for one candidate; it never
pins, admits or excepts anything.
"""
from collections import Counter
import argparse
import json
from pathlib import Path
import re
import sys

import edgepulse_supply_chain as ep
import supply_chain as sc

ROOT = Path(__file__).resolve().parents[2]
REVIEW = 'security/evidence/iot-wo-08/tb-4.3.1.9-qualification-2026-11-27.json'
# The 4.3.1.8 record predates expectedPackages; its reviewed proof is kept
# here unchanged (Amendment 2: fixed Brotli, OpenJDK as in the proposals).
REVIEWED_PROOFS = {
    'docker.io/thingsboard/tb-node@sha256:5e2c180f3c48a9f4efd3e19d2f03c41b510ff1a935f25083657e0cf046a94872': {
        'deb:libbrotli1': '1.1.0-2+deb13u1',
        'deb:openjdk-25-jdk-headless': '25.0.4.1+1-1~deb13u1',
        'deb:openjdk-25-jre-headless': '25.0.4.1+1-1~deb13u1'}}
# TB's own application archive inside the image; its version is the release.
TB_APPLICATION = 'pkg:maven/org.thingsboard/application@'
# ADR 0020: TB CE 4.3.x only; 4.4.0 and later (BUSL-1.1) is never a candidate.
CE_RELEASE = re.compile(r'4\.3\.\d+\.\d+')


def identities(values):
    """Match the existing same-component package/advisory carry semantics."""
    return {(v['package'], v['vulnerability']) for v in values
            if v['fixAvailable'] and v['severity'] in ('Critical', 'High')}


def compare(result):
    def distinct(values):
        return list({(v['package'], v.get('version', ''), v['vulnerability']): v for v in values}.values())
    before, after = (distinct(result[k]) for k in ('previousFindings', 'findings'))
    added = sorted(identities(after) - identities(before))
    value = dict(identityFields=['package', 'vulnerability'],
                 before=dict(findings=len(before), severities=dict(Counter(v['severity'] for v in before))),
                 after=dict(findings=len(after), severities=dict(Counter(v['severity'] for v in after))),
                 newFixableCriticalHigh=[dict(package=p, vulnerability=v) for p, v in added],
                 removedFixableCriticalHigh=[dict(package=p, vulnerability=v)
                                            for p, v in sorted(identities(before)-identities(after))],
                 retainedFixableCriticalHigh=[dict(package=p, vulnerability=v)
                                             for p, v in sorted(identities(before) & identities(after))],
                 netImprovement=not added and len(identities(after)) < len(identities(before)))
    return value


def observed_packages(sbom, keys):
    """The version of every copy Syft catalogued for each type:name key, sorted; copies are kept."""
    found = {}
    for artifact in sbom['artifacts']:
        found.setdefault(artifact['type']+':'+artifact['name'], []).append(artifact['version'])
    return {key: sorted(found.get(key, ())) for key in keys}


def expected_packages(review):
    expected = review.get('expectedPackages') or REVIEWED_PROOFS.get(review.get('candidate'))
    if not expected:
        raise ValueError('Candidate record has no exact-digest package proof')
    return expected


def candidate_packages(sbom, review):
    # This is an exact-digest assessment, not an admission of arbitrary future versions:
    # each proven package must appear exactly once, at the reviewed version.
    expected = expected_packages(review)
    packages = observed_packages(sbom, [*expected, *review.get('reportedPackages', [])])
    for key, version in expected.items():
        if packages[key] != [version]:
            raise ValueError('Candidate package differs from the reviewed record: '+key)
    return packages


def check_record(review, candidate, baseline):
    if candidate == baseline or not CE_RELEASE.fullmatch(str(review.get('release'))):
        raise ValueError('TB candidate must be a different Apache-2.0 CE 4.3.x release digest')


def bundled_release(sbom):
    """Versions of every TB application archive Syft catalogued in the image."""
    return sorted(a['version'] for a in sbom['artifacts'] if str(a.get('purl', '')).startswith(TB_APPLICATION))


def check_release(candidate_sbom, baseline_sbom, release):
    """Bind the record's release label to the scanned image, not to the record alone."""
    found, prior = bundled_release(candidate_sbom), bundled_release(baseline_sbom)
    if found != [release]:
        raise ValueError('Candidate image must bundle exactly one TB application '+release+'; found '+repr(found))
    if len(prior) != 1 or not CE_RELEASE.fullmatch(prior[0]) or prior == found:
        raise ValueError('Baseline image must bundle one different TB CE 4.3.x application; found '+repr(prior))
    return dict(candidate=found[0], baseline=prior[0])


def check_proof_coverage(comparison, expected):
    """Every package behind a removed or retained fixable identity needs an exact-version proof."""
    proven = {key.split(':', 1)[1] for key in expected}
    named = {v['package'] for k in ('removedFixableCriticalHigh', 'retainedFixableCriticalHigh')
             for v in comparison[k]}
    if named - proven:
        raise ValueError('Candidate record has no package proof for: '+', '.join(sorted(named - proven)))


def run(root, tools_path, out, cache, review_path=REVIEW):
    if sys.platform != 'linux':
        raise ValueError('Full TB image comparison requires Linux; no Windows substitute')
    review = sc.read(root/review_path)
    candidate, baseline = (ep.canonical(review[k]) for k in ('candidate', 'baseline'))
    if {v.split('@')[0] for v in (candidate, baseline)} != {'docker.io/thingsboard/tb-node'}:
        raise ValueError('TB evidence must compare the same approved upstream repository')
    check_record(review, candidate, baseline)
    origins = ['charts/edgepulse-thingsboard/values.yaml:docker.io/thingsboard/tb-node',
               'dev/kind/pins.json:docker.io/thingsboard/tb-node']
    prior = [dict(target=baseline, source='registry:'+baseline, digest=baseline.split('@')[1],
                  platform='linux/amd64', component=origin) for origin in origins]
    image = dict(target=candidate, source='registry:'+candidate, digest=candidate.split('@')[1],
                 platform='linux/amd64', origins=origins, introduced=True,
                 previousInputs=prior, historicalTargets=[baseline])
    plan = dict(version=1, base='555d9055c01c4f20de07c183d7bd3c272781fcf2',
                images=[image], lockfiles=[], coverage=[], full=False,
                scope='Full baseline and candidate TB images, not the entire platform')
    out.mkdir(parents=True, exist_ok=True)
    result = sc.scan(plan, sc.verify_tools(tools_path, root), cache, out, root=root)
    digest = candidate.split('@sha256:')[1]
    candidate_sbom = sc.read(out/'sboms'/(digest+'.syft.json'))
    baseline_sbom = sc.read(out/'sboms'/(baseline.split('@sha256:')[1]+'.syft.json'))
    bundled = check_release(candidate_sbom, baseline_sbom, review['release'])
    packages = candidate_packages(candidate_sbom, review)
    prior = observed_packages(baseline_sbom, list(packages))
    comparison = compare(result)
    comparison.update(candidate=candidate, baseline=baseline, release=review['release'], bundledRelease=bundled,
                      record=Path(review_path).as_posix(), packages=packages, baselinePackages=prior,
                      database=result['database'], date=sc.today().isoformat(),
                      toolVersions=ep.scanner_metadata(root), scope=plan['scope'])
    sc.write(out/'net-improvement.json', comparison)
    # Preserve complete comparison output even if admission still fails.
    ep.canonical_sboms(plan, out)
    # Records with expectedPackages must prove every package the comparison relies on;
    # the 4.3.1.8 record keeps its original reviewed proof.
    if review.get('expectedPackages'):
        check_proof_coverage(comparison, review['expectedPackages'])
    if not comparison['netImprovement']:
        raise ValueError('TB candidate fails net improvement: new fixable Critical/High identity or no reduction')
    with ep.github_reads():
        state, link = sc.previous_state(ep.REPOSITORY)
    raw = sc.fetch('https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json')
    (out/'kev.json').write_bytes(raw)
    report = ep.evaluate(result, sc.read(root/'security/vulnerability-exceptions.json'),
                         json.loads(raw), root, state if link else None)
    report['trackingIssue'] = link
    report['kev']['downloadSHA256'] = sc.sha(raw)
    report['netImprovement'] = comparison
    report['markdown'] = sc.markdown(report)
    sc.write(out/'report.json', report)
    (out/'report.md').write_text(report['markdown'], encoding='utf-8')
    print('Full Linux TB comparison: net improvement passed; '+str(sum(v['blocked'] for v in report['findings']))
          +' blocking findings; no proposals activated')
    return int(report['status'] != 'passed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--review', default=REVIEW, help='reviewed candidate record, relative to --root')
    parser.add_argument('--tools', type=Path, default=ROOT/'target/scan-tools/bin')
    parser.add_argument('--out', type=Path, default=ROOT/'target/tb-refresh')
    parser.add_argument('--cache', type=Path, default=ROOT/'target/supply-chain-cache')
    args = parser.parse_args()
    try:
        return run(args.root, args.tools, args.out, args.cache, args.review)
    except (ValueError, KeyError, OSError) as error:
        print('TB evidence failure: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
