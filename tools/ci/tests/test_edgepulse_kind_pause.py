from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import edgepulse_harness as h
import edgepulse_kind_pause as pause
import edgepulse_supply_chain as ep
import supply_chain as sc


class KindPause(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ep.ROOT/'target')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.paths = []
        for path in ('security/supply-chain-policy.json', pause.RECORD):
            self.put(path, (ep.ROOT/path).read_text(encoding='utf-8'))
        self.put('.github/workflows/kind-rehearsal.yml', '''permissions: {contents: read}
jobs:
  kind-smoke:
    if: ${{ false }}
    steps:
      - run: ./dev/kind/up.ps1
''')
        self.refs = {e['repository']+'@sha256:'+'a'*64: ['dev/kind/pins.json']
                     for e in h.policy(self.root)['testHarnessImages'] if e['repository'] != pause.REPOSITORY}

    def put(self, path, text):
        p = self.root/path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
        if path not in self.paths:
            self.paths.append(path)

    def guard(self):
        return h.check_references(self.root, self.refs, self.paths)

    def test_only_paused_node_is_absent_from_the_five_image_class(self):
        self.assertEqual(len(h.policy(self.root)['testHarnessImages']), 5)
        self.assertEqual(len(self.guard()['targets']), 4)

    def test_paused_node_in_active_inventory_fails(self):
        self.refs[pause.REPOSITORY+'@sha256:'+'b'*64] = ['dev/kind/pins.json']
        with self.assertRaisesRegex(ValueError, 'must not remain an active image'):
            self.guard()

    def test_paused_node_in_a_workflow_fails(self):
        for prefix in ('', 'docker.io/', 'index.docker.io/', 'registry-1.docker.io/'):
            with self.subTest(prefix=prefix):
                self.put('.github/workflows/other.yml', 'permissions: {contents: read}\njobs:\n  run:\n    steps:\n      - run: docker run '+prefix+'kindest/node@sha256:'+'b'*64)
                with self.assertRaisesRegex(ValueError, 'cannot be executed'):
                    self.guard()

    def test_docker_hub_aliases_resolve_to_the_paused_inventory_identity(self):
        expected = pause.REPOSITORY+'@sha256:'+'b'*64
        for prefix in ('', 'docker.io/', 'index.docker.io/', 'registry-1.docker.io/'):
            with self.subTest(prefix=prefix):
                self.assertEqual(expected, ep.canonical(prefix+'kindest/node@sha256:'+'b'*64))

    def test_reenabled_rehearsal_while_paused_fails(self):
        path = '.github/workflows/kind-rehearsal.yml'
        self.put(path, (self.root/path).read_text().replace('${{ false }}', '${{ true }}'))
        with self.assertRaisesRegex(ValueError, 'explicitly skipped'):
            self.guard()

    def test_shipped_kind_reference_still_fails_during_pause(self):
        self.put('charts/synthetic/values.yaml', 'image: kindest/node@sha256:'+'b'*64)
        with self.assertRaisesRegex(ValueError, 'outside harness/records'):
            self.guard()

    def test_pause_cannot_exclude_another_component_or_extend_restore_duty(self):
        original = sc.read(self.root/pause.RECORD)
        for change in ({'repository':'quay.io/cilium/cilium'}, {'restoreWithinDays':15},
                       {'pausedOn':'2026-10-29'}, {'pausedOn':'2026-11-17'}):
            self.put(pause.RECORD, json.dumps(original | change))
            with patch.object(sc, 'today', return_value=date(2026,11,17)), \
                 self.assertRaisesRegex(ValueError, 'exact owner-approved scope'):
                pause.record(self.root)

    def test_debian_fixed_version_ordering(self):
        minimum = '1.1.0-2+deb13u1'
        for value in ('1.1.0-2+b7', '1.1.0-2+deb13u1~rc1', '1.1.0-1'):
            self.assertFalse(pause.debian_at_least(value, minimum), value)
        for value in (minimum, '1.1.0-2+deb13u2', '1.2.0-1', '1:1.0.0-1'):
            self.assertTrue(pause.debian_at_least(value, minimum), value)
        with self.assertRaisesRegex(ValueError, 'Unverifiable'):
            pause.debian_at_least('SYNTHETIC invalid version', minimum)

    def test_weekly_fixed_publication_starts_clock_without_newer_release_reset(self):
        releases = [dict(tag_name='v0.34.'+str(n), published_at=published, draft=False, prerelease=False,
                         body='kindest/node:v1.36.'+str(5+n)+'@sha256:'+str(n)*64)
                    for n,published in ((1,'2026-10-31T00:00:00Z'),(2,'2026-11-16T00:00:00Z'))]
        def scan(plan, tools, cache, out, root, database):
            item = plan['images'][0]
            sc.write(out/'sboms'/(item['digest'].split(':')[1]+'.syft.json'),
                     dict(artifacts=[dict(type='deb', name='libbrotli1', version='1.1.0-2+deb13u1')]))
            return dict(findings=[], database={'source':'SYNTHETIC'})
        with patch.object(pause.watch, 'releases', return_value=releases), \
             patch.object(sc, 'scan', side_effect=scan), \
             patch.object(sc, 'fetch', return_value=b'{"catalogVersion":"SYNTHETIC", "vulnerabilities":[]}'):
            value = pause.run_watch(self.root, {}, self.root/'out', self.root/'cache', self.root/'db', date(2026,11,17))
        self.assertEqual('2026-10-31', value['fixedAvailableSince'])
        self.assertEqual('2026-11-14', value['restoreBy'])
        self.assertTrue(value['blocked'])
        self.assertEqual(len(value['candidates']), 2)

    def test_unfixed_paused_candidate_is_watched_not_admitted(self):
        release = dict(tag_name='v0.33.0', published_at='2026-08-26T00:00:00Z', draft=False, prerelease=False,
                       body='kindest/node:v1.36.4@sha256:'+'a'*64)
        def scan(plan, tools, cache, out, root, database):
            digest = plan['images'][0]['digest'].split(':')[1]
            sc.write(out/'sboms'/(digest+'.syft.json'),
                     dict(artifacts=[dict(type='deb',name='libbrotli1',version='1.1.0-2+b7')]))
            return dict(findings=[], database={'source':'SYNTHETIC'})
        with patch.object(pause.watch, 'releases', return_value=[release]), \
             patch.object(sc, 'scan', side_effect=scan), \
             patch.object(sc, 'fetch', return_value=b'{"catalogVersion":"SYNTHETIC", "vulnerabilities":[]}'):
            value = pause.run_watch(self.root, {}, self.root/'out', self.root/'cache', self.root/'db', date(2026,10,30))
        self.assertFalse(value['candidates'][0]['fixed'])
        self.assertIsNone(value['restoreBy'])
        self.assertFalse(value['blocked'])
        self.assertIn('not an active gated image', value['scope'])


if __name__ == '__main__':
    unittest.main()
