"""Planted violations: real audit/election/collector paths, synthetic data only."""
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SECURITY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SECURITY))
from check_licences import audit, check_component, evaluate, expression, identifiers
from edgepulse_licences import election
from licence_ladder import fingerprint, validate
from maven_inventory import sha, test_only_modules
from maven_commands import guard_workflows, selected_plugins

TODAY = date(2026, 10, 20)


class LicenceGateTest(unittest.TestCase):
    def setUp(self):
        work = SECURITY.parent / 'target'
        work.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='licence-test-', dir=work)
        self.root = Path(self.temp.name)
        assert self.root.resolve().is_relative_to(work.resolve())
        self.addCleanup(self.temp.cleanup)
        for pom in ('pom.xml', 'architecture/pom.xml', 'services/identity/pom.xml', 'contract-tests/pom.xml'):
            target = self.root / pom
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SECURITY.parent / pom, target)
        (self.root / 'security').mkdir()
        self.policy = json.loads((SECURITY / 'licence-policy.json').read_text())
        self.policy['ladder']['legacy'] = {}
        self.modules = [
            dict(path='architecture', artifactId='edgepulse-architecture',
                 enforcerExecution='enforce-no-shared-runtime', restriction='test-scope'),
            dict(path='contract-tests', artifactId='edgepulse-contract-tests',
                 enforcerExecution='enforce-contract-tests-not-consumable', restriction='no-consumers'),
        ]

    def component(self, spdx='EPL-2.0', scope='test', kind='dependency', test_module=False):
        return dict(id='maven|org.synthetic:probe|1.0.0', ecosystem='maven',
                    name='org.synthetic:probe', version='1.0.0', locations=['services/identity/pom.xml'],
                    observations=[dict(scope=scope, kind=kind, testOnlyModule=test_module,
                                       shippedReachable=scope != 'test' and not test_module,
                                       packaged=False, spdx=spdx)])

    def entry(self, component, spdx='EPL-2.0', kind='build-tool'):
        return dict(id=component['id'], ecosystem='maven', name=component['name'], version=component['version'],
                    spdx=spdx, electedSpdx=spdx, locations=component['locations'],
                    licenceSource='https://example.invalid/SYNTHETIC-licence',
                    recordedOn='2026-10-20', verifiedOn='2026-10-20', integrities=[],
                    unmodified=True, **{'class': kind})

    def check(self, entry, component):
        check_component(entry, component, self.policy, self.root, TODAY, {})

    # Amendment 3: the original six extension cases.
    def test_epl_compile_in_identity_fails(self):
        component = self.component(scope='compile')
        with self.assertRaisesRegex(ValueError, 'not permitted for allowed'):
            self.check(self.entry(component, kind='allowed'), component)

    def test_epl_test_scope_passes(self):
        component = self.component()
        self.check(self.entry(component), component)

    def test_unregistered_maven_dependency_fails_real_audit(self):
        component = self.component(spdx='MIT')
        self.make_audit_fixture(component, [])
        report = self.run_fixture_audit()
        self.assertEqual('failed', report['status'])
        self.assertIn('Unregistered component: ' + component['id'], report['errors'])

    def test_test_dependency_newly_runtime_reachable_fails(self):
        component = self.component()
        entry = self.entry(component)
        component['observations'].append(dict(scope='runtime', kind='dependency',
                                              shippedReachable=True, packaged=False))
        with self.assertRaisesRegex(ValueError, 'reachable from a shipped classpath'):
            self.check(entry, component)

    # IOT-WO-06 ruling 2026-10-21: POM imports are inventoried, not runtime exemptions.
    def imported_bom(self, name='org.synthetic:probe'):
        bom = dict(name=name, version='1.0.0', sha256='a'*64,
                   licences=[dict(name='MIT', url='https://example.invalid/SYNTHETIC-licence')],
                   pomURL='https://example.invalid/SYNTHETIC.pom')
        self.bom_inputs['components'].append(bom)
        path = self.root/'target/licence/maven-evidence.json'
        evidence = json.loads(path.read_text())
        evidence['importedBoms'] = deepcopy(self.bom_inputs)
        self.write(path, evidence)

    def test_imported_bom_missing_from_register_fails(self):
        # Synthetic BOM exists only as an import, not as a dependency fixture.
        self.make_audit_fixture(self.component('MIT'), [])
        self.imported_bom('org.synthetic:import-only')
        report = self.run_fixture_audit()
        self.assertIn('Unregistered component: maven|org.synthetic:import-only|1.0.0', report['errors'])

    def test_imported_bom_coordinate_at_runtime_scope_fails(self):
        component = self.component('MIT')
        self.make_audit_fixture(component, [self.entry(component, 'MIT')])
        self.imported_bom()
        path = self.root/'services/identity/target/tree.json'
        tree = json.loads(path.read_text())
        tree['children'][0]['scope'] = 'runtime'
        self.write(path, tree)
        with self.assertRaisesRegex(ValueError, 'Imported BOM coordinate reachable at runtime'):
            self.run_fixture_audit()

    def test_imported_bom_evidence_cannot_omit_an_input(self):
        self.make_audit_fixture(self.component('MIT'), [])
        self.bom_inputs['components'].append(dict(name='org.synthetic:missing',version='1.0.0'))
        with self.assertRaisesRegex(ValueError, 'Stale or incomplete imported BOM evidence'):
            self.run_fixture_audit()

    def test_imported_bom_packaged_in_service_fails(self):
        self.make_audit_fixture(self.component('MIT'), [])
        self.imported_bom('org.synthetic:import-only')
        with zipfile.ZipFile(self.root/'services/identity/target/synthetic.jar', 'a') as jar:
            jar.writestr('BOOT-INF/lib/import-only-1.0.0.pom', '<project/>')
        with self.assertRaisesRegex(ValueError, 'Imported BOM coordinate is packaged'):
            self.run_fixture_audit()

    def test_pom_import_is_build_tool_but_jar_import_is_not(self):
        from edgepulse_licences import maven_build_tool
        component = self.component('MIT', scope='import', kind='bom-import')
        component['observations'][0].update(type='pom', shippedReachable=False)
        maven_build_tool(component)
        component['observations'][0]['type'] = 'jar'
        with self.assertRaisesRegex(ValueError, 'neither test-scoped nor a build plugin'):
            maven_build_tool(component)

    def test_architecture_compile_consumer_fails(self):
        component = self.component(spdx='MIT')
        self.make_audit_fixture(component, [])
        for name in ('all', 'shipped'):
            path = self.root / ('services/identity/target/' + name + '.json')
            bom = json.loads(path.read_text())
            ref = 'pkg:maven/com.edgepulse.platform/edgepulse-architecture@2.0.0?type=jar'
            bom['components'].append(dict(group='com.edgepulse.platform', name='edgepulse-architecture',
                                          version='2.0.0', purl=ref, **{'bom-ref':ref}))
            bom['dependencies'][0]['dependsOn'].append(ref)
            bom['dependencies'].append(dict(ref=ref, dependsOn=[]))
            self.write(path, bom)
        path = self.root/'services/identity/target/tree.json'
        tree = json.loads(path.read_text())
        tree['children'].append(dict(groupId='com.edgepulse.platform',artifactId='edgepulse-architecture',
            version='2.0.0',scope='compile'))
        self.write(path,tree)
        with self.assertRaisesRegex(ValueError, 'Test-only module is a forbidden dependency'):
            self.run_fixture_audit()

    def test_second_epl_compile_artifact_is_not_jakarta_exception(self):
        component = self.component(scope='compile')
        entry = self.entry(component, kind='exception')
        entry['adr'] = '0025'
        with self.assertRaisesRegex(ValueError, 'Exception is not authorized'):
            self.check(entry, component)

    # Amendment 4: licence-family scope and fail-closed cases.
    def test_epl_one_plugin_dependency_passes(self):
        component = self.component('EPL-1.0', scope='plugin', kind='plugin-dependency')
        component['observations'][0]['shippedReachable'] = False
        self.check(self.entry(component, 'EPL-1.0'), component)

    def test_same_epl_one_plugin_reachable_from_shipped_classpath_fails(self):
        component = self.component('EPL-1.0', scope='plugin', kind='plugin-dependency')
        component['observations'][0]['shippedReachable'] = False
        entry = self.entry(component, 'EPL-1.0')
        component['observations'].append(dict(scope='compile', shippedReachable=True))
        with self.assertRaisesRegex(ValueError, 'reachable from a shipped classpath'):
            self.check(entry, component)

    def test_agpl_build_plugin_fails(self):
        component = self.component('AGPL-3.0-only', scope='plugin', kind='plugin')
        component['observations'][0]['shippedReachable'] = False
        with self.assertRaisesRegex(ValueError, 'blocked or unknown licence'):
            self.check(self.entry(component, 'AGPL-3.0-only'), component)

    def test_no_licence_fails(self):
        component = self.component('NOASSERTION')
        with self.assertRaisesRegex(ValueError, 'blocked or unknown licence'):
            self.check(self.entry(component, 'NOASSERTION'), component)

    # Architect's enterprise-grade ruling: unchanged upstream legacy mechanism.
    def legacy(self):
        component = self.component('MIT', scope='compile')
        entry = self.entry(component, 'MIT', 'allowed')
        entry.update(tier=1, enterpriseGrade=dict(status='legacy-pending', due='2027-04-20'))
        self.policy['ladder']['legacy'][entry['id']] = dict(
            sha256=fingerprint(entry), tier=1, due='2027-04-20')
        return entry

    def test_changed_legacy_fingerprint_fails(self):
        entry = self.legacy()
        entry['version'] = '1.0.1'
        with self.assertRaisesRegex(ValueError, 'Changed legacy runtime'):
            validate(entry, self.policy, {'MIT'}, TODAY)

    def test_extended_legacy_due_date_fails(self):
        entry = self.legacy()
        entry['enterpriseGrade']['due'] = '2027-04-21'
        with self.assertRaisesRegex(ValueError, 'deadline cannot be extended'):
            validate(entry, self.policy, {'MIT'}, TODAY)

    def test_new_runtime_component_cannot_use_legacy_pending(self):
        entry = self.legacy()
        entry['id'] = 'maven|org.synthetic:new-runtime|1.0.0'
        with self.assertRaisesRegex(ValueError, 'requires all enterprise-grade criteria'):
            validate(entry, self.policy, {'MIT'}, TODAY)

    def test_unchanged_legacy_passes_until_fixed_due_date(self):
        validate(self.legacy(), self.policy, {'MIT'}, TODAY)

    def test_or_requires_the_recorded_option(self):
        component = self.component('EPL-1.0 OR Apache-2.0')
        entry = self.entry(component, 'EPL-1.0 OR Apache-2.0')
        entry['electedSpdx'] = 'Apache-2.0'
        self.check(entry, component)
        entry['electedSpdx'] = 'MIT'
        with self.assertRaisesRegex(ValueError, 'not an option'):
            self.check(entry, component)

    def test_and_cannot_discard_an_obligation(self):
        component = self.component('Apache-2.0 AND AGPL-3.0-only')
        entry = self.entry(component, 'Apache-2.0 AND AGPL-3.0-only')
        entry['electedSpdx'] = 'Apache-2.0'
        with self.assertRaisesRegex(ValueError, 'not an option'):
            self.check(entry, component)

    def test_classpath_exception_build_only(self):
        license = 'GPL-2.0-only WITH Classpath-exception-2.0'
        component = self.component(license)
        self.check(self.entry(component, license), component)
        with self.assertRaisesRegex(ValueError, 'not permitted for allowed'):
            self.check(self.entry(component, license, 'allowed'), component)

    def test_missing_enforcer_rule_fails(self):
        p = self.root / 'pom.xml'
        p.write_text(p.read_text().replace('enforce-no-shared-runtime', 'SYNTHETIC-removed'))
        with self.assertRaisesRegex(ValueError, 'Missing/disabled test-only Enforcer'):
            test_only_modules(self.root, dict(testOnlyModules=self.modules))

    def test_test_only_module_compile_dependency_passes(self):
        component = self.component(test_module=True, scope='compile')
        self.check(self.entry(component), component)

    def test_packaged_build_tool_fails(self):
        component = self.component()
        component['observations'][0]['packaged'] = True
        with self.assertRaisesRegex(ValueError, 'or packaged'):
            self.check(self.entry(component), component)

    def test_licenseref_build_tool_without_stored_text_fails(self):
        component = self.component('LicenseRef-public-domain-xz-1.9')
        component['name'] = 'org.tukaani:xz'
        component['version'] = '1.9'
        entry = self.entry(component, 'LicenseRef-public-domain-xz-1.9')
        with self.assertRaisesRegex(ValueError, 'requires stored full licence text'):
            self.check(entry, component)

    def test_licenseref_cannot_authorize_an_unreviewed_version(self):
        component = self.component('LicenseRef-public-domain-xz-1.9')
        component['name'] = 'org.tukaani:xz'
        with self.assertRaisesRegex(ValueError, 'Unapproved build-tool LicenseRef'):
            self.check(self.entry(component, 'LicenseRef-public-domain-xz-1.9'), component)

    def test_skipped_enforcer_fence_fails(self):
        p = self.root/'pom.xml'
        p.write_text(p.read_text().replace('<id>enforce-no-shared-runtime</id>',
            '<id>enforce-no-shared-runtime</id><phase>none</phase>'))
        with self.assertRaisesRegex(ValueError, 'Missing/disabled test-only Enforcer'):
            test_only_modules(self.root, dict(testOnlyModules=self.modules))

    def test_baseline_cannot_admit_an_unregistered_component(self):
        component = self.component(spdx='MIT')
        self.make_audit_fixture(component, [])
        self.write(self.root / 'security/licence-baseline.json', dict(version=1, findings=[dict(
            id='licence-source:' + component['id'], component=component['id'], kind='licence-source',
            reason='SYNTHETIC-evidence gap', owner='SYNTHETIC-owner', requiredEvidence='SYNTHETIC-source',
            recordedOn=TODAY.isoformat(), expires=(TODAY + timedelta(days=90)).isoformat())]))
        self.assertIn('Unregistered component: ' + component['id'], self.run_fixture_audit()['errors'])

    def test_baseline_over_ninety_days_fails(self):
        self.make_audit_fixture(self.component(spdx='MIT'), [])
        self.write(self.root / 'security/licence-baseline.json', dict(version=1, findings=[dict(
            id='SYNTHETIC-gap', kind='licence-source', reason='SYNTHETIC-evidence',
            owner='SYNTHETIC-owner', requiredEvidence='SYNTHETIC-evidence',
            recordedOn=TODAY.isoformat(), expires=(TODAY + timedelta(days=91)).isoformat())]))
        self.assertTrue(any('Invalid expiry window' in e for e in self.run_fixture_audit()['errors']))

    def workflow(self, run):
        path = self.root / '.github/workflows/synthetic.yml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('jobs:\n  synthetic:\n    steps:\n      - run: ' + run + '\n')

    def test_workflow_site_fails_invocation_guard(self):
        self.workflow('mvn site')
        with self.assertRaisesRegex(ValueError, 'Unreviewed gated Maven invocation'):
            guard_workflows(self.root, self.policy)

    def test_workflow_negative_profile_fails_invocation_guard(self):
        self.workflow('mvn -B -f pom.xml verify -P enforcerNegativeTest')
        with self.assertRaisesRegex(ValueError, 'Unreviewed gated Maven invocation'):
            guard_workflows(self.root, self.policy)

    def test_new_verify_plugin_unregistered_classpath_fails(self):
        self.make_audit_fixture(self.component('MIT'), [])
        self.effective_plugin('org.synthetic', 'verify-plugin', '1.0.0')
        path = self.root / 'target/licence/maven-evidence.json'
        evidence = json.loads(path.read_text())
        selected, _ = selected_plugins(self.root, self.root/'target/effective.xml', Path.home()/'.m2/repository')
        evidence['executedPlugins'] = sorted(selected)
        root_ref = 'pkg:maven/org.synthetic/verify-plugin@1.0.0?type=jar'
        lib_ref = 'pkg:maven/org.synthetic/unregistered-plugin-library@1.0.0?type=jar'
        wrapper = 'pkg:maven/com.edgepulse.licence-evidence/SYNTHETIC@1?type=jar'
        bom = dict(bomFormat='CycloneDX', metadata=dict(component={'bom-ref':wrapper}),
                   components=[dict(group='org.synthetic',name=a,version='1.0.0',purl=r,
                                    licenses=[dict(license=dict(id='MIT'))], **{'bom-ref':r})
                               for a,r in [('verify-plugin',root_ref),('unregistered-plugin-library',lib_ref)]],
                   dependencies=[dict(ref=wrapper,dependsOn=[root_ref]),
                                 dict(ref=root_ref,dependsOn=[lib_ref]),dict(ref=lib_ref,dependsOn=[])])
        self.write(self.root/'target/new-plugin.json',bom)
        evidence['pluginModules'].append(dict(root=dict(groupId='org.synthetic',artifactId='verify-plugin',
             version='1.0.0',kind='plugin'),sbom='target/new-plugin.json'))
        self.write(path,evidence)
        report = self.run_fixture_audit()
        self.assertIn('Unregistered component: maven|org.synthetic:unregistered-plugin-library|1.0.0',report['errors'])

    def test_unexecuted_plugin_bound_to_verify_fails(self):
        self.make_audit_fixture(self.component('MIT'), [])
        self.effective_plugin('org.apache.maven.plugins','maven-site-plugin','3.12.1')
        self.write(self.root/'security/maven-unexecuted-plugins.json',dict(plugins=[dict(
            coordinates='org.apache.maven.plugins:maven-site-plugin:3.12.1',binding='site',
            reason='SYNTHETIC-site only',evidenceDate='2026-10-20')]))
        with self.assertRaisesRegex(ValueError, 'Listed unexecuted plugin became active'):
            self.run_fixture_audit()

    def test_clear_resolved_scope_overrides_bom_and_reports_disagreement(self):
        component = self.component('MIT')
        self.make_audit_fixture(component, [self.entry(component, 'MIT')])
        pom = self.root/'services/identity/pom.xml'
        text = pom.read_text()
        text = text.replace('<dependencies>', '<dependencies><dependency>'
            '<groupId>org.synthetic</groupId><artifactId>probe</artifactId>'
            '<version>1.0.0</version><scope>test</scope></dependency>', 1)
        pom.write_text(text)
        all_bom = json.loads((self.root/'services/identity/target/all.json').read_text())
        self.write(self.root/'services/identity/target/shipped.json', all_bom)
        path = self.root/'target/licence/maven-evidence.json'
        evidence = json.loads(path.read_text())
        evidence['sourceInputs']['services/identity/pom.xml'] = sha(pom)
        self.write(path, evidence)
        report = self.run_fixture_audit()
        self.assertIn(dict(id='maven|org.synthetic:probe|1.0.0',module='services/identity/pom.xml',
            resolvedScope='test',bomNonTestReachable=True), report['mavenScopeDisagreements'])
        probe = next(x for x in report['components'] if x['id'] == component['id'])
        self.assertEqual('build-tool', probe['class'])
        self.assertEqual('test', probe['observations'][0]['scope'])
        self.assertFalse(any(component['id'] in e for e in report['errors']))
        self.assertFalse(any('scope disagreement' in e.lower() for e in report['errors']))

    def test_tree_component_missing_from_bom_fails(self):
        self.make_audit_fixture(self.component('MIT'), [])
        path = self.root/'services/identity/target/tree.json'
        tree = json.loads(path.read_text())
        tree['children'].append(dict(groupId='org.synthetic',artifactId='missing-from-bom',
                                    version='1.0.0',scope='runtime'))
        self.write(path,tree)
        with self.assertRaisesRegex(ValueError, 'Resolved tree/BOM component set mismatch'):
            self.run_fixture_audit()

    def test_blank_lines_do_not_hide_site_invocation(self):
        from maven_commands import workflow_commands, check_invocation
        commands = workflow_commands('echo SYNTHETIC\n\nmvn site\n\n')
        self.assertEqual([['site']], commands)
        with self.assertRaisesRegex(ValueError, 'Unreviewed gated Maven invocation'):
            check_invocation(self.root, commands[0], self.policy)

    def test_collector_inventory_uses_reviewed_goal_version_and_managed_realm(self):
        self.make_audit_fixture(self.component('MIT'), [])
        goal = next(g for c in self.policy['gatedMavenCommands'] for g in c['goals']
                    if 'maven-dependency-plugin:' in g)
        group, artifact, version, _ = goal.split(':')
        path = self.root/'target/effective.xml'
        path.write_text('<project xmlns="http://maven.apache.org/POM/4.0.0">'
            '<artifactId>SYNTHETIC</artifactId><build><pluginManagement><plugins><plugin>'
            '<groupId>'+group+'</groupId><artifactId>'+artifact+'</artifactId><version>'+version+'</version>'
            '<dependencies><dependency><groupId>org.synthetic</groupId><artifactId>realm-override</artifactId>'
            '<version>1.0.0</version></dependency></dependencies></plugin></plugins></pluginManagement></build></project>')
        selected, _ = selected_plugins(self.root,path,Path.home()/'.m2/repository')
        realm = selected[group+':'+artifact+':'+version]
        self.assertEqual(realm['version'],version)
        self.assertEqual(realm['dependencies'][0]['artifactId'],'realm-override')

    def effective_plugin(self,group,artifact,version):
        (self.root/'target/effective.xml').write_text(
            '<project xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>SYNTHETIC</artifactId>'
            '<build><plugins><plugin><groupId>'+group+'</groupId><artifactId>'+artifact+'</artifactId>'
            '<version>'+version+'</version><executions><execution><phase>verify</phase><goals>'
            '<goal>SYNTHETIC-goal</goal></goals></execution></executions></plugin></plugins></build></project>')

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def make_audit_fixture(self, component, entries):
        self.bom_inputs = dict(components=[], modelSources={})
        self.write(self.root/'security/maven-bom-licence-evidence.json', {})
        self.write(self.root / 'security/licence-policy.json', self.policy)
        shutil.copyfile(SECURITY / 'licence-register.schema.json', self.root / 'security/licence-register.schema.json')
        self.write(self.root / 'security/licence-register.json', dict(version=1,
                   testOnlyModules=self.modules, components=entries))
        self.write(self.root / 'security/licence-baseline.json', dict(version=1, findings=[]))
        self.write(self.root / 'security/maven-licence-evidence.json', {})
        # No workflow, binary or chart inputs in this synthetic collector fixture.
        self.write(self.root / 'security/toolchain.lock.json', dict(tools=[dict(name='python', version='3.12.12')]))
        self.write(self.root / 'dev/kind/pins.json', dict(
            **{x:dict(version='1.0.0', windowsSha256='0'*64, linuxSha256='1'*64)
               for x in ('kind', 'kubectl', 'helm')},
            cilium=dict(version='1.0.0', chartSha256='2'*64),
            cnpg=dict(version='1.0.0', manifestSha256='3'*64)))
        modules = {}
        for pom in ('pom.xml', 'architecture/pom.xml', 'services/identity/pom.xml', 'contract-tests/pom.xml'):
            aid = {'pom.xml':'edgepulse-platform-parent', 'architecture/pom.xml':'edgepulse-architecture',
                   'services/identity/pom.xml':'edgepulse-service-identity',
                   'contract-tests/pom.xml':'edgepulse-contract-tests'}[pom]
            base = Path(pom).parent
            root_ref = 'pkg:maven/com.edgepulse.platform/' + aid + '@2.0.0?type=jar'
            for view in ('all','shipped'):
                bom = dict(bomFormat='CycloneDX', metadata=dict(component={'bom-ref':root_ref}),
                           components=[], dependencies=[dict(ref=root_ref, dependsOn=[])])
                if pom == 'services/identity/pom.xml' and view == 'all':
                    ref = 'pkg:maven/org.synthetic/probe@1.0.0?type=jar'
                    bom['components'].append(dict(group='org.synthetic', name='probe', version='1.0.0',
                        purl=ref, licenses=[dict(license=dict(id='MIT'))], **{'bom-ref':ref}))
                    bom['dependencies'][0]['dependsOn'].append(ref)
                    bom['dependencies'].append(dict(ref=ref, dependsOn=[]))
                self.write(self.root / base / ('target/' + view + '.json'), bom)
            modules[pom] = dict(artifactId=aid, packaging='pom' if pom == 'pom.xml' else 'jar',
                                allBom=(base/'target/all.json').as_posix(),
                                shippedBom=(base/'target/shipped.json').as_posix(),
                                archive=(base/'target/synthetic.jar').as_posix(),
                                resolvedTree=(base/'target/tree.json').as_posix())
            tree = dict(groupId='com.edgepulse.platform', artifactId=aid, version='2.0.0', children=[])
            if pom == 'services/identity/pom.xml':
                tree['children'].append(dict(groupId='org.synthetic',artifactId='probe',version='1.0.0',scope='test'))
            self.write(self.root/base/'target/tree.json', tree)
            if pom == 'services/identity/pom.xml':
                with zipfile.ZipFile(self.root / modules[pom]['archive'], 'w') as z:
                    z.writestr('com/edgepulse/Synthetic.class', b'SYNTHETIC-bytecode')
        self.write(self.root / 'target/licence/maven-evidence.json', dict(
            sourceInputs={p:sha(self.root/p) for p in modules}, modules=modules,
            pluginModules=[]))
        self.write(self.root/'security/maven-unexecuted-plugins.json',dict(plugins=[]))
        (self.root/'target/effective.xml').write_text(
            '<project xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>SYNTHETIC</artifactId></project>')
        evidence=json.loads((self.root/'target/licence/maven-evidence.json').read_text())
        evidence['effectivePom']='target/effective.xml'
        evidence['mavenHome']='SYNTHETIC-Maven-home'
        evidence['importedBoms']=deepcopy(self.bom_inputs)
        evidence['executedPlugins']=[]
        cli = sorted({tuple(goal.split(':')[:3]) for command in self.policy['gatedMavenCommands']
                      for goal in command['goals'] if len(goal.split(':')) == 4})
        for i,(g,a,v) in enumerate(cli):
            ref='pkg:maven/'+g+'/'+a+'@'+v+'?type=jar'
            wrapper='pkg:maven/com.edgepulse.licence-evidence/SYNTHETIC-'+str(i)+'@1?type=jar'
            bom=dict(bomFormat='CycloneDX',metadata=dict(component={'bom-ref':wrapper}),
                components=[dict(group=g,name=a,version=v,purl=ref,licenses=[dict(license=dict(id='Apache-2.0'))],
                                 **{'bom-ref':ref})],
                dependencies=[dict(ref=wrapper,dependsOn=[ref]),dict(ref=ref,dependsOn=[])])
            path='target/cli-'+str(i)+'.json'
            self.write(self.root/path,bom)
            evidence['pluginModules'].append(dict(root=dict(groupId=g,artifactId=a,version=v,kind='plugin'),sbom=path))
            evidence['executedPlugins'].append(g+':'+a+':'+v)
            c=dict(id='maven|'+g+':'+a+'|'+v,name=g+':'+a,version=v,locations=['pom.xml'])
            entries.append(self.entry(c,'Apache-2.0'))
        self.write(self.root/'security/licence-register.json',dict(version=1,testOnlyModules=self.modules,components=entries))
        self.write(self.root/'target/licence/maven-evidence.json',evidence)

    def run_fixture_audit(self):
        tracked = [p.relative_to(self.root).as_posix() for p in self.root.rglob('*')
                   if p.is_file() and 'target' not in p.relative_to(self.root).parts]
        with patch('licence_inventory.files', return_value=tracked), \
                patch('maven_boms.inputs', side_effect=lambda *args: deepcopy(self.bom_inputs)):
            return audit(self.root, TODAY)


if __name__ == '__main__':
    unittest.main()
