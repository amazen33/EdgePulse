"""WO-32 offline fixtures: no registry/database access, no scanner/host execution."""
import copy
from datetime import date,timedelta
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import yaml

CI=Path(__file__).resolve().parents[1];ROOT=CI.parents[1]
sys.path.insert(0,str(CI));sys.path.insert(0,str(ROOT/'tools'))
import supply_chain as sc
import supply_chain_watch as watch
import supply_chain_report as reporter
import stage_tools

ON=date(2026,10,13)
BASE='9c33d0c3bdae2447173df3797ec2c8666116992d'
EMPTY={'version':1,'exceptions':[]}
KEV={'catalogVersion':'2026.10.13','vulnerabilities':[]}


def value(severity='High',fix=True,introduced=False):
    return sc.finding('docker.io/example/api@sha256:'+'a'*64,'example','1.0',['GHSA-fixture','CVE-2026-1234'],severity,fix,'fixture',introduced,
                      ['2.0'] if fix else [])


def result(*values):return dict(version=1,date=ON.isoformat(),findings=list(values),inventory=dict(images=[],coverage=[]))


def exception(v,**overrides):
    entry={k:v[k] for k in ('target','package','version','vulnerability','severity')}|dict(
        owner='amazen33',reason='Owner-approved mitigation with a scheduled removal.',approvedBy='amazen33',createdOn=ON.isoformat(),
        expires=(ON+timedelta(days=sc.EXCEPTION_DAYS.get(v['severity'],90))).isoformat())
    if v['fixAvailable']:entry['workOrder']='WO-34'
    return entry|overrides


class Gate(unittest.TestCase):
    def evaluate(self,v,exceptions=EMPTY,kev=KEV,state=None,on=ON,bootstrap=False):
        return sc.evaluate(result(v),exceptions,kev,state,on,bootstrap)

    def test_kev_alias_blocks_even_low_without_fix(self):
        v=value('Low',False);kev=KEV|{'vulnerabilities':[{'cveID':'CVE-2026-1234'}]}
        report=self.evaluate(v,kev=kev)
        self.assertEqual(report['status'],'failed');self.assertEqual(report['findings'][0]['blockReason'],'KEV')

    def test_critical_with_fix_blocks_without_fix_reports(self):
        self.assertEqual(self.evaluate(value('Critical'))['status'],'failed')
        self.assertEqual(self.evaluate(value('Critical',False))['status'],'passed')

    def test_high_introduced_immediate_and_preexisting_day14(self):
        v=value();state={v['key']:'2026-10-01'}
        self.assertEqual(self.evaluate(value(introduced=True))['status'],'failed')
        self.assertEqual(self.evaluate(v,state=state,on=date(2026,10,14))['status'],'passed')
        self.assertEqual(self.evaluate(v,state=state,on=date(2026,10,15))['status'],'failed')

    def test_no_fix_and_medium_only_report(self):
        for severity,fix in [('High',False),('Critical',False),('Medium',True),('Low',True),('Negligible',True)]:
            with self.subTest(severity=severity,fix=fix):self.assertEqual(self.evaluate(value(severity,fix,introduced=True))['status'],'passed')

    def test_missing_issue_uses_fixed_anchor_not_moving_grace(self):
        self.assertEqual(self.evaluate(value(),on=date(2026,10,26))['status'],'passed')
        self.assertEqual(self.evaluate(value(),on=date(2026,10,27))['status'],'failed')

    def test_newly_discovered_risk_in_existing_issue_gets_its_own_first_seen_date(self):
        report=self.evaluate(value(),state={},on=date(2026,11,1))
        self.assertEqual(report['status'],'passed');self.assertEqual(report['findings'][0]['firstSeen'],'2026-11-01')
        self.assertEqual(self.evaluate(value(),state=report['firstSeen'],on=date(2026,11,15))['status'],'failed')

    def test_expired_malformed_and_over90_day_exceptions_fail(self):
        v=value('Critical')
        for fault in ({'expires':'2026-10-12'},{'expires':'2027-01-12'}, {'reason':''},{'createdOn':'bad'}, {'extra':True}):
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                self.evaluate(v,{'version':1,'exceptions':[exception(v,**fault)]})
        with self.assertRaises(ValueError):sc.validate_exceptions({'version':1},on=ON)

    def test_exact_exception_cannot_cover_changed_version(self):
        v=value('Critical');entries={'version':1,'exceptions':[exception(v)]}
        self.assertEqual(self.evaluate(v,entries)['status'],'passed')
        v=v|{'version':'2.0'};self.assertEqual(self.evaluate(v,entries)['status'],'failed')

    def test_critical_high_and_other_expiry_caps_from_created_on(self):
        for level,days in [('Critical',30),('High',60),('Medium',90),('Unknown',90)]:
            v=value(level)
            with self.subTest(severity=level):
                # Creation, not the evaluation date, anchors the maximum lifetime.
                good=exception(v,expires=(ON+timedelta(days=days)).isoformat())
                self.assertEqual(len(sc.validate_exceptions({'version':1,'exceptions':[good]},on=ON+timedelta(days=1))),1)
                bad=good|{'expires':(ON+timedelta(days=days+1)).isoformat()}
                with self.assertRaisesRegex(ValueError,'lifetime'):
                    sc.validate_exceptions({'version':1,'exceptions':[bad]},on=ON+timedelta(days=1))

    def test_grouped_critical_entries_are_rejected(self):
        v=value('Critical');entry=exception(v)
        for fault in ({'vulnerability':['CVE-2026-1234','CVE-2026-5678']},
                      {'vulnerability':'CVE-2026-1234,CVE-2026-5678'},
                      {'vulnerability':'CVE-2026-*'},
                      {'vulnerabilities':['CVE-2026-1234','CVE-2026-5678']},
                      {'target':[v['target'],'docker.io/other@sha256:'+'b'*64]}):
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'Malformed'):
                self.evaluate(v,{'version':1,'exceptions':[entry|fault]})

    def test_fixable_exception_requires_work_order(self):
        v=value('Critical');entry=exception(v);del entry['workOrder']
        with self.assertRaisesRegex(ValueError,'requires workOrder'):
            self.evaluate(v,{'version':1,'exceptions':[entry]})
        for reference in ('', 'WO-34 and WO-35', 'future work'):
            with self.subTest(reference=reference),self.assertRaisesRegex(ValueError,'Malformed'):
                self.evaluate(v,{'version':1,'exceptions':[entry|{'workOrder':reference}]})
        # A no-fix KEV exception can be risk-approved without inventing a patch WO.
        no_fix=value('Low',False);kev=KEV|{'vulnerabilities':[{'cveID':'CVE-2026-1234'}]}
        self.assertEqual(self.evaluate(no_fix,{'version':1,'exceptions':[exception(no_fix)]},kev=kev)['status'],'passed')

    def test_severity_and_owner_required_and_severity_cannot_evade_expiry(self):
        v=value('Critical');entry=exception(v)
        for field in ('severity','owner'):
            missing=dict(entry);del missing[field]
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'Malformed'):
                self.evaluate(v,{'version':1,'exceptions':[missing]})
        with self.assertRaisesRegex(ValueError,'severity differs'):
            self.evaluate(v,{'version':1,'exceptions':[exception(v,severity='High',expires='2026-12-12')]})

    def test_pending_owner_only_original_wo32_pr(self):
        v=value('Critical');entries={'version':1,'exceptions':[exception(v,approvedBy='pending-owner')]}
        with self.assertRaisesRegex(ValueError,'Pending-owner'):self.evaluate(v,entries)
        self.assertEqual(self.evaluate(v,entries,bootstrap=True)['status'],'passed')
        with tempfile.TemporaryDirectory() as tmp:
            event=Path(tmp)/'event.json'
            for name,repo,branch,expected in [('pull_request',sc.REPOSITORY,sc.BOOTSTRAP_BRANCH,True),
                    ('push',sc.REPOSITORY,sc.BOOTSTRAP_BRANCH,False),
                    ('pull_request','fork/twinfra',sc.BOOTSTRAP_BRANCH,False),
                    ('pull_request',sc.REPOSITORY,'other',False)]:
                event.write_text(json.dumps({'pull_request':{'head':{'ref':branch,'repo':{'full_name':repo}}}}))
                with patch.dict(os.environ,{'GITHUB_EVENT_NAME':name,'GITHUB_EVENT_PATH':str(event)}):
                    self.assertEqual(sc.bootstrap_context(),expected)

    def test_proposals_are_real_blockers_fixed_expiry_and_pending(self):
        report=sc.evaluate(result(value('Critical'),value('Low')),EMPTY,KEV,on=ON)
        entries=report['proposedExceptions']['exceptions'];self.assertEqual(len(entries),1)
        self.assertEqual(entries[0]['expires'],'2026-11-12');self.assertEqual(entries[0]['approvedBy'],'pending-owner')
        self.assertEqual(entries[0]['severity'],'Critical');self.assertEqual(entries[0]['owner'],'amazen33')
        self.assertEqual(entries[0]['workOrder'],'WO-34')
        for text in ('fix version(s): 2.0','LAN-only','tunnel-only UIs','remediated by WO-34'):
            self.assertIn(text,entries[0]['reason'])
        sc.validate_exceptions(report['proposedExceptions'],on=ON,bootstrap=True)
        high=self.evaluate(value(introduced=True))['proposedExceptions']['exceptions'][0]
        self.assertEqual(high['expires'],'2026-12-12')

    def test_grype_alias_and_osv_cvss_fix_state_parsing(self):
        data={'matches':[{'vulnerability':{'id':'GHSA-fixture','severity':'Critical','fix':{'state':'fixed','versions':['2']}},
                         'relatedVulnerabilities':[{'id':'CVE-2026-1234'}],'artifact':{'name':'example','version':'1'}}]}
        parsed=sc.grype_findings(data,{'target':value()['target']})[0]
        self.assertEqual(parsed['vulnerability'],'CVE-2026-1234');self.assertEqual(parsed['fixVersions'],['2'])
        osv={'results':[{'source':{'path':'console/package-lock.json'},'packages':[{'package':{'name':'example','version':'1','ecosystem':'npm'},
            'vulnerabilities':[{'id':'GHSA-fixture','aliases':['CVE-2026-1234'],
                'severity':[{'type':'CVSS_V3','score':'CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N'}],
                'affected':[{'package':{'name':'example','ecosystem':'npm'},'ranges':[{'events':[{'introduced':'0'},{'fixed':'2'}]}]}]}]}]}]}
        parsed=sc.osv_findings(osv,ROOT)[0];self.assertEqual(parsed['severity'],'High');self.assertTrue(parsed['fixAvailable'])
        self.assertEqual(parsed['fixVersions'],['2'])


class InventoryAndIntegrity(unittest.TestCase):
    def p2_register_replacements(self,current):
        """Assert every field of the two owner-approved replacements; omit no comparison."""
        pins=[('registry.k8s.io/coredns/coredns','7efd3c635b03efd68c4e8398fc45f0d993d0e9ab016f72c1cefb0fd6d01aa286',
               'coredns/coredns/v1.14.7','f0530760b1e2ffcf23df322db638ee06d06fc07fead0ed3ddd710f2e224698a9',
               'wo34-coredns-v1.14.7.cdx.json.gz','4cd5c00ff3b9c9d95c81d9c679a50e794bb30ecbe109fd09324e0f44d3663468'),
              ('registry.k8s.io/etcd','5ed4e32061aa061f970d6500629213e8579ef17571dcf9789074966acb9afad1',
               'etcd-io/etcd/v3.6.15','cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30',
               'wo34-etcd-3.6.15-0.cdx.json.gz','3ec7f9e702ccea64fd4b4f8c4647ea4a39c539d92fd514e000bb31c09f0b4c2d')]
        expected=[]
        for name,pin,licence,licence_hash,sbom,sbom_hash in pins:
            item=dict(id='oci-image|'+name+'|sha256:'+pin,ecosystem='oci-image',name=name,version='sha256:'+pin,
                locations=['deploy/common/bootstrap-images.lock.json'],spdx='Apache-2.0',**{'class':'allowed'},
                licenceSource='https://raw.githubusercontent.com/'+licence+'/LICENSE',verifiedOn='2026-10-15',recordedOn='2026-10-15',
                integrities=['sha256:'+pin],notes='Unmodified upstream. Primary LICENSE SHA256 '+licence_hash+'. OS/dependency terms remain in the reviewed SBOM.',
                imageSBOM=dict(path='deploy/common/vendor/'+sbom,sha256=sbom_hash))
            self.assertEqual(current[item['id']],item)
            raw=(ROOT/item['imageSBOM']['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),sbom_hash)
            import gzip
            self.assertEqual(json.loads(gzip.decompress(raw))['bomFormat'],'CycloneDX')
            expected.append(item)
        return expected

    def fixture(self,root):
        for name in (*sc.LOCKS,*sc.RECEIPTS):
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
        path=root/'tools/platform_pg_image.py';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/'tools/platform_pg_image.py').read_bytes())

    def test_every_lock_entry_has_explicit_input_fallback_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            with patch.object(sc,'tracked',return_value=['console/package-lock.json','module/requirements-runtime.lock.txt','tools/ci/toolchain.lock.json']):
                plan=sc.inventory(root,full=True)
            expected=sum(len(sc.read(root/name)['images']) for name in sc.LOCKS)
            self.assertEqual(len(plan['coverage']),expected)
            self.assertEqual(len(plan['lockfiles']),2)
            owned=[v for v in plan['coverage'] if v['entry'].endswith((':console',':postgres'))]
            self.assertTrue(all(v['mode']=='pinned-inputs-only' for v in owned))
            inputs=[v['target'] for v in plan['images']]
            self.assertTrue(any('cloudnative-pg/postgresql@sha256:' in x for x in inputs))
            self.assertTrue(any('cloudnative-pg/pgvector@sha256:' in x for x in inputs))
            for image in plan['images']:
                self.assertEqual(image['platform'],'linux/amd64');self.assertRegex(image['source'],r'@sha256:[a-f0-9]{64}$')

    def test_built_images_use_graph_verified_archives_when_present(self):
        config=b'{"os":"linux","architecture":"amd64","rootfs":{"diff_ids":[]}}'
        cfg=dict(digest='sha256:'+sc.sha(config),size=len(config),mediaType='application/vnd.oci.image.config.v1+json')
        manifest=json.dumps(dict(schemaVersion=2,mediaType='application/vnd.oci.image.manifest.v1+json',config=cfg,layers=[])).encode()
        digest='sha256:'+sc.sha(manifest)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root);images=sc.read(root/sc.LOCKS[1])
            for name,file in [('console','console.oci.tar'),('postgres','postgresql-pgvector.tar')]:
                images['images'][name]['digest']=digest;target=root/'.build/dev-images'/file;target.parent.mkdir(parents=True,exist_ok=True)
                with tarfile.open(target,'w') as archive:
                    for member,raw in [('oci-layout',b'{"imageLayoutVersion":"1.0.0"}'),
                        ('index.json',json.dumps({'manifests':[dict(digest=digest,size=len(manifest),mediaType='application/vnd.oci.image.manifest.v1+json',
                            annotations={'org.opencontainers.image.ref.name':'registry.twinfra.example.com/twinfra/fixture:1.0'},platform={'os':'linux','architecture':'amd64'})]}).encode()),
                        ('blobs/sha256/'+sc.sha(config),config),('blobs/sha256/'+sc.sha(manifest),manifest)]:
                        item=tarfile.TarInfo(member);item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
            sc.write(root/sc.LOCKS[1],images)
            with patch.object(sc,'tracked',return_value=[]):plan=sc.inventory(root,full=True)
            self.assertTrue(all(v['mode']=='built-archive' for v in plan['coverage'] if v['entry'].endswith((':console',':postgres'))))
            self.assertTrue(any(v['source'].startswith('oci-archive:') for v in plan['images']))
            (root/'.build/dev-images/console.oci.tar').write_bytes(b'tampered')
            with patch.object(sc,'tracked',return_value=[]),self.assertRaises((ValueError,tarfile.ReadError)):sc.inventory(root,full=True)

    def test_changed_selection_and_tooling_full_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            originals={name:json.dumps(sc.read(root/name)) for name in sc.LOCKS}
            images=sc.read(root/sc.LOCKS[1]);images['images']['argocd']['digest']='sha256:'+'f'*64;sc.write(root/sc.LOCKS[1],images)
            def fake_git(root,*args):return originals[args[-1].split(':',1)[1]]
            with patch.object(sc,'tracked',return_value=[]),patch.object(sc,'changed',return_value=[sc.LOCKS[1]]),patch.object(sc,'git',side_effect=fake_git):
                plan=sc.inventory(root,base='a'*40)
            self.assertEqual(len(plan['images']),1);self.assertTrue(plan['images'][0]['introduced'])
            with patch.object(sc,'tracked',return_value=[]),patch.object(sc,'changed',return_value=['tools/ci/supply_chain.py']),patch.object(sc,'git',side_effect=fake_git):
                self.assertTrue(sc.inventory(root,base='a'*40)['full'])

    def test_tampered_scanner_binary_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);directory=root/'bin';directory.mkdir();artifacts={}
            for name in sc.TOOLS:
                raw=name.encode();(directory/name).write_bytes(raw);artifacts[name]={'binarySHA256':sc.sha(raw)}
            sc.write(root/'tools/ci/toolchain.lock.json',{'artifacts':artifacts})
            self.assertEqual(len(sc.verify_tools(directory,root)),3)
            (directory/'syft').write_bytes(b'tamper')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):sc.verify_tools(directory,root)

    def test_cached_sbom_reuses_digest_but_refuses_content_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'syft';binary.write_bytes(b'verified fixture binary')
            cache=root/'cache';out=root/'report';out.mkdir()
            plan={'images':[dict(target=value()['target'],source='registry:'+value()['target'],digest='sha256:'+'a'*64)]}
            calls=[]
            def fake_run(command,output,**kwargs):
                calls.append(command);Path(output).write_text('{"artifacts":[],"source":{}}')
            with patch.object(sc,'run',side_effect=fake_run):
                sc.sboms(plan,{'syft':str(binary)},cache,out)
                sc.sboms(plan,{'syft':str(binary)},cache,out)
                self.assertEqual(sum(c[1]=='scan' for c in calls),1)
                (cache/('a'*64+'.syft.json')).write_text('{"artifacts":["tampered"]}')
                with self.assertRaisesRegex(ValueError,'Cached SBOM'):sc.sboms(plan,{'syft':str(binary)},cache,out)

    def test_lockfile_baseline_comparison_does_not_mark_existing_risk_introduced(self):
        v=sc.finding('lockfile:requirements.txt','example','1.0',['CVE-2026-1234'],'High',True,'osv')
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            def fake_run(command,output,**kwargs):Path(output).write_text('{}')
            for same in (True,False):
                old=v if same else v|{'key':'b'*64,'version':'0.9'}
                with patch.object(sc,'sboms',return_value=[]),patch.object(sc,'run',side_effect=fake_run),\
                     patch.object(sc,'scan_locks',side_effect=[[dict(v)],[old]]),patch.object(sc,'git',side_effect=['requirements.txt','example==1.0']):
                    report=sc.scan(dict(images=[],lockfiles=['requirements.txt'],base='a'*40),{'grype':'fixture'},out/'cache',out)
                self.assertEqual(report['findings'][0]['introduced'],not same)

    def test_only_verified_added_artifacts_and_baseline_fingerprint_change(self):
        old=json.loads(subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':tools/ci/toolchain.lock.json']))
        new=sc.read(ROOT/'tools/ci/toolchain.lock.json')
        for name,entry in old['artifacts'].items():self.assertEqual(entry,new['artifacts'][name],name)
        self.assertEqual(set(new['artifacts'])-set(old['artifacts']),set(sc.TOOLS))
        for name in sc.TOOLS:
            self.assertRegex(new['artifacts'][name]['binarySHA256'],r'^[a-f0-9]{64}$')
            self.assertRegex(new['artifacts'][name]['checksumSHA256'],r'^[a-f0-9]{64}$')
        old=json.loads(subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':security/licence-baseline.json']))
        new=sc.read(ROOT/'security/licence-baseline.json')
        for a,b in zip(old['findings'],new['findings']):
            if a['id']=='schema-source:tools/ci/toolchain.lock.json':
                b=copy.deepcopy(b);b['fingerprint']=a['fingerprint']
            if a['id']=='image-digest:00-setup-ubuntu-host.sh' and (ROOT/'tools/ci/promote_p2.py').is_file():
                self.assertEqual(b['fingerprint'],hashlib.sha256((ROOT/'00-setup-ubuntu-host.sh').read_bytes()).hexdigest())
                b=copy.deepcopy(b);b['fingerprint']=a['fingerprint']
            self.assertEqual(a,b)
        added=[v for v in new['findings'] if v['id'] not in {f['id'] for f in old['findings']}]
        for entry in added:
            self.assertEqual(entry['id'],'image-sbom:oci-image|docker.io/library/python|sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170')
            before=next(v for v in old['findings'] if v['id'].startswith('image-sbom:oci-image|docker.io/library/python|'))
            masked=copy.deepcopy(entry);masked['id']=before['id'];masked['component']=before['component']
            self.assertEqual(masked,before,'Original distribution evidence deadline/owner remain unchanged')
        self.assertLessEqual(len(added),1)
        self.assertEqual((ROOT/'tools/ci/pr-baselines.json').read_bytes(),subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':tools/ci/pr-baselines.json']))

    def test_licence_register_preserves_existing_terms_and_only_adds_scanners_actions(self):
        old=json.loads(subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':security/licence-register.json']))
        removed='oci-image|docker.io/grafana/grafana|sha256:b28bae15e219c998fb0e0424ed724930cc61b1f61fb404d47c862f9a23f9e572'
        entry=next(v for v in old['components'] if v['id']==removed)
        self.assertEqual(entry['class'],'pending-removal');old['components'].remove(entry)
        old={v['id']:v for v in old['components']}
        current={v['id']:v for v in sc.read(ROOT/'security/licence-register.json')['components']}
        if (ROOT/'tools/ci/licence_ladder.py').is_file():
            sys.path.insert(0,str(ROOT/'tests'))
            from ladder_receipts import register
            current={v['id']:v for v in json.loads(register())['components']}
        replacements=self.p2_register_replacements(current) if (ROOT/'tools/ci/promote_p2.py').is_file() else []
        for name,entry in old.items():
            if name=='oci-image|registry.k8s.io/coredns/coredns|sha256:e7e6440cfd1e919280958f5b5a6ab2b184d385bba774c12ad2a9e1e4183f90d9' and replacements:
                self.assertNotIn(name,current)
                self.assertEqual(replacements[0]['name'],entry['name'])
                # Its fully asserted replacement supersedes this immutable historical receipt.
                value=copy.deepcopy(entry)
            else:value=copy.deepcopy(current[name])
            if name=='oci-image|registry.k8s.io/etcd|sha256:397189418d1a00e500c0605ad18d1baf3b541a1004d768448c367e48071622e5' and replacements:
                self.assertEqual(value['locations'],['security/node-exceptions.json'])
                value['locations']=entry['locations']
            value['locations']=[p for p in value['locations'] if p!='.github/workflows/supply-chain.yaml']
            if entry['name']=='docker.io/library/python':
                # WO-34 moves only the console builder/dev consumers to 3.14.8.
                moved={'console/Dockerfile','console/image.lock.json','tools/build_console_image.py','deploy/common/images.lock.json',
                       'deploy/environments/dev/cairo-1/services/workloads.yaml'}
                self.assertEqual(set(value['locations'])-moved,set(entry['locations'])-moved)
                value['locations']=entry['locations']
            if entry['id']=='oci-image|registry.k8s.io/pause|sha256:278fb9dbcca9518083ad1e11276933a2e96f23de604a3a08cc3c80002767d24c':
                self.assertEqual(value['locations'],[p for p in entry['locations'] if p!='deploy/common/bootstrap-images.lock.json'])
                value['locations']=entry['locations']
            self.assertEqual(value,entry,name)
        self.assertNotIn(removed,current)
        self.assertFalse(any(v['name']=='docker.io/grafana/grafana' for v in current.values()))
        extra=[v for k,v in current.items() if k not in old]
        for replacement in replacements:
            self.assertIn(replacement,extra);extra.remove(replacement)
        python=[v for v in extra if v['name']=='docker.io/library/python']
        for entry in python:
            self.assertEqual(entry['version'],'sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170')
            self.assertEqual(entry['class'],'base-os');self.assertEqual(entry['spdx'],'PSF-2.0')
            self.assertEqual(entry['licenceSource'],'https://raw.githubusercontent.com/python/cpython/v3.14.8/LICENSE')
        self.assertLessEqual(len(python),1)
        extra=[v for v in extra if v not in python]
        go_names={'golang/go','golang.org/x/mod','golang.org/x/sync','golang.org/x/sys',
                  'golang.org/x/telemetry','golang.org/x/tools','golang.org/x/vuln'}
        go=[v for v in extra if v['name'] in go_names]
        self.assertEqual({v['name'] for v in go},go_names)
        for entry in go:
            self.assertEqual(entry['spdx'],'BSD-3-Clause');self.assertEqual(entry['class'],'build-tool')
            self.assertEqual(entry['locations'],['tools/ci/toolchain.lock.json']);self.assertTrue(entry['unmodified'])
        extra=[v for v in extra if v['name'] not in go_names]
        self.assertEqual(len(extra),5)
        self.assertEqual({v['name'] for v in extra if v['ecosystem']=='github-action'},{'actions/cache','actions/download-artifact'})
        scanners=[v for v in extra if v['ecosystem']=='tool'];self.assertEqual(len(scanners),3)
        for entry in scanners:
            self.assertEqual(entry['spdx'],'Apache-2.0');self.assertEqual(entry['class'],'build-tool');self.assertTrue(entry['unmodified'])


class ReportingAndWorkflow(unittest.TestCase):
    def test_issue_created_once_then_edited_same_number(self):
        report=sc.evaluate(result(value('Low')),EMPTY,KEV,on=ON);report['markdown']=sc.markdown(report)
        url='https://github.com/amazen33/twinfra/actions/runs/123'
        with patch.object(reporter,'request',side_effect=[{'name':'security'},[],{'html_url':'issue/1'}]) as api:
            self.assertEqual(reporter.publish(report,sc.TITLE,url,'fixture'),'issue/1')
            self.assertEqual(api.call_args.args[3],'POST')
            body=api.call_args.args[2]['body']
        trusted={'title':sc.TITLE,'number':1,'user':{'login':'github-actions[bot]'},'labels':[{'name':'security'}]}
        with patch.object(reporter,'request',side_effect=[{'name':'security'},[trusted],{'html_url':'issue/1'}]) as api:
            self.assertEqual(reporter.publish(report,sc.TITLE,url,'fixture'),'issue/1')
            self.assertTrue(api.call_args.args[0].endswith('/issues/1'));self.assertEqual(api.call_args.args[3],'PATCH')
        with patch.object(sc,'fetch',return_value=json.dumps([trusted|{'body':body,'html_url':'issue/1'}]).encode()):
            self.assertEqual(sc.previous_state()[0],report['firstSeen'])

    def test_missing_issue_fallback_but_malformed_existing_state_fails(self):
        with patch.object(sc,'fetch',return_value=b'[]'):self.assertEqual(sc.previous_state(),({},None))
        with patch.object(sc,'fetch',return_value=json.dumps([{'title':sc.TITLE,'body':'broken'}]).encode()),self.assertRaises(ValueError):sc.previous_state()

    def test_thousands_of_first_seen_records_fit_one_issue_losslessly(self):
        findings=[sc.finding('docker.io/example/image'+str(i%21)+'@sha256:'+'a'*64,
                  'package-'+str(i%200),str(i%5),['CVE-2026-'+str(10000+i%1000)],'High',True,'fixture') for i in range(2452)]
        report=sc.evaluate(result(*findings),EMPTY,KEV,on=ON);report['markdown']=sc.markdown(report)
        with patch.object(reporter,'request',side_effect=[{'name':'security'},[],{'html_url':'issue/1'}]) as api:
            reporter.publish(report,sc.TITLE,'https://github.com/amazen33/twinfra/actions/runs/123','fixture')
            body=api.call_args.args[2]['body'];self.assertLess(len(body),65000)
        trusted={'title':sc.TITLE,'user':{'login':'github-actions[bot]'},'labels':[{'name':'security'}]}
        with patch.object(sc,'fetch',return_value=json.dumps([trusted|{'body':body,'html_url':'issue/1'}]).encode()):
            state,_=sc.previous_state()
        self.assertEqual(state,report['firstSeen']);self.assertEqual(state.identities,report['identityState'])
        # A resolved finding's complete identity and date survive the next report.
        later=sc.evaluate(result(),EMPTY,KEV,state,on=ON+timedelta(days=1))
        self.assertEqual(later['identityState'],report['identityState']);self.assertEqual(later['firstSeen'],report['firstSeen'])

    def test_untrusted_public_issue_cannot_reset_first_seen_or_be_edited(self):
        fake={'title':sc.TITLE,'number':1,'user':{'login':'untrusted'},'labels':[{'name':'security'}]}
        with patch.object(sc,'fetch',return_value=json.dumps([fake]).encode()),self.assertRaisesRegex(ValueError,'Untrusted'):
            sc.previous_state()
        report=sc.evaluate(result(value('Low')),EMPTY,KEV,on=ON);report['markdown']=sc.markdown(report)
        with patch.object(reporter,'request',side_effect=[{'name':'security'},[fake]]) as api,self.assertRaisesRegex(ValueError,'Untrusted'):
            reporter.publish(report,sc.TITLE,'https://github.com/amazen33/twinfra/actions/runs/123','fixture')
        self.assertEqual(api.call_count,2)

    def test_workflow_permissions_pins_secret_and_trigger_boundaries(self):
        for name in ('pr-tests.yaml','supply-chain.yaml'):
            path=ROOT/'.github/workflows'/name;raw=path.read_text();flow=yaml.safe_load(raw)
            self.assertNotIn('pull_request_target',raw)
            for job_name,job in flow['jobs'].items():
                if job_name.startswith('report-'):
                    self.assertEqual(job['permissions'],{'issues':'write'})
                    self.assertIn("github.ref == 'refs/heads/main'",job['if'])
                    self.assertNotIn('supply_chain.py scan',json.dumps(job))
                    self.assertNotIn('stage_tools',json.dumps(job))
                elif job_name in ('scan-pr','scan-nightly','watch-weekly'):
                    self.assertEqual(job['permissions'],{'contents':'read'})
                    self.assertNotIn('secrets.',json.dumps(job))
                for step in job.get('steps',[]):
                    if 'uses' in step:
                        self.assertRegex(step['uses'],r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[a-f0-9]{40}$')
                        self.assertNotRegex(step['uses'].lower(),r'aqua|trivy')
            if name=='pr-tests.yaml':self.assertIn('scan-pr',flow['jobs']['required']['needs'])
            else:
                triggers=flow.get('on',flow.get(True));self.assertEqual({v['cron'] for v in triggers['schedule']},{'30 2 * * *','0 3 * * 1'})

    def test_watch_selects_aged_stable_release_never_latest_or_candidate_execution(self):
        values=[dict(tag_name='v1.0.0',published_at='2026-09-01T00:00:00Z'),
                dict(tag_name='v2.0.0',published_at='2026-10-05T00:00:00Z'),
                dict(tag_name='v3.0.0',published_at='2026-09-20T00:00:00Z',prerelease=True)]
        self.assertEqual(watch.newest(values,ON)['tag_name'],'v1.0.0')
        code=(CI/'supply_chain_watch.py').read_text()
        self.assertNotIn('subprocess.run',code);self.assertNotIn('git push',code)
        self.assertIn('tool_candidate',code)

    def test_every_pinned_upstream_and_ci_binary_has_watch_provenance(self):
        tools=sc.read(ROOT/'tools/ci/toolchain.lock.json')['artifacts']
        names={k for k,v in tools.items() if v['output'].startswith('bin/') or v.get('runtimeArchive')}
        self.assertEqual(names,set(watch.TOOL_RULES))
        for lock in sc.LOCKS:
            for entry in sc.read(ROOT/lock)['images'].values():
                repo=sc.immutable(entry).split('@')[0]
                self.assertTrue(repo in watch.IMAGES or repo in watch.HUB or repo.startswith('docker.io/twinfra/'),repo)


if __name__=='__main__':unittest.main()
