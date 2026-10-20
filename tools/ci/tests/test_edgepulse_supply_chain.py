"""Synthetic planted violations plus actual EdgePulse inventory/permission guards."""
import copy
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))
import edgepulse_supply_chain as ep
import supply_chain as sc
import yaml

ON = date(2026, 10, 20)
EMPTY = {'version':1, 'exceptions':[]}
KEV = {'catalogVersion':'2026.10.20', 'vulnerabilities':[]}


def finding(level='Critical', fix=True):
    return sc.finding('maven:services/identity/pom.xml', 'SYNTHETIC-group:SYNTHETIC-artifact', '1.0',
                      ['CVE-2099-12345'], level, fix, 'osv', True, ['2.0'] if fix else [])


def result(value):
    return dict(findings=[value], inventory={'images':[], 'coverage':[]})


class PlantedViolations(unittest.TestCase):
    def test_kev_blocks_even_with_a_matched_exception(self):
        v = finding('Low', False)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schema = root/'security/vulnerability-exceptions.schema.json'
            schema.parent.mkdir(parents=True)
            schema.write_bytes((ep.ROOT/'security/vulnerability-exceptions.schema.json').read_bytes())
            path = 'security/evidence/vulnerability-exceptions/synthetic.md'
            file = root/path
            file.parent.mkdir(parents=True)
            file.write_text('SYNTHETIC evidence only. Reachability: synthetic call path, no environment.', encoding='utf-8')
            exception = {k:v[k] for k in ('target','package','version','vulnerability','severity')}
            exception.update(owner='SYNTHETIC-owner', approvedBy='SYNTHETIC-owner',
                             createdOn=ON.isoformat(), expires=(ON+timedelta(days=10)).isoformat(),
                             reason='SYNTHETIC recorded mitigation for a planted test only.', controls=[path])
            report = ep.evaluate(result(v), {'version':1, 'exceptions':[exception]},
                                 KEV|{'vulnerabilities':[{'cveID':'CVE-2099-12345'}]}, root, on=ON)
            self.assertEqual(report['status'], 'failed')
            self.assertEqual(report['findings'][0]['blockReason'], 'KEV')

    def test_expired_exception_fails(self):
        v = finding()
        exception = {k:v[k] for k in ('target','package','version','vulnerability','severity')}
        exception.update(owner='SYNTHETIC-owner', approvedBy='SYNTHETIC-owner', workOrder='WO-99',
                         createdOn='2026-09-01', expires='2026-09-10', reason='SYNTHETIC expired test evidence.')
        with self.assertRaisesRegex(ValueError, 'Expired/invalid exception lifetime'):
            ep.evaluate(result(v), {'version':1,'exceptions':[exception]}, KEV, ep.ROOT, on=ON)

    def test_exception_without_evidence_fails(self):
        v = finding()
        exception = {k:v[k] for k in ('target','package','version','vulnerability','severity')}
        exception.update(owner='SYNTHETIC-owner', approvedBy='SYNTHETIC-owner', workOrder='WO-99',
                         createdOn=ON.isoformat(), expires='2026-11-01', reason='SYNTHETIC reason without evidence.')
        with self.assertRaisesRegex(ValueError, 'Exception requires evidence'):
            ep.evaluate(result(v), {'version':1,'exceptions':[exception]}, KEV, ep.ROOT, on=ON)

    def test_image_without_digest_fails(self):
        for ref in ['thingsboard/tb-node:latest', 'SYNTHETIC/image:1.0', 'ghcr.io/example/image@sha256:123']:
            with self.subTest(ref=ref), self.assertRaisesRegex(ValueError, 'without an immutable digest'):
                ep.canonical(ref)

    def test_maven_critical_without_exception_fails_for_critical_fix(self):
        report = ep.evaluate(result(finding()), EMPTY, KEV, ep.ROOT, on=ON)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['findings'][0]['blockReason'], 'Critical with fix')
        self.assertEqual(report['proposedExceptions'], EMPTY)

    def test_evidence_only_backfill_passes(self):
        sys.path.insert(0, str(ep.ROOT/'security'))
        from licence_ladder import fingerprint
        old = {'id':'SYNTHETIC-image', 'version':'sha256:'+'a'*64, 'class':'allowed', 'spdx':'Apache-2.0',
               'tier':2, 'enterpriseGrade':{'status':'legacy-pending', 'due':'2027-04-20'}}
        new = copy.deepcopy(old)|{'imageSBOM':{'path':'target/SYNTHETIC.cdx.json','sha256':'b'*64}}
        before = {'sha256':fingerprint(old),'tier':2,'due':'2027-04-20'}
        after = before|{'sha256':fingerprint(new)}
        ep.evidence_only(old, new, before, after)

    def test_image_sbom_cannot_hide_a_changed_field_or_deadline(self):
        sys.path.insert(0, str(ep.ROOT/'security'))
        from licence_ladder import fingerprint
        old = {'id':'SYNTHETIC-image', 'name':'SYNTHETIC/image', 'version':'sha256:'+'a'*64,
               'class':'allowed', 'spdx':'Apache-2.0', 'tier':2,
               'enterpriseGrade':{'status':'legacy-pending','due':'2027-04-20'}}
        before = {'sha256':fingerprint(old),'tier':2,'due':'2027-04-20'}
        for key in old:
            new = copy.deepcopy(old)|{'imageSBOM':{'path':'target/SYNTHETIC.cdx.json','sha256':'b'*64}}
            new[key] = 'SYNTHETIC-changed'
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Non-evidence field changed'):
                ep.evidence_only(old, new, before, before|{'sha256':fingerprint(new)})
        new = copy.deepcopy(old)|{'imageSBOM':{'path':'target/SYNTHETIC.cdx.json','sha256':'b'*64}}
        with self.assertRaisesRegex(ValueError, 'Legacy tier or due date changed'):
            ep.evidence_only(old,new,before, before|{'sha256':fingerprint(new),'due':'2027-04-21'})


class RepositoryWiring(unittest.TestCase):
    def test_actual_legacy_records_obey_the_evidence_only_ruling(self):
        self.assertLessEqual(len(ep.verify_backfill(ep.ROOT)), 7)

    def test_every_current_image_is_covered_by_immutable_inventory(self):
        plan = ep.inventory(ep.ROOT)
        self.assertEqual(len(plan['images']), 7)
        expected = set(ep.image_references(ep.ROOT))
        self.assertEqual({i['target'] for i in plan['images']}, expected)
        for item in plan['images']:
            self.assertRegex(item['digest'], r'^sha256:[a-f0-9]{64}$')
            self.assertEqual(item['platform'], 'linux/amd64')

    def test_only_nightly_reporter_has_issue_write(self):
        for path in (ep.ROOT/'.github/workflows').glob('*.yaml'):
            raw = path.read_text(encoding='utf-8')
            if 'supply-chain' not in path.name:
                continue
            flow = yaml.safe_load(raw)
            self.assertNotIn('pull_request_target', raw)
            for name, job in flow['jobs'].items():
                if job.get('permissions',{}).get('issues') == 'write':
                    self.assertEqual(path.name, 'supply-chain.yaml')
                    self.assertEqual(name, 'report-issue')
                    self.assertEqual(job['permissions'], {'issues':'write'})
                    self.assertIn("github.ref == 'refs/heads/main'", job['if'])
                    self.assertNotIn('stage_tools.py', json.dumps(job))
                    self.assertNotIn('edgepulse_supply_chain.py', json.dumps(job))
                for step in job['steps']:
                    if 'uses' in step:
                        self.assertRegex(step['uses'], r'^[\w.-]+/[\w.-]+@[a-f0-9]{40}$')
                self.assertNotIn('secrets.', json.dumps(job))

    def test_scanner_lock_versions_match_the_port_and_cool_off(self):
        lock = sc.read(ep.ROOT/'security/toolchain.lock.json')
        self.assertEqual({k:lock['artifacts'][k]['version'] for k in sc.TOOLS},
                         {'syft':'1.52.0','grype':'0.119.0','osv-scanner':'2.6.0'})
        for name in sc.TOOLS:
            self.assertGreaterEqual((ON-date.fromisoformat(lock['artifacts'][name]['published'])).days, 14)

    def test_maven_scans_each_bom_with_no_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            docs = [dict(path=str(out/'SYNTHETIC.cdx.json'), module='services/identity/pom.xml')]
            def run(command, destination, **kwargs):
                self.assertIn('--no-resolve', command)
                self.assertEqual(command[command.index('--sbom')+1], docs[0]['path'])
                sc.write(destination, {'results':[]})
            with patch.object(ep,'maven_inputs',return_value=docs),patch.object(sc,'run',side_effect=run):
                self.assertEqual(ep.scan_maven(ep.ROOT,{'osv-scanner':'SYNTHETIC-scanner'},out), [])


if __name__ == '__main__':
    unittest.main()
