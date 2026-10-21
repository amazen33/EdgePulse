"""ADR 0028: synthetic class-boundary, KEV and staleness violations."""
import copy
from datetime import date
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import edgepulse_harness as h
import edgepulse_supply_chain as ep
import supply_chain as sc

ON = date(2026, 10, 21)
EMPTY = dict(version=1, exceptions=[])
KEV = dict(catalogVersion='SYNTHETIC-2026-10-21', vulnerabilities=[])


class HarnessPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ep.ROOT/'target')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.paths = []
        self.put('security/supply-chain-policy.json', (ep.ROOT/'security/supply-chain-policy.json').read_text(encoding='utf-8'))
        self.put('security/vulnerability-exceptions.schema.json', (ep.ROOT/'security/vulnerability-exceptions.schema.json').read_text(encoding='utf-8'))
        self.put('dev/kind/pins.json', (ep.ROOT/'dev/kind/pins.json').read_text(encoding='utf-8'))
        self.put('dev/kind/up.ps1', '# SYNTHETIC harness entry point')
        self.put('.github/workflows/synthetic.yml', '''permissions: {contents: read}
jobs:
  harness:
    runs-on: ubuntu-24.04
    steps:
      - run: ./dev/kind/up.ps1
''')
        self.refs = {e['repository']+'@sha256:'+'a'*64:['dev/kind/pins.json']
                     for e in h.policy(self.root)['testHarnessImages']}

    def put(self, path, value):
        file = self.root/path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value, encoding='utf-8')
        if path not in self.paths:
            self.paths.append(path)

    def guard(self):
        return h.check_references(self.root, self.refs, self.paths)

    def flow(self, change):
        import yaml
        path = '.github/workflows/synthetic.yml'
        value = yaml.safe_load((self.root/path).read_text(encoding='utf-8'))
        change(value['jobs']['harness'])
        self.put(path, yaml.safe_dump(value))

    def report(self, severity='High', kev=False, checks=None, target=None):
        target = target or next(iter(self.refs))
        finding = sc.finding(target, 'SYNTHETIC-package', '1.0', ['CVE-2099-12345'], severity, True, 'grype', True, ['2.0'])
        return ep.evaluate(dict(findings=[finding], inventory=dict(images=[], coverage=[])), EMPTY,
                           KEV | dict(vulnerabilities=[dict(cveID='CVE-2099-12345')] if kev else []),
                           self.root, on=ON, harness_guard=self.guard(), staleness=checks or [])

    def test_harness_in_chart_fails_even_when_inventory_misses_template(self):
        self.put('charts/synthetic/templates/job.yaml', 'image: kindest/node@sha256:'+'a'*64)
        with self.assertRaisesRegex(ValueError, 'outside harness/records'):
            self.guard()

    def test_harness_pin_file_reused_by_packaging_fails(self):
        self.put('charts/synthetic/values.yaml', 'source: dev/kind/pins.json')
        with self.assertRaisesRegex(ValueError, 'reused by packaging'):
            self.guard()

    def test_documentation_link_does_not_package_a_harness_image(self):
        self.put('charts/synthetic/README.md', '[Harness](../../dev/kind/README.md)')
        self.assertEqual(len(self.guard()['targets']), 5)

    def test_structured_shipped_reference_fails(self):
        self.refs[next(iter(self.refs))].append('charts/synthetic/values.yaml')
        with self.assertRaisesRegex(ValueError, 'in shipped input'):
            self.guard()

    def test_contents_write_fails(self):
        self.flow(lambda job:job.update(permissions={'contents':'write'}))
        with self.assertRaisesRegex(ValueError, 'only contents: read'):
            self.guard()

    def test_extra_permission_fails(self):
        self.flow(lambda job:job.update(permissions={'contents':'read', 'issues':'write'}))
        with self.assertRaisesRegex(ValueError, 'only contents: read'):
            self.guard()

    def test_repository_secret_fails(self):
        self.flow(lambda job:job.update(env={'SYNTHETIC_INPUT':'${{ secrets.SYNTHETIC_VALUE }}'}))
        with self.assertRaisesRegex(ValueError, 'cannot receive secrets'):
            self.guard()

    def test_environment_fails(self):
        self.flow(lambda job:job.update(environment='SYNTHETIC-environment'))
        with self.assertRaisesRegex(ValueError, 'cannot receive secrets'):
            self.guard()

    def test_indirect_script_and_reusable_workflow_callers_are_guarded(self):
        self.put('tools/synthetic.ps1', './dev/kind/up.ps1')
        self.flow(lambda job:job.update(steps=[{'run':'./tools/synthetic.ps1'}],permissions={'contents':'write'}))
        with self.assertRaisesRegex(ValueError, 'only contents: read'):
            self.guard()
        self.flow(lambda job:job.update(permissions={'contents':'read'}))
        self.put('.github/workflows/caller.yml', '''permissions: {contents: write}
jobs:
  caller:
    uses: ./.github/workflows/synthetic.yml
''')
        with self.assertRaisesRegex(ValueError, 'only contents: read'):
            self.guard()

    def test_kev_in_harness_blocks(self):
        report = self.report(kev=True)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['findings'][0]['blockReason'], 'KEV')

    def test_fixed_high_and_critical_are_report_only_with_first_seen(self):
        for severity in ('High', 'Critical'):
            report = self.report(severity)
            self.assertEqual(report['status'], 'passed')
            value = report['findings'][0]
            self.assertEqual(value['firstSeen'], ON.isoformat())
            self.assertFalse(value['blocked'])
            self.assertIsNone(value['exception'])
            self.assertIn('ADR 0028', value['reportOnlyReason'])
            self.assertIn(ON.isoformat(), h.markdown(report))

    def test_shipped_critical_stays_strict(self):
        report = self.report('Critical', target='SYNTHETIC-shipped@sha256:'+'b'*64)
        self.assertEqual(report['status'], 'failed')
        self.assertNotIn('imageClass', report['findings'][0])

    def test_stale_harness_blocks_even_without_vulnerabilities(self):
        guard = self.guard()
        report = self.report(checks=[dict(target=guard['targets'][0],blocked=True)])
        self.assertEqual(report['status'], 'failed')
        self.assertFalse(report['findings'][0]['blocked'])

    def test_live_metadata_staleness_eligibility_and_exact_owner_reason(self):
        pins = sc.read(self.root/'dev/kind/pins.json')
        def releases(repo, memo):
            family = {'kubernetes-sigs/kind':'kind', 'cilium/cilium':'cilium', 'cloudnative-pg/cloudnative-pg':'cnpg'}[repo]
            current = pins[family]['version']
            tag = 'v'+current.rsplit('.',1)[0]+'.99'
            return [dict(tag_name=tag, published_at='2026-09-01T00:00:00Z', draft=False, prerelease=False,
                         body='kindest/node:v1.36.99@sha256:'+'b'*64)]
        with patch.object(h.watch, 'releases', side_effect=releases):
            checks = h.release_checks(self.root, self.guard()['targets'], ON)
            self.assertTrue(all(c['blocked'] for c in checks))
            policy = h.policy(self.root)
            c = checks[0]
            policy['ownerReasons'] = [dict(repository=c['target'].split('@')[0],release=c['newestEligibleRelease'],
                                          owner='amazen33', date=ON.isoformat(),reason='SYNTHETIC dated owner decision')]
            self.put('security/supply-chain-policy.json', json.dumps(policy))
            updated = h.release_checks(self.root, self.guard()['targets'], ON)
            self.assertEqual(sum(c['blocked'] for c in updated), 4)
        with patch.object(h.watch, 'releases', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'no verifiable eligible'):
                h.release_checks(self.root, self.guard()['targets'], ON)

    def test_fourteen_day_cooloff_and_thirty_day_boundary(self):
        pins = sc.read(self.root/'dev/kind/pins.json')
        for published, blocked in [('2026-09-21T00:00:00Z', False), ('2026-09-20T23:59:59Z', True)]:
            def releases(repo, memo):
                family = {'kubernetes-sigs/kind':'kind', 'cilium/cilium':'cilium', 'cloudnative-pg/cloudnative-pg':'cnpg'}[repo]
                current = pins[family]['version']
                return [dict(tag_name='v'+current.rsplit('.',1)[0]+'.99', published_at=published, draft=False, prerelease=False,
                             body='kindest/node:v1.36.99@sha256:'+'b'*64),
                        dict(tag_name='v'+current.rsplit('.',1)[0]+'.100', published_at='2026-10-20T00:00:00Z', draft=False, prerelease=False,
                             body='kindest/node:v1.36.100@sha256:'+'c'*64)]
            with self.subTest(published=published), patch.object(h.watch, 'releases', side_effect=releases):
                checks = h.release_checks(self.root, self.guard()['targets'], ON)
                self.assertTrue(all(c['blocked'] == blocked for c in checks))
                self.assertTrue(all(c['newestEligibleRelease'].endswith('.99') for c in checks))

    def test_new_release_does_not_reset_older_unadopted_release_clock(self):
        pins = sc.read(self.root/'dev/kind/pins.json')
        def releases(repo, memo):
            family = {'kubernetes-sigs/kind':'kind', 'cilium/cilium':'cilium', 'cloudnative-pg/cloudnative-pg':'cnpg'}[repo]
            current = pins[family]['version']
            return [dict(tag_name='v'+current.rsplit('.',1)[0]+'.'+patch, published_at=published,
                         draft=False, prerelease=False, body='kindest/node:v1.36.'+patch+'@sha256:'+'b'*64)
                    for patch, published in [('98','2026-09-01T00:00:00Z'),('99','2026-10-01T00:00:00Z')]]
        with patch.object(h.watch, 'releases', side_effect=releases):
            checks = h.release_checks(self.root, self.guard()['targets'], ON)
        self.assertTrue(all(c['newestEligibleRelease'].endswith('.99') and c['blocked'] for c in checks))
        self.assertTrue(all(c['overdueReleases'][0]['release'].endswith('.98') for c in checks))

    def test_report_writer_keeps_ported_formatter_unchanged(self):
        report = self.report()
        original = sc.markdown
        ep.report_files(report, self.root/'out')
        self.assertIs(sc.markdown, original)
        stored = sc.read(self.root/'out/report.json')
        self.assertTrue(stored['markdown'].startswith('## ADR 0028'))
        self.assertEqual(stored['firstSeen'], report['firstSeen'])


class HarnessRepository(unittest.TestCase):
    def test_exactly_266_exceptions_removed_and_all_other_entry_bytes_retained(self):
        before = sc.git(ep.ROOT, 'show', 'c126d1e00b345d0721ed08fbcc4e92a87384055d:security/vulnerability-exceptions.json')
        after = (ep.ROOT/'security/vulnerability-exceptions.json').read_text(encoding='utf-8')
        blocks = lambda text:re.findall(r'^    \{\n.*?^    \}', text, re.M | re.S)
        old, new = blocks(before), blocks(after)
        self.assertEqual(len(old), 302)
        names = {v['repository'] for v in h.policy(ep.ROOT)['testHarnessImages']}
        removed = [v for v in old if json.loads(v)['target'].split('@')[0] in names
                   and json.loads(v)['workOrder'] == 'IOT-WO-08']
        self.assertEqual(len(removed), 266)
        self.assertEqual(new, [v for v in old if v not in removed])

    def test_actual_inputs_remain_isolated_and_read_only(self):
        guard = h.check_references(ep.ROOT, ep.image_references(ep.ROOT))
        self.assertEqual(len(guard['targets']), 5)
        self.assertIn('.github/workflows/kind-rehearsal.yml:kind-smoke', guard['readOnlySecretlessJobs'])


if __name__ == '__main__':
    unittest.main()
