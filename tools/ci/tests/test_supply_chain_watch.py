"""Offline weekly-watch resilience and sanitized scanner failure fixtures."""
import json
import io
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import supply_chain as sc
import supply_chain_watch as watch
import check_tool_sbom


def image(name,letter):
    target='docker.io/example/'+name+'@sha256:'+letter*64
    return dict(target=target,source='registry:'+target,digest='sha256:'+letter*64,
                publishedAt='2026-09-01T00:00:00Z',release='1.0.1',origins=[],introduced=False)


class WatchResilience(unittest.TestCase):
    def run_watch(self,root,scan,with_tool=False):
        plan=dict(images=[image('first','a'),image('second','b')],coverage=[],lockfiles=[])
        artifacts={'jq':dict(output='bin/jq',url='https://example.invalid/jq',sha256=sc.sha(b'fixture'))} if with_tool else {}
        sc.write(root/'tools/ci/toolchain.lock.json',{'artifacts':artifacts})
        out=root/'out';out.mkdir()
        candidates=[image('first','c'),image('second','d')]
        with patch.object(sc,'inventory',return_value=plan),patch.object(sc,'scan',side_effect=scan),\
             patch.object(sc,'fetch',return_value=b'fixture'),\
             patch.object(watch,'image_candidate',side_effect=candidates),\
             patch.object(watch,'tool_candidate',return_value=None),\
             patch.object(watch.time,'sleep') as sleep:
            report=watch.watch(root,{},out,root/'cache')
        return report,sleep

    def test_one_candidate_failure_completes_report_without_claiming_resolutions(self):
        for tool in ('syft','grype'):
            with self.subTest(tool=tool),tempfile.TemporaryDirectory() as tmp:
                calls=[]
                old=dict(target=image('first','a')['target'],package='pkg',version='1',
                         vulnerability='CVE-fixture',severity='High',fixAvailable=True)
                def scan(plan,*args,**kwargs):
                    calls.append(plan)
                    if plan['images'][0]['digest']=='sha256:'+'c'*64:
                        raise sc.ScannerCommandError(tool,1,plan['images'][0]['target'])
                    return {'findings':[old] if len(plan['images'])==2 else []}
                report,sleep=self.run_watch(Path(tmp),scan)
                row=report['comparisons'][0]
                reason='Candidate scan failed: '+image('first','c')['target']+' ('+tool+' exit 1)'
                self.assertEqual(row['unavailableReason'],reason)
                self.assertEqual(row['resolvedFindings'],[])
                self.assertIsNone(row['candidateFindings'])
                self.assertIsNone(report['comparisons'][1]['unavailableReason'])
                self.assertIn('## Failed candidate scans\n\n- '+reason,report['markdown'])
                self.assertEqual(len(calls),4);sleep.assert_called_once_with(2)

    def test_pinned_image_and_tool_failures_still_abort_without_retry(self):
        for tool_input in (False,True):
            with self.subTest(tool_input=tool_input),tempfile.TemporaryDirectory() as tmp:
                calls=[]
                def scan(plan,*args,**kwargs):
                    calls.append(plan)
                    if not tool_input or plan['images'][0]['target'].startswith('tool:'):
                        raise sc.ScannerCommandError('syft',1,plan['images'][0]['target'])
                    return {'findings':[]}
                with self.assertRaises(sc.ScannerCommandError):
                    self.run_watch(Path(tmp),scan,with_tool=tool_input)
                self.assertEqual(len(calls),2 if tool_input else 1)

    def test_retry_success_and_remaining_candidates_scan_individually(self):
        calls=[];attempts=0
        def scan(plan,*args,**kwargs):
            nonlocal attempts
            calls.append(plan)
            if len(plan['images'])==1 and plan['images'][0]['digest']=='sha256:'+'c'*64:
                attempts+=1
                if attempts==1:raise sc.ScannerCommandError('grype',2,plan['images'][0]['target'])
            return {'findings':[]}
        with tempfile.TemporaryDirectory() as tmp:
            report,sleep=self.run_watch(Path(tmp),scan)
        self.assertTrue(all(v['unavailableReason'] is None for v in report['comparisons']))
        self.assertTrue(all(len(v['images'])==1 for v in calls[1:]))
        self.assertEqual(attempts,2);sleep.assert_called_once_with(2)
        self.assertIn('## Failed candidate scans\n\nNone.',report['markdown'])

    def test_non_scanner_errors_are_not_softened(self):
        def scan(plan,*args,**kwargs):
            if len(plan['images'])==1:raise ValueError('Cached SBOM integrity/binding mismatch')
            return {'findings':[]}
        with tempfile.TemporaryDirectory() as tmp,self.assertRaisesRegex(ValueError,'integrity'):
            self.run_watch(Path(tmp),scan)

    def test_syft_scan_and_conversion_receive_the_item_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'syft';binary.write_bytes(b'fixture')
            item=image('first','a');calls=[]
            def run(command,output,**kwargs):
                calls.append((command,kwargs));Path(output).write_text('{}')
            with patch.object(sc,'run',side_effect=run):
                sc.sboms({'images':[item]},{'syft':str(binary)},root/'cache',root/'out')
            self.assertEqual([v[0][1] for v in calls],['scan','convert'])
            self.assertEqual([v[1]['target'] for v in calls],[item['target']]*2)
            self.assertIn('--platform',calls[0][0])

    def test_local_tool_scan_omits_image_platform_and_binds_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'actionlint';binary.write_bytes(b'fixture');calls=[]
            item=dict(target='tool:actionlint@sha256:'+sc.sha(binary.read_bytes()),
                      source='file:'+binary.as_posix(),digest='sha256:'+sc.sha(binary.read_bytes()))
            syft=root/'syft';syft.write_bytes(b'pinned scanner')
            def run(command,output,**kwargs):
                calls.append((command,kwargs));Path(output).write_text('{}')
            with patch.object(sc,'run',side_effect=run):
                sc.sboms({'images':[item]},{'syft':str(syft)},root/'cache',root/'out')
            self.assertNotIn('--platform',calls[0][0])
            self.assertEqual(calls[0][1]['diagnostic'].parent,root/'out'/'diagnostics')

    def test_integration_check_uses_pinned_member_and_rejects_empty_sbom_or_missing_grype(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);staged=root/'staged';(staged/'downloads').mkdir(parents=True)
            binary=bytearray(64);binary[:6]=b'\x7fELF\x02\x01';binary[18:20]=(62).to_bytes(2,'little')
            buffer=io.BytesIO()
            with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
                info=tarfile.TarInfo('actionlint');info.size=len(binary);archive.addfile(info,io.BytesIO(binary))
            raw=buffer.getvalue();(staged/'downloads/actionlint').write_bytes(raw)
            sc.write(root/'tools/ci/toolchain.lock.json',{'artifacts':{'actionlint':dict(sha256=sc.sha(raw),member='actionlint')}})
            for source,artifacts,matches,passes in [('file',[{'type':'go-module'}],[],True),
                                                    ('file',[],[],False),('image',[{'type':'go-module'}],[],False),
                                                    ('file',[{'type':'go-module'}],None,False)]:
                with self.subTest(source=source,artifacts=artifacts,matches=matches):
                    def scan(plan,tools,cache,out,*args):
                        self.assertEqual(plan['images'][0]['digest'],'sha256:'+sc.sha(binary))
                        key=sc.sha(binary)
                        sc.write(out/'sboms'/(key+'.syft.json'),dict(source={'type':source},artifacts=artifacts))
                        sc.write(out/(key+'.grype.json'),{'matches':matches})
                    with patch.object(sc,'verify_tools',return_value={}),patch.object(sc,'scan',side_effect=scan):
                        if passes:self.assertEqual(check_tool_sbom.check(root,staged,root/'out')['status'],'passed')
                        else:
                            with self.assertRaises(ValueError):check_tool_sbom.check(root,staged,root/'out')

    def test_grype_database_and_sbom_failures_receive_the_item_identity(self):
        for fail_at in ('update','status','sbom'):
            with self.subTest(fail_at=fail_at),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);item=image('first','a')|{'sbom':'fixture.json'}
                def run(command,output,**kwargs):
                    if (command[1].startswith('sbom:') if fail_at=='sbom' else command[2]==fail_at):
                        raise sc.ScannerCommandError('grype',3,kwargs['target'])
                    Path(output).write_text('{}')
                with patch.object(sc,'sboms',return_value=[item]),patch.object(sc,'run',side_effect=run),\
                     self.assertRaises(sc.ScannerCommandError) as caught:
                    sc.scan(dict(images=[item],lockfiles=[]),{'grype':'grype'},root/'cache',root/'out')
                self.assertEqual(caught.exception.target,item['target'])

    def test_candidate_evidence_is_retained_by_the_weekly_workflow(self):
        workflow=Path(__file__).resolve().parents[3]/'.github/workflows/supply-chain.yaml'
        self.assertIn('.build/supply-chain/watch-candidates/',workflow.read_text(encoding='utf-8'))

    def test_candidates_share_pinned_database_without_repeated_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);database=root/'pinned';calls=[]
            def run(command,output,**kwargs):
                calls.append((command,kwargs));Path(output).write_text('{}')
            with patch.object(sc,'sboms',return_value=[]),patch.object(sc,'run',side_effect=run):
                sc.scan(dict(images=[],lockfiles=[]),{'grype':'grype'},root/'cache',root/'candidate',database=database)
            self.assertEqual([v[0][1:3] for v in calls],[['db','status']])
            self.assertEqual(calls[0][1]['env']['GRYPE_DB_CACHE_DIR'],str((database/'database').resolve()))

    def test_scanner_failures_name_safe_target_without_serializing_output_or_credentials(self):
        secret='DO-NOT-LEAK'
        targets=[image('first','a')['target'],'tool:jq@sha256:'+'b'*64,
                 'https://user:'+secret+'@example.com/image?token='+secret,secret+'\nraw output']
        for tool in ('syft','grype'):
            for target in targets:
                with self.subTest(tool=tool,target=target),tempfile.TemporaryDirectory() as tmp:
                    output=Path(tmp)/'result.json'
                    completed=subprocess.CompletedProcess([],7,stdout=secret,stderr=secret)
                    with patch.object(sc.subprocess,'run',return_value=completed),self.assertRaises(sc.ScannerCommandError) as caught:
                        sc.run([tool,'scan','https://user:'+secret+'@example.com'],output,target=target)
                    message=str(caught.exception)
                    self.assertNotIn(secret,message);self.assertNotIn('https://',message)
                    self.assertIn(tool+' (exit 7)',message)
                    self.assertIn(target if target==targets[0] else ('jq' if target==targets[1] else tool),message)
                    self.assertEqual(list(Path(tmp).iterdir()),[])
                    self.assertNotIn(secret,json.dumps(vars(caught.exception)))

    def test_verified_local_file_diagnostics_preserve_error_but_redact_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'actionlint';binary.write_bytes(b'public verified ELF fixture')
            target='tool:actionlint@sha256:'+sc.sha(binary.read_bytes())
            diagnostic=root/'diagnostics'/'syft.stderr.log'
            completed=subprocess.CompletedProcess([],1,stdout='unused',stderr=(
                'ERROR unable to catalog local file\nhttps://user:DO-NOT-LEAK@example.com/path?token=hidden '
                'token=DO-NOT-LEAK environment-token-value'))
            command=['syft','scan','file:'+binary.as_posix()]
            with patch.dict(sc.os.environ,{'CI_TEST_TOKEN':'environment-token-value'}),\
                 patch.object(sc.subprocess,'run',return_value=completed),self.assertRaises(sc.ScannerCommandError) as caught:
                sc.run(command,target=target,diagnostic=diagnostic)
            value=diagnostic.read_text(encoding='utf-8')
            self.assertIn('unable to catalog local file',value)
            for secret in ('DO-NOT-LEAK','https://','hidden','environment-token-value'):
                self.assertNotIn(secret,value);self.assertNotIn(secret,str(caught.exception))

    def test_real_pinned_extraction_path_checks_archive_and_selects_regular_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);data=b'\x7fELF fixture actionlint bytes';buffer=io.BytesIO()
            with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
                info=tarfile.TarInfo('actionlint');info.size=len(data);info.mode=0o755
                archive.addfile(info,io.BytesIO(data))
                info=tarfile.TarInfo('README.md');info.size=5
                archive.addfile(info,io.BytesIO(b'wrong'))
            raw=buffer.getvalue();item=dict(sha256=sc.sha(raw),member='actionlint')
            value=watch.pinned_tool('actionlint',item,raw,out)
            self.assertEqual(Path(value['source'].removeprefix('file:')).read_bytes(),data)
            self.assertEqual(value['digest'],'sha256:'+sc.sha(data))
            self.assertEqual(value['target'],'tool:actionlint@sha256:'+sc.sha(data))
            with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):
                watch.pinned_tool('actionlint',item,raw+b'truncated-or-wrong',out)
            with self.assertRaises(KeyError):
                watch.pinned_tool('actionlint',item|{'member':'not-actionlint'},raw,out)

    def test_diagnostics_refuse_remote_or_unbound_local_inputs_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);binary=root/'actionlint';binary.write_bytes(b'fixture')
            target='tool:actionlint@sha256:'+'f'*64
            for source in ('registry:'+image('first','a')['target'],'file:'+binary.as_posix()):
                with self.subTest(source=source),patch.object(sc.subprocess,'run') as run,self.assertRaises(ValueError):
                    sc.run(['syft','scan',source],target=target,diagnostic=root/'diagnostic.log')
                run.assert_not_called()
            self.assertFalse((root/'diagnostic.log').exists())

    def test_real_tool_regression_has_no_pip_dependency_install(self):
        script=Path(__file__).resolve().parents[1]/'check_tool_sbom.py'
        env=sc.os.environ|{'PYTHONPATH':str(script.parent),'PYTHONNOUSERSITE':'1'}
        value=subprocess.run([sys.executable,'-S',str(script),'--help'],env=env,capture_output=True,text=True,check=True)
        self.assertIn('--staged',value.stdout)
        workflow=script.parents[2]/'.github/workflows/supply-chain-tools.yaml'
        self.assertNotIn('pip install',workflow.read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main()
