"""IOT-WO-08 Amendments 2/3: Linux-only TB comparison; no exception activation."""
from collections import Counter
import argparse
import json
from pathlib import Path
import sys

import edgepulse_supply_chain as ep
import supply_chain as sc

ROOT = Path(__file__).resolve().parents[2]
REVIEW = 'security/evidence/iot-wo-08/tb-4.3.1.8-qualification-2026-10-30.json'


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
                 netImprovement=not added and len(identities(after)) < len(identities(before)))
    return value


def candidate_packages(sbom):
    packages = {v['name']: v['version'] for v in sbom['artifacts'] if v['type'] == 'deb'}
    # This is an exact-digest assessment, not an admission of arbitrary future versions.
    if packages.get('libbrotli1') != '1.1.0-2+deb13u1':
        raise ValueError('Approved TB candidate does not contain the reviewed fixed Brotli package')
    for name in ('openjdk-25-jdk-headless', 'openjdk-25-jre-headless'):
        if packages.get(name) != '25.0.4.1+1-1~deb13u1':
            raise ValueError('OpenJDK proposal differs from the actual candidate package: '+name)
    return {k: packages[k] for k in ('libbrotli1', 'openjdk-25-jdk-headless', 'openjdk-25-jre-headless')}


def run(root, tools_path, out, cache):
    if sys.platform != 'linux':
        raise ValueError('Full TB image comparison requires Linux; no Windows substitute')
    review = sc.read(root/REVIEW)
    candidate, baseline = (ep.canonical(review[k]) for k in ('candidate', 'baseline'))
    if {v.split('@')[0] for v in (candidate, baseline)} != {'docker.io/thingsboard/tb-node'}:
        raise ValueError('TB evidence must compare the same approved upstream repository')
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
    packages = candidate_packages(sc.read(out/'sboms'/(digest+'.syft.json')))
    comparison = compare(result)
    comparison.update(candidate=candidate, baseline=baseline, packages=packages,
                      database=result['database'], date=sc.today().isoformat(),
                      toolVersions=ep.scanner_metadata(root), scope=plan['scope'])
    sc.write(out/'net-improvement.json', comparison)
    # Preserve complete comparison output even if admission still fails.
    ep.canonical_sboms(plan, out)
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
    parser.add_argument('--tools', type=Path, default=ROOT/'target/scan-tools/bin')
    parser.add_argument('--out', type=Path, default=ROOT/'target/tb-refresh')
    parser.add_argument('--cache', type=Path, default=ROOT/'target/supply-chain-cache')
    args = parser.parse_args()
    try:
        return run(args.root, args.tools, args.out, args.cache)
    except (ValueError, KeyError, OSError) as error:
        print('TB evidence failure: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
