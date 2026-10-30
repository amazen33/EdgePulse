import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tb_refresh_evidence as tb


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
        with self.assertRaisesRegex(ValueError, 'fixed Brotli'):
            tb.candidate_packages(dict(artifacts=[dict(name='libbrotli1', version='SYNTHETIC-old', type='deb')]))

    def test_proposed_jdk_versions_must_match_the_image(self):
        with self.assertRaisesRegex(ValueError, 'OpenJDK proposal differs'):
            tb.candidate_packages(dict(artifacts=[dict(name='libbrotli1', version='1.1.0-2+deb13u1', type='deb')]))


if __name__ == '__main__':
    unittest.main()
