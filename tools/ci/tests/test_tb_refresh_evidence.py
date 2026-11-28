from datetime import date
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tb_refresh_evidence as tb


RECORD_4318 = dict(candidate='docker.io/thingsboard/tb-node@sha256:'
                   '5e2c180f3c48a9f4efd3e19d2f03c41b510ff1a935f25083657e0cf046a94872')


def deb(name, version):
    return dict(name=name, version=version, type='deb')


def jar(name, version):
    return dict(name=name, version=version, type='java-archive')


def application(version):
    return dict(name='application', version=version, type='java-archive', purl=tb.TB_APPLICATION+version)


def finding(package='SYNTHETIC-package', advisory='CVE-2099-1000', severity='Critical', fixed=True):
    return dict(package=package, vulnerability=advisory, severity=severity, fixAvailable=fixed)


class TbRefreshEvidenceTests(unittest.TestCase):
    def test_removal_without_new_fixable_identity_is_net_improvement(self):
        value = tb.compare(dict(previousFindings=[finding(), finding(advisory='CVE-2099-1001')],
                                findings=[finding()]))
        self.assertTrue(value['netImprovement'])
        self.assertEqual([], value['newFixableCriticalHigh'])

    def test_planted_new_fixable_high_fails_net_improvement(self):
        value = tb.compare(dict(previousFindings=[finding()],
                                findings=[finding(package='SYNTHETIC-new', severity='High')]))
        self.assertFalse(value['netImprovement'])
        self.assertEqual('SYNTHETIC-new', value['newFixableCriticalHigh'][0]['package'])

    def test_an_unchanged_finding_does_not_prove_improvement(self):
        self.assertFalse(tb.compare(dict(previousFindings=[finding()], findings=[finding()]))['netImprovement'])

    def test_duplicate_scanner_matches_do_not_inflate_before_counts(self):
        value = tb.compare(dict(previousFindings=[finding(), finding()], findings=[]))
        self.assertEqual(1, value['before']['findings'])

    def test_no_fix_report_only_finding_does_not_create_a_fixed_identity(self):
        value = tb.compare(dict(previousFindings=[finding()], findings=[finding(fixed=False)]))
        self.assertTrue(value['netImprovement'])

    def test_planted_unfixed_brotli_fails_package_proof(self):
        with self.assertRaisesRegex(ValueError, 'deb:libbrotli1'):
            tb.candidate_packages(dict(artifacts=[deb('libbrotli1', 'SYNTHETIC-old')]), RECORD_4318)

    def test_proposed_jdk_versions_must_match_the_image(self):
        with self.assertRaisesRegex(ValueError, 'differs from the reviewed record: deb:openjdk-25-jdk-headless'):
            tb.candidate_packages(dict(artifacts=[deb('libbrotli1', '1.1.0-2+deb13u1')]), RECORD_4318)

    def test_record_without_package_proof_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no exact-digest package proof'):
            tb.candidate_packages(dict(artifacts=[]), dict(candidate='SYNTHETIC-unreviewed'))

    def test_record_proof_covers_bundled_java_archives_and_reports_versions(self):
        record = dict(expectedPackages={'java-archive:SYNTHETIC-embed': '2.0.1'},
                      reportedPackages=['deb:SYNTHETIC-jdk', 'deb:SYNTHETIC-absent'])
        sbom = dict(artifacts=[jar('SYNTHETIC-embed', '2.0.1'), deb('SYNTHETIC-jdk', '1.1'),
                               deb('SYNTHETIC-jdk', '1.1'), deb('SYNTHETIC-embed', '9.9')])
        self.assertEqual({'java-archive:SYNTHETIC-embed': ['2.0.1'], 'deb:SYNTHETIC-jdk': ['1.1', '1.1'],
                          'deb:SYNTHETIC-absent': []}, tb.candidate_packages(sbom, record))

    def test_planted_second_bundled_copy_fails_exact_proof(self):
        record = dict(expectedPackages={'java-archive:SYNTHETIC-embed': '2.0.1'})
        for second in ('2.0.0', '2.0.1'):  # a different or an identical second copy
            with self.subTest(second=second), self.assertRaisesRegex(ValueError, 'java-archive:SYNTHETIC-embed'):
                tb.candidate_packages(dict(artifacts=[jar('SYNTHETIC-embed', '2.0.1'), jar('SYNTHETIC-embed', second)]),
                                      record)

    def test_record_guard_rejects_the_same_digest_and_releases_outside_ce_43x(self):
        tb.check_record(dict(release='4.3.1.9'), 'SYNTHETIC-candidate', 'SYNTHETIC-baseline')
        with self.assertRaisesRegex(ValueError, 'different Apache-2.0 CE 4.3.x'):
            tb.check_record(dict(release='4.3.1.9'), 'SYNTHETIC-same', 'SYNTHETIC-same')
        for release in (None, '4.4.0', '4.4.0.0', '4.3.1', '4.3.1.9.1', '14.3.1.9', '4.3.1.9 '):
            with self.subTest(release=release), self.assertRaisesRegex(ValueError, 'different Apache-2.0 CE 4.3.x'):
                tb.check_record(dict(release=release), 'SYNTHETIC-candidate', 'SYNTHETIC-baseline')

    def test_release_label_is_bound_to_the_bundled_tb_application(self):
        baseline = dict(artifacts=[application('4.3.1.8')])
        self.assertEqual(dict(candidate='4.3.1.9', baseline='4.3.1.8'),
                         tb.check_release(dict(artifacts=[application('4.3.1.9')]), baseline, '4.3.1.9'))
        planted = {'mislabelled 4.4 image': [application('4.4.0.0')], 'no application': [],
                   'second application': [application('4.3.1.9'), application('4.3.1.9')]}
        for name, artifacts in planted.items():
            with self.subTest(name), self.assertRaisesRegex(ValueError, 'Candidate image must bundle exactly one'):
                tb.check_release(dict(artifacts=artifacts), baseline, '4.3.1.9')
        for artifacts in ([application('4.3.1.9')], [application('4.4.0.0')], []):
            with self.subTest(baseline=artifacts), self.assertRaisesRegex(ValueError, 'Baseline image must bundle'):
                tb.check_release(dict(artifacts=[application('4.3.1.9')]), dict(artifacts=artifacts), '4.3.1.9')

    def test_record_must_prove_every_removed_and_retained_package(self):
        comparison = tb.compare(dict(previousFindings=[finding(), finding(package='SYNTHETIC-gone')],
                                     findings=[finding()]))
        tb.check_proof_coverage(comparison, {'deb:SYNTHETIC-package': '1', 'java-archive:SYNTHETIC-gone': '2'})
        with self.assertRaisesRegex(ValueError, 'no package proof for: SYNTHETIC-gone$'):
            tb.check_proof_coverage(comparison, {'deb:SYNTHETIC-package': '1'})
        with self.assertRaisesRegex(ValueError, 'no package proof for: SYNTHETIC-package$'):
            tb.check_proof_coverage(comparison, {'java-archive:SYNTHETIC-gone': '2'})

    def test_unchanged_fixable_identity_is_reported_as_retained(self):
        value = tb.compare(dict(previousFindings=[finding(), finding(advisory='CVE-2099-1001')],
                                findings=[finding(), finding(advisory='CVE-2099-1002', fixed=False)]))
        self.assertEqual([dict(package='SYNTHETIC-package', vulnerability='CVE-2099-1000')],
                         value['retainedFixableCriticalHigh'])

    def test_active_record_compares_the_pinned_digest_with_a_43x_candidate(self):
        record = json.loads((tb.ROOT/tb.REVIEW).read_text(encoding='utf-8'))
        pinned = {ref for ref in tb.ep.image_references(tb.ROOT) if ref.startswith('docker.io/thingsboard/tb-node@')}
        self.assertEqual({tb.ep.canonical(record['baseline'])}, pinned)
        self.assertNotEqual(record['candidate'], record['baseline'])
        self.assertRegex(record['release'], r'^4\.3\.\d+\.\d+$')
        self.assertTrue(record['expectedPackages'])

    def test_digest_specific_tomcat_proposal_matches_the_candidate_and_stays_inactive(self):
        # A-9 (proposed): exact counterpart of A-8 on the candidate digest; owner approval by hash.
        path = tb.ROOT/'security/vulnerability-exception-proposals/iot-wo-08-tb-4.3.1.9-tomcat-2026-11-28.json'
        payload = path.read_bytes()
        self.assertEqual(tb.sc.sha(payload), '2257195a05472138602b67014f2b1506560a8f6ef78cd60479ca7bc7e389bd64')
        rows = json.loads(payload)['exceptions']
        record = json.loads((tb.ROOT/tb.REVIEW).read_text(encoding='utf-8'))
        a8 = json.loads((tb.ROOT/'security/vulnerability-exception-proposals/'
                         'iot-wo-08-tb-tomcat-2026-11-27.json').read_text(encoding='utf-8'))['exceptions']
        same = ('vulnerability', 'package', 'version', 'severity', 'owner', 'workOrder', 'approvedBy', 'expires')
        self.assertEqual([{k: v[k] for k in same} for v in a8], [{k: v[k] for k in same} for v in rows])
        self.assertEqual({record['candidate']}, {v['target'] for v in rows})
        for value in rows:
            self.assertEqual(record['expectedPackages']['java-archive:'+value['package']], value['version'])
        self.assertEqual(8, len(rows))
        self.assertEqual([('', '2026-12-23')]*8, [(v['approvedBy'], v['expires']) for v in rows])
        active = json.loads((tb.ROOT/'security/vulnerability-exceptions.json').read_text(encoding='utf-8'))['exceptions']
        self.assertFalse({v['target'] for v in active} & {record['candidate']})
        # An approved copy must pass the unchanged lifetime and evidence checks through the expiry date.
        approved = dict(version=1, exceptions=[v | {'approvedBy': 'SYNTHETIC-approver'} for v in rows])
        for on in ('2026-11-28', '2026-12-23'):
            tb.ep.validate_exception_evidence(approved, tb.ROOT, date.fromisoformat(on))

if __name__ == '__main__':
    unittest.main()
