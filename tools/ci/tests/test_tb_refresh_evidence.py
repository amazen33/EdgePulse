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
        sbom = dict(artifacts=[jar('SYNTHETIC-embed', '2.0.1'), jar('SYNTHETIC-embed', '2.0.1'),
                               deb('SYNTHETIC-jdk', '1.1'), deb('SYNTHETIC-embed', '9.9')])
        self.assertEqual({'java-archive:SYNTHETIC-embed': ['2.0.1'], 'deb:SYNTHETIC-jdk': ['1.1'],
                          'deb:SYNTHETIC-absent': []}, tb.candidate_packages(sbom, record))

    def test_planted_second_bundled_copy_fails_exact_proof(self):
        record = dict(expectedPackages={'java-archive:SYNTHETIC-embed': '2.0.1'})
        with self.assertRaisesRegex(ValueError, 'java-archive:SYNTHETIC-embed'):
            tb.candidate_packages(dict(artifacts=[jar('SYNTHETIC-embed', '2.0.1'), jar('SYNTHETIC-embed', '2.0.0')]),
                                  record)

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

if __name__ == '__main__':
    unittest.main()
