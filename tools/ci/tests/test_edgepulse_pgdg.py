"""IOT-WO-02 Amendment 7 (proposed): regression tests for the PGDG coverage probe.

The fixture mirrors the CNPG trixie image's dpkg records (gate run 45132416685):
PGDG postgresql-18 packages that Grype's dpkg pass never matched.
Scanner output is synthetic; no image, registry or database is used.
"""
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

CI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CI))
import edgepulse_pgdg as pgdg
import edgepulse_supply_chain as ep
import supply_chain as sc

DIGEST = 'sha256:'+'a'*64
TARGET = 'ghcr.io/synthetic/postgresql@'+DIGEST
AFFECTED = 'CVE-2099-12345'


def artifact(identifier, name, version, source=''):
    return dict(id=identifier, name=name, version=version, type='deb',
                metadata=dict(package=name, source=source, version=version))


def sbom():
    return dict(
        schema=dict(version='16.0.0'), source=dict(type='image', name='ghcr.io/synthetic/postgresql'),
        distro=dict(id='debian', versionID='13.7'), files=[{'id': 'SYNTHETIC-file'}],
        artifacts=[
            artifact('p1', 'postgresql-18', '18.6-1.pgdg13+2'),
            artifact('p2', 'postgresql-client-18', '18.6-1.pgdg13+2', 'postgresql-18'),
            artifact('p3', 'libpq5', '18.6-1.pgdg13+2', 'postgresql-18'),
            artifact('p4', 'postgresql-common', '293.pgdg13+1'),
            artifact('p5', 'libc6', '2.41-12+deb13u4', 'glibc'),
        ],
        artifactRelationships=[dict(parent='p1', child='p2', type='dependency-of'),
                               dict(parent='p1', child='p5', type='dependency-of')])


def grype_match(name, version, vulnerability, fix, namespace):
    return dict(artifact=dict(name=name, version=version, type='deb'),
                vulnerability=dict(id=vulnerability, severity='High', namespace=namespace,
                                   fix=dict(state='fixed', versions=[fix])),
                matchDetails=[dict(type='cpe-match' if namespace.startswith('nvd') else 'exact-direct-match')])


class Scanner:
    """Synthetic pinned-Grype stand-in: 18.6 affected, 18.7 fixed, no trixie rows."""

    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def __call__(self, command, output=None, allowed=(0,), env=None, target=None, diagnostic=None):
        self.calls.append(dict(command=[str(x) for x in command], env=env, target=target))
        if self.fail:
            raise sc.ScannerCommandError('grype', 1, target)
        args = [str(x) for x in command[1:]]
        if args[:2] == ['db', 'search']:
            value = [dict(vulnerability=dict(id=AFFECTED), packages=[
                dict(os=dict(name='debian', version='14'), package=dict(name='postgresql-18')),
                dict(cpe='cpe:2.3:a:postgresql:postgresql:*:*:*:*:*:*:*:*')])]
        elif args[0] == pgdg.cpe('18.6'):
            value = dict(matches=[grype_match('postgresql', '18.6', AFFECTED, '18.7', 'nvd:cpe')])
        elif args[0].startswith('cpe:'):
            value = dict(matches=[])
        elif args[0].startswith('sbom:') and '--distro' in args:
            value = dict(matches=[grype_match('postgresql-18', '18.6-1.pgdg13+2', AFFECTED, '18.7-1',
                                              'debian:distro:debian:14')])
        else:
            raise AssertionError('unexpected scanner command: '+' '.join(args))
        sc.write(output, value)


def gate_outputs(out):
    key = DIGEST.split(':')[1]
    sc.write(out/'sboms'/(key+'.syft.json'), sbom())
    # The real dpkg pass: trixie records match glibc but nothing for postgresql-18.
    sc.write(out/(key+'.grype.json'), dict(distro=dict(name='debian', version='13.7'), matches=[
        grype_match('libc6', '2.41-12+deb13u4', 'CVE-2099-23456', '2.41-12+deb13u5', 'debian:distro:debian:13')]))
    return dict(images=[dict(target=TARGET, digest=DIGEST)])


class PgdgCoverage(unittest.TestCase):
    def test_pgdg_server_packages_group_by_source_with_upstream_minor(self):
        groups, other = pgdg.packages(sbom())
        self.assertEqual([(g['source'], g['version'], g['upstream'], g['packages']) for g in groups],
                         [('postgresql-18', '18.6-1.pgdg13+2', '18.6', ['libpq5', 'postgresql-18', 'postgresql-client-18'])])
        self.assertEqual([v['name'] for v in other], ['postgresql-common'])
        self.assertEqual(pgdg.cpe('18.6'), 'cpe:2.3:a:postgresql:postgresql:18.6:*:*:*:*:*:*:*')

    def test_unrecognised_pgdg_packages_are_reported_not_guessed(self):
        value = sbom()
        value['artifacts'] = [artifact('x1', 'postgresql-18-pgvector', '0.8.1-2.pgdg13+1', 'pgvector'),
                              artifact('x2', 'postgresql-17', '18.6-1.pgdg13+2')]
        groups, other = pgdg.packages(value)
        self.assertEqual(groups, [])
        self.assertEqual([v['name'] for v in other], ['postgresql-17', 'postgresql-18-pgvector'])

    def test_probe_locates_the_loss_and_shows_affected_18_6_and_fixed_18_7(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            plan = gate_outputs(out)
            scanner = Scanner()
            with patch.object(sc, 'run', side_effect=scanner):
                value = pgdg.probe(plan, {'grype': 'SYNTHETIC-grype'}, out)
            group = value['images'][0]['groups'][0]
            # Exactly where coverage is lost: the dpkg pass has no trixie rows.
            self.assertEqual(group['dpkgPassMatches'], {'libpq5': 0, 'postgresql-18': 0, 'postgresql-client-18': 0})
            self.assertEqual(group['status'], 'lost in the dpkg pass')
            self.assertEqual(value['databaseSearches']['postgresql-18'], {'cpe': 1, 'debian:14': 1})
            self.assertIn('searches only debian:13, which holds 0 vulnerability records', group['lossPoint'])
            # Known affected 18.6 case and fixed 18.7 case through the same pinned scanner.
            route = group['upstreamCpeRoute']
            self.assertEqual(list(route['vulnerabilities']), [AFFECTED])
            self.assertEqual(route['vulnerabilities'][AFFECTED]['fixVersions'], ['18.7'])
            self.assertEqual(route['fixedControls'], [dict(version='18.7', matches=0, stillAffected=[])])
            self.assertEqual(group['debianRoute']['vulnerabilities'][AFFECTED]['fixVersions'], ['18.7-1'])
            # The Debian route scans only the PGDG server-source subset.
            subset = sc.read(out/'pgdg'/(DIGEST.split(':')[1]+'.postgresql-18.syft.json'))
            self.assertEqual(sorted(a['name'] for a in subset['artifacts']),
                             ['libpq5', 'postgresql-18', 'postgresql-client-18'])
            self.assertEqual(subset['artifactRelationships'], [dict(parent='p1', child='p2', type='dependency-of')])
            self.assertEqual(value['images'][0]['otherPgdgPackages'][0]['dpkgPassMatches'], 0)
            self.assertTrue((out/'pgdg-coverage.json').is_file())
            # Pinned binary and the scan's own database snapshot; never an update.
            for call in scanner.calls:
                self.assertEqual(call['command'][0], 'SYNTHETIC-grype')
                self.assertNotIn('update', call['command'])
                self.assertEqual(call['env']['GRYPE_DB_AUTO_UPDATE'], 'false')
                self.assertEqual(call['env']['GRYPE_DB_CACHE_DIR'], str((out/'database').resolve()))

    def test_scanner_errors_are_recorded_and_never_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            plan = gate_outputs(out)
            with patch.object(sc, 'run', side_effect=Scanner(fail=True)):
                value = pgdg.probe(plan, {'grype': 'SYNTHETIC-grype'}, out)
            group = value['images'][0]['groups'][0]
            self.assertIn('error', value['databaseSearches']['postgresql-18'])
            self.assertIn('error', group['upstreamCpeRoute'])
            self.assertIn('error', group['debianRoute'])
            self.assertIn('an unknown number of', group['lossPoint'])
            self.assertIn('error: Scanner command failed: grype', pgdg.markdown(dict(pgdgCoverage=value)))

    def test_gate_report_shows_the_probe_without_changing_findings_or_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            plan = gate_outputs(out)
            with patch.object(sc, 'run', side_effect=Scanner()):
                coverage = pgdg.probe(plan, {'grype': 'SYNTHETIC-grype'}, out)
            report = dict(status='passed', findings=[], inventory=dict(images=[], coverage=[]),
                          testHarness=dict(staleness=[], targets=[]),
                          proposedExceptions=dict(version=1, exceptions=[]), pgdgCoverage=coverage)
            with patch.dict(os.environ):
                os.environ.pop('GITHUB_STEP_SUMMARY', None)
                ep.report_files(report, out)
            text = (out/'report.md').read_text(encoding='utf-8')
            self.assertIn('## PGDG PostgreSQL coverage probe (report-only)', text)
            self.assertIn('Coverage loss for `postgresql-18 18.6-1.pgdg13+2`', text)
            self.assertIn('18.7: 0 still affected', text)
            saved = json.loads((out/'report.json').read_text(encoding='utf-8'))
            self.assertEqual((saved['status'], saved['findings']), ('passed', []))
        self.assertEqual(pgdg.markdown(dict(findings=[])), '')

    def test_gate_run_invokes_the_probe_as_report_only(self):
        source = inspect.getsource(ep.run)
        self.assertIn('pgdg.probe(plan, tools, out)', source)
        self.assertIn("report['pgdgCoverage'] = coverage", source)
        self.assertNotIn("coverage['", source.split("report['pgdgCoverage'] = coverage")[0].split('pgdg.probe')[1])


if __name__ == '__main__':
    unittest.main()
