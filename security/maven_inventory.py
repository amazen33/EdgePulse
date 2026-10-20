"""ADRs 0024/0025: join CycloneDX components to actual Maven reachability.

The resolved per-module Maven tree is the scope authority (IOT-WO-02 ruling).
CycloneDX supplies identity, licence and hashes; disagreements are reported.
Source hashes reject stale evidence.
"""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

NS = {'m': 'http://maven.apache.org/POM/4.0.0'}
GROUP = 'com.edgepulse.platform'


def sha(path):
    path = Path(path)
    data = path.read_bytes()
    if path.suffix not in ('.jar', '.exe', '.zip', '.gz', '.tgz'):
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def reactor(root, directory='.'):
    path = Path(directory) / 'pom.xml'
    doc = ET.parse(root / path).getroot()
    yield path.as_posix().removeprefix('./'), doc
    for module in doc.findall('m:modules/m:module', NS):
        yield from reactor(root, str(Path(directory) / module.text))


def test_only_modules(root, register):
    """ADR 0025: verify both the declared Enforcer fence and resolved consumers."""
    modules = register['testOnlyModules']
    docs = dict(reactor(root))
    parent = docs['pom.xml']
    enforcer = parent.find("m:build/m:plugins/m:plugin[m:artifactId='maven-enforcer-plugin']", NS)
    if enforcer is None:
        raise ValueError('Test-only modules require the active Maven Enforcer plugin')
    if enforcer.findtext('m:inherited', 'true', NS) == 'false':
        raise ValueError('Test-only Enforcer fence is not inherited')
    if enforcer.findtext('m:configuration/m:skip', 'false', NS) != 'false':
        raise ValueError('Test-only Enforcer fence is skipped')
    executions = {e.findtext('m:id', '', NS): e for e in enforcer.findall('m:executions/m:execution', NS)}
    result = set()
    for item in modules:
        pom = item['path'] + '/pom.xml'
        if pom not in docs or docs[pom].findtext('m:artifactId', '', NS) != item['artifactId']:
            raise ValueError('Unknown test-only reactor module: ' + item['path'])
        execution = executions.get(item['enforcerExecution'])
        if execution is None or execution.findtext('m:configuration/m:fail', 'true', NS) == 'false':
            raise ValueError('Missing/disabled test-only Enforcer rule: ' + item['path'])
        from maven_commands import PHASES
        if (execution.findtext('m:configuration/m:skip', 'false', NS) != 'false'
                or execution.findtext('m:inherited', 'true', NS) != 'true'
                or execution.findtext('m:phase', 'validate', NS) not in PHASES[:PHASES.index('verify')+1]
                or execution.findall('m:configuration/m:rules/m:bannedDependencies/m:includes/m:include', NS)):
            raise ValueError('Missing/disabled test-only Enforcer rule: ' + item['path'])
        if 'enforce' not in [x.text for x in execution.findall('m:goals/m:goal', NS)]:
            raise ValueError('Test-only Enforcer execution does not enforce')
        excludes = {x.text for x in execution.findall(
            'm:configuration/m:rules/m:bannedDependencies/m:excludes/m:exclude', NS)}
        if item['restriction'] == 'no-consumers':
            expected = {GROUP + ':' + item['artifactId']}
        else:
            expected = {GROUP + ':*:*:*:' + s for s in ('compile', 'runtime', 'provided', 'system')}
        if not expected <= excludes:
            raise ValueError('Test-only Enforcer rule no longer bans shipped scopes: ' + item['path'])
        # A module cannot replace or skip its inherited fence.
        for name, doc in docs.items():
            if doc.findtext('m:properties/m:enforcer.skip', 'false', NS) != 'false':
                raise ValueError('Enforcer skip is forbidden: ' + name)
            for plugin in doc.findall('m:build/m:plugins/m:plugin', NS):
                aid = plugin.findtext('m:artifactId', '', NS)
                if name != 'pom.xml' and aid == 'maven-enforcer-plugin':
                    raise ValueError('Module overrides its inherited Enforcer fence: ' + name)
            if name == pom:
                for plugin in doc.findall('.//m:plugin', NS):
                    if plugin.findtext('m:artifactId', '', NS) in (
                            'maven-assembly-plugin', 'jib-maven-plugin', 'dockerfile-maven-plugin',
                            'docker-maven-plugin', 'spring-boot-maven-plugin'):
                        raise ValueError('Test-only module produces a shipping artifact: ' + item['path'])
        result.add(item['artifactId'])
    if len(result) != len(modules):
        raise ValueError('Duplicate test-only module')
    return result


def licence_expression(component):
    """Preserve SPDX expressions. Multiple POM licences need a reviewed election."""
    licenses = component.get('licenses', [])
    if len(licenses) == 1 and licenses[0].get('expression'):
        return licenses[0]['expression']
    ids = [x.get('license', {}).get('id') for x in licenses]
    if len(ids) == 1 and ids[0]:
        return ids[0]
    return None  # No invented AND/OR semantics from a list of POM licences.


def reviewed_licence(root, component):
    """Exact-version corrections/elections are bound to the unmodified SBOM label."""
    evidence = json.loads((root / 'security/maven-licence-evidence.json').read_text(encoding='utf-8'))
    key = component.get('group', '') + ':' + component['name'] + ':' + component['version']
    record = evidence.get(key)
    if record:
        if component.get('licenses', []) != record['sbomLicenses']:
            raise ValueError('SBOM licence declaration changed from reviewed evidence: ' + key)
        return record['spdx']
    return licence_expression(component)


def resolved_nodes(tree):
    """Dependency Plugin 3.11.0 JSON omits mediated nodes; keep resolved scopes."""
    for node in tree.get('children', []):
        scope = node.get('scope')
        if scope not in ('compile', 'runtime', 'provided', 'system', 'test'):
            raise ValueError('Unclear resolved Maven scope: ' + str(scope))
        yield node, scope
        yield from resolved_nodes(node)


def resolved_scopes(path):
    result = {}
    for node, scope in resolved_nodes(json.loads(path.read_text(encoding='utf-8'))):
        key = (node['groupId'] + ':' + node['artifactId'], node['version'])
        if key in result and result[key] != scope:
            raise ValueError('Conflicting resolved Maven scopes: ' + str(key))
        result[key] = scope
    return result


def nested_jars(path):
    """The current thin JAR and any future Spring Boot/WAR dependency archives."""
    with zipfile.ZipFile(path) as archive:
        return {Path(n).name for n in archive.namelist() if n.endswith('.jar')}


def bom_graph(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('bomFormat') != 'CycloneDX':
        raise ValueError('Invalid CycloneDX evidence: ' + str(path))
    root = data['metadata']['component']['bom-ref']
    components = {c['bom-ref']:c for c in data.get('components', [])}
    edges = {d['ref']:d.get('dependsOn', []) for d in data['dependencies']}
    if root not in edges:
        raise ValueError('CycloneDX graph has no module root: ' + str(path))
    pending, reached = [root], set()
    while pending:
        ref = pending.pop()
        if ref in reached:
            continue
        reached.add(ref)
        if ref not in edges:
            raise ValueError('Incomplete CycloneDX dependency graph: ' + ref)
        pending.extend(edges[ref])
    if reached - set(components) - {root} or set(components) - reached:
        raise ValueError('CycloneDX component/graph coverage disagreement: ' + str(path))
    return components, reached - {root}


def enumerate_maven(root, register, add):
    root = Path(root)
    test_only = test_only_modules(root, register)
    from maven_commands import guard_workflows, selected_plugins
    guard_workflows(root)
    doc = json.loads((root / 'target/licence/maven-evidence.json').read_text(encoding='utf-8'))
    for path, expected in doc['sourceInputs'].items():
        if sha(root / path) != expected:
            raise ValueError('Stale Maven licence evidence: ' + path)
    if set(doc['modules']) != {p for p, _ in reactor(root)}:
        raise ValueError('Maven evidence does not cover the full reactor')
    selected, _ = selected_plugins(root, root / doc['effectivePom'], Path.home() / '.m2/repository')
    if set(doc['executedPlugins']) != set(selected):
        raise ValueError('Executed plugin evidence changed')
    plugin_roots = {x['root']['groupId'] + ':' + x['root']['artifactId'] + ':' + x['root']['version']
                    for x in doc['pluginModules']}
    if not set(selected) <= plugin_roots:
        raise ValueError('Executed plugin classpath evidence missing')
    seen, shipping_archives = set(), []
    for pom, module in doc['modules'].items():
        all_components, all_reached = bom_graph(root / module['allBom'])
        non_test, non_test_reached = bom_graph(root / module['shippedBom'])
        if not set(non_test) <= set(all_components):
            raise ValueError('Non-test BOM is not a subset of all-scope BOM: ' + pom)
        scopes = resolved_scopes(root / module['resolvedTree'])
        bom_keys = {(c.get('group', '') + ':' + c['name'], c['version'])
                    for c in all_components.values()}
        if set(scopes) != bom_keys:
            raise ValueError('Resolved tree/BOM component set mismatch: ' + pom
                             + '; missing from BOM: ' + str(sorted(set(scopes) - bom_keys))
                             + '; missing from tree: ' + str(sorted(bom_keys - set(scopes))))
        for ref, bom in all_components.items():
            if not bom.get('purl', '').startswith('pkg:maven/'):
                raise ValueError('Unsupported Maven SBOM component identity')
            name, version = bom.get('group', '') + ':' + bom['name'], bom['version']
            scope = scopes[(name, version)]
            shipped = scope != 'test'
            bom_shipped = ref in non_test_reached
            if bom.get('group') == GROUP:
                if bom['name'] in test_only:
                    restriction = next(x['restriction'] for x in register['testOnlyModules']
                                       if x['artifactId'] == bom['name'])
                    if shipped or restriction == 'no-consumers':
                        raise ValueError('Test-only module is a forbidden dependency: ' + name)
                continue
            seen.add((name, version))
            is_test_module = module['artifactId'] in test_only
            add('maven', name, version, pom, scope=scope, kind='dependency',
                bomNonTestReachable=bom_shipped, scopeDisagreement=shipped != bom_shipped,
                testOnlyModule=is_test_module, shippedReachable=shipped and not is_test_module,
                packaged=False, spdx=reviewed_licence(root, bom),
                hashes=[x['content'] for x in bom.get('hashes', []) if x['alg'] == 'SHA-256'])
        if module['packaging'] != 'pom' and module['artifactId'] not in test_only:
            archive = root / module['archive']
            if not archive.is_file():
                raise ValueError('Missing packaged-artifact evidence; run mvn verify: ' + str(archive))
            shipping_archives.append(archive)
            with zipfile.ZipFile(archive) as jar:
                names = jar.namelist()
                manifest = jar.read('META-INF/MANIFEST.MF').decode('utf-8') if 'META-INF/MANIFEST.MF' in names else ''
                manifest = re.sub(r'\r?\n ', '', manifest)
                class_path = re.search(r'^Class-Path: (.*)$', manifest, re.M)
                class_path = class_path.group(1).split() if class_path else []
                packaging = dict(artifact=module['archive'], sha256=sha(archive),
                    nestedJars=sorted(n for n in names if n.endswith('.jar')),
                    manifestClassPath=class_path,
                    logbackClassesPresent=any(n.startswith('ch/qos/logback/') for n in names))
            # Attach archive evidence to an observation without creating a component.
            for ref, bom in all_components.items():
                if bom.get('group') == 'ch.qos.logback':
                    scope = scopes[('ch.qos.logback:' + bom['name'], bom['version'])]
                    filename = bom['name'] + '-' + bom['version'] + '.jar'
                    present = (any(Path(n).name == filename for n in packaging['nestedJars'])
                               or any(Path(n).name == filename for n in class_path)
                               or packaging['logbackClassesPresent'])
                    add('maven', 'ch.qos.logback:' + bom['name'], bom['version'], pom,
                        scope=scope, kind='dependency', shippedReachable=scope != 'test',
                        packaged=present, packagingEvidence=packaging,
                        testOnlyModule=False)

    plugin_seen = set()
    for module in doc['pluginModules']:
        components, reached = bom_graph(root / module['sbom'])
        for ref, bom in components.items():
            name, version = bom.get('group', '') + ':' + bom['name'], bom['version']
            if name.startswith('com.edgepulse.licence-evidence:'):
                continue
            if name == 'dom4j:dom4j' and version == '1.1':
                raise ValueError('Unclassified bundled AElfred licence in dom4j:dom4j:1.1')
            plugin_seen.add((name, version))
            r = module['root']
            kind = r['kind'] if (name == r['groupId'] + ':' + r['artifactId']
                                 and version == r['version']) else 'plugin-dependency'
            add('maven', name, version, 'pom.xml', kind=kind, scope='plugin',
                shippedReachable=False, testOnlyModule=False, packaged=False,
                spdx=reviewed_licence(root, bom),
                hashes=[x['content'] for x in bom.get('hashes', []) if x['alg'] == 'SHA-256'])
    packaged = set().union(*(nested_jars(p) for p in shipping_archives)) if shipping_archives else set()
    for archive in shipping_archives:
        with zipfile.ZipFile(archive) as jar:
            if any(n.startswith(('org/junit/', 'com/tngtech/archunit/', 'org/apache/maven/'))
                   for n in jar.namelist()):
                raise ValueError('Build-tool classes are packaged in ' + str(archive))
    for name, version in plugin_seen:
        if name.split(':')[1] + '-' + version + '.jar' in packaged:
            raise ValueError('Build plugin is packaged in a shipped artifact: ' + name)
    for name, version in seen:
        if name.split(':')[1] + '-' + version + '.jar' in packaged:
            add('maven', name, version, 'packaged-artifact', scope='runtime',
                kind='dependency', packaged=True, shippedReachable=True)
