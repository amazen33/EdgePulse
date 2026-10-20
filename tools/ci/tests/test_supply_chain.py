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
    # EdgePulse wiring schema extension: valid fixtures use this repository's namespace.
    if v['fixAvailable']:entry['workOrder']='IOT-WO-34'
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
        # The checker is unchanged; EdgePulse rejects its Twinfra proposal namespace.
        with self.assertRaisesRegex(ValueError,'Malformed vulnerability exception:.*does not match'):
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




class ReportingAndWorkflow(unittest.TestCase):
    def test_issue_created_once_then_edited_same_number(self):
        report=sc.evaluate(result(value('Low')),EMPTY,KEV,on=ON);report['markdown']=sc.markdown(report)
        url='https://github.com/amazen33/EdgePulse/actions/runs/123'
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
            reporter.publish(report,sc.TITLE,'https://github.com/amazen33/EdgePulse/actions/runs/123','fixture')
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
            reporter.publish(report,sc.TITLE,'https://github.com/amazen33/EdgePulse/actions/runs/123','fixture')
        self.assertEqual(api.call_count,2)


    def test_watch_selects_aged_stable_release_never_latest_or_candidate_execution(self):
        values=[dict(tag_name='v1.0.0',published_at='2026-09-01T00:00:00Z'),
                dict(tag_name='v2.0.0',published_at='2026-10-05T00:00:00Z'),
                dict(tag_name='v3.0.0',published_at='2026-09-20T00:00:00Z',prerelease=True)]
        self.assertEqual(watch.newest(values,ON)['tag_name'],'v1.0.0')
        code=(CI/'supply_chain_watch.py').read_text()
        self.assertNotIn('subprocess.run',code);self.assertNotIn('git push',code)
        self.assertIn('tool_candidate',code)



if __name__=='__main__':unittest.main()
