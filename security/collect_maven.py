#!/usr/bin/env python
"""IOT-WO-02: per-module CycloneDX scope views and executed-plugin classpaths."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from maven_inventory import NS, reactor, sha
from maven_commands import check_invocation, guard_workflows, selected_plugins

CYCLONEDX = 'org.cyclonedx:cyclonedx-maven-plugin:2.9.3:makeBom'
HELP = 'org.apache.maven.plugins:maven-help-plugin:3.5.2:effective-pom'
TREE = 'org.apache.maven.plugins:maven-dependency-plugin:3.11.0:tree'


def invoke(maven, root, arguments, log):
    check_invocation(root, arguments)
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([maven, '-B', '-ntp', *arguments], cwd=root,
                                stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise ValueError('Maven evidence command failed; see ' + str(log))


def bom_args(pom, tests, name):
    return ['-f', str(pom), CYCLONEDX, '-DincludeTestScope=' + str(tests).lower(),
            '-DincludeProvidedScope=true', '-DincludeSystemScope=true',
            '-DoutputFormat=json', '-DoutputName=' + name]


def collect(root, maven):
    root = root.resolve()
    work = root / 'target/licence'
    work.mkdir(parents=True, exist_ok=True)
    guard_workflows(root)
    invoke(maven, root, bom_args('pom.xml', True, 'licence-all-scopes'), work / 'all-scopes.log')
    invoke(maven, root, bom_args('pom.xml', False, 'licence-shipped-scopes'), work / 'shipped-scopes.log')
    invoke(maven, root, ['-f', 'pom.xml', TREE, '-DoutputType=json',
                         '-DoutputFile=target/licence-resolved-tree.json'], work / 'resolved-tree.log')
    invoke(maven, root, ['-f', 'pom.xml', HELP, '-Doutput=target/licence/effective-pom.xml',
                         '-Dverbose=true'], work / 'effective-pom.log')
    cache = Path.home() / '.m2/repository'
    plugins, candidates = selected_plugins(root, work / 'effective-pom.xml', cache)
    docs = dict(reactor(root))
    roots = []
    for key, plugin in sorted(plugins.items()):
        g, a = plugin['name'].split(':')
        roots.append(dict(groupId=g, artifactId=a, version=plugin['version'],
                          type='jar', classifier='', kind='plugin', dependencies=plugin['dependencies']))
    for pom, doc in docs.items():
        for ext in doc.findall('m:build/m:extensions/m:extension', NS):
            roots.append(dict(**{k:ext.findtext('m:' + k, '', NS) for k in
                                 ('groupId', 'artifactId', 'version')},
                              type='jar', classifier='', kind='build-extension', dependencies=[]))
    properties = docs['pom.xml'].find('m:properties', NS)
    for g, a, prop in [('com.google.protobuf', 'protoc', 'protobuf.version'),
                       ('io.grpc', 'protoc-gen-grpc-java', 'grpc.version')]:
        for platform in ('linux-x86_64', 'windows-x86_64'):
            roots.append(dict(groupId=g, artifactId=a, version=properties.findtext('m:' + prop, '', NS),
                              type='exe', classifier=platform, kind='code-generator', dependencies=[]))
    plugin_modules = []
    project = work / 'plugin-project-executed'
    project.mkdir(exist_ok=True)
    for i, entry in enumerate(roots):
        directory = project / ('plugin-' + str(i))
        directory.mkdir(exist_ok=True)
        doc = ET.Element('project', {'xmlns':'http://maven.apache.org/POM/4.0.0'})
        for k, v in [('modelVersion','4.0.0'), ('groupId','com.edgepulse.licence-evidence'),
                     ('artifactId','plugin-' + str(i)), ('version','1')]:
            ET.SubElement(doc, k).text = v
        deps = ET.SubElement(doc, 'dependencies')
        for dependency in [entry] + entry['dependencies']:
            d = ET.SubElement(deps, 'dependency')
            for k in ('groupId', 'artifactId', 'version', 'type', 'classifier'):
                if dependency.get(k):
                    ET.SubElement(d, k).text = dependency[k]
        # These stand-alone wrappers must execute the same patched collector
        # realm as the reactor. Do not inherit runtime dependencyManagement:
        # that would misrepresent the isolated plugin dependency graph.
        g,a,v,_ = CYCLONEDX.split(':')
        collector = plugins[g+':'+a+':'+v]
        build = ET.SubElement(doc,'build')
        active = ET.SubElement(ET.SubElement(build,'plugins'),'plugin')
        for k,value in [('groupId',g),('artifactId',a),('version',v)]:
            ET.SubElement(active,k).text = value
        overrides = ET.SubElement(active,'dependencies')
        for dependency in collector['dependencies']:
            d = ET.SubElement(overrides,'dependency')
            for k in ('groupId','artifactId','version','type','classifier'):
                if dependency.get(k):
                    ET.SubElement(d,k).text = dependency[k]
        ET.ElementTree(doc).write(directory / 'pom.xml', encoding='utf-8', xml_declaration=True)
        pom = (directory / 'pom.xml').relative_to(root).as_posix()
        invoke(maven, root, bom_args(pom, False, 'plugin-bom'), work / ('plugin-' + str(i) + '.log'))
        plugin_modules.append(dict(root=entry, sbom=(directory / 'target/plugin-bom.json').relative_to(root).as_posix()))
    modules = {}
    for pom, doc in docs.items():
        parent = Path(pom).parent
        artifact = doc.findtext('m:artifactId', '', NS)
        version = doc.findtext('m:version', '', NS) or doc.findtext('m:parent/m:version', '', NS)
        modules[pom] = dict(artifactId=artifact, packaging=doc.findtext('m:packaging', 'jar', NS),
                            allBom=(parent / 'target/licence-all-scopes.json').as_posix(),
                            shippedBom=(parent / 'target/licence-shipped-scopes.json').as_posix(),
                            resolvedTree=(parent / 'target/licence-resolved-tree.json').as_posix(),
                            archive=(parent / 'target' / (artifact + '-' + version + '.jar')).as_posix())
    inputs = {p:sha(root / p) for p in sorted(docs)}
    for p in ['security/collect_maven.py', 'security/maven_commands.py',
              'security/maven-unexecuted-plugins.json', 'security/licence-policy.json']:
        inputs[p] = sha(root / p)
    document = dict(sourceInputs=inputs, modules=modules, pluginModules=plugin_modules,
                    effectivePom="target/licence/effective-pom.xml",
                    executedPlugins=sorted(plugins), candidateBindings=candidates)
    (work / 'maven-evidence.json').write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
    print('Maven licence evidence: per-module scope graphs and executed plugin classpaths')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--mvn', default=shutil.which('mvn'))
    args = parser.parse_args()
    if not args.mvn:
        parser.error('Maven is required')
    collect(args.root, args.mvn)
