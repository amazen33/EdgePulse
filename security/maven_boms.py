"""IOT-WO-06 ruling 2026-10-21: imported POM-only BOM input inventory.

Use Maven 3.9.11's model builder, already part of the registered Maven tool,
offline against the gated build's cache. No new Maven goal or dependency.
Compare its managed model to help:effective-pom before accepting any inputs.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

NS = {'m': 'http://maven.apache.org/POM/4.0.0'}
FIELDS = ('groupId', 'artifactId', 'version', 'type', 'classifier', 'scope')


def raw_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs(root, maven_home, cache, effective, classpaths=()):
    from maven_inventory import reactor
    home = Path(maven_home)
    policy = json.loads((root/'security/licence-policy.json').read_text(encoding='utf-8'))
    if any(c['profiles'] for c in policy['gatedMavenCommands']):
        raise ValueError('Explicit gated Maven profiles need a matching BOM model request; refusing incomplete inventory')
    if not (home/'lib/maven-model-builder-3.9.11.jar').is_file():
        raise ValueError('Imported BOM inventory requires the pinned Maven 3.9.11 model builder')
    java = str(Path(os.environ['JAVA_HOME'])/'bin/java') if os.environ.get('JAVA_HOME') else shutil.which('java')
    reactor_poms = [str(root/p) for p, _ in reactor(root)]
    resolved_poms = set()
    for path in classpaths:
        for component in json.loads((root/path).read_text(encoding='utf-8')).get('components', []):
            g, a, v = component.get('group', ''), component['name'], component['version']
            if g.startswith('com.edgepulse.'):
                continue  # Reactor models and generated collector wrappers are already covered.
            pom = cache/g.replace('.', '/')/a/v/(a+'-'+v+'.pom')
            if not pom.is_file():
                raise ValueError('Missing resolved component POM for BOM input traversal: ' + g+':'+a+':'+v)
            resolved_poms.add(str(pom))
    command = [java, '--class-path', str(home/'lib/*'), str(root/'security/ImportedBoms.java'),
               str(cache), *reactor_poms, *sorted(resolved_poms)]
    result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # Diagnostics contain model coordinates/paths only; no POM body is logged.
        raise ValueError('Offline Maven BOM model building failed: ' + result.stderr.decode('utf-8', errors='replace'))
    models = ET.fromstring(result.stdout)
    actual = ET.parse(effective).getroot()
    projects = list(actual) if actual.tag.endswith('projects') else [actual]
    for project, modeled in zip(projects, models.findall('project')[:len(reactor_poms)], strict=True):
        def row(d):
            return tuple(d.findtext('m:'+k, 'jar' if k == 'type' else '', NS) for k in FIELDS)
        flattened = {row(d) for d in project.findall('m:dependencyManagement/m:dependencies/m:dependency', NS)}
        built = {tuple(d.get(k, '') for k in FIELDS) for d in modeled.findall('managed')}
        if flattened != built:
            raise ValueError('BOM input model differs from gated Maven effective model: ' + modeled.get('pom'))
    boms = []
    for bom in models.findall('bom'):
        g, a, v = bom.get('coordinates').split(':')
        licences = [dict(x.attrib) for x in bom.findall('license')]
        if not licences:
            raise ValueError('Imported BOM has no effective POM licence: ' + bom.get('coordinates'))
        boms.append(dict(name=g+':'+a, version=v, sha256=raw_sha(bom.get('pom')),
                         pomURL='https://repo.maven.apache.org/maven2/'+g.replace('.','/')+'/'+a+'/'+v+'/'+a+'-'+v+'.pom',
                         licences=licences))
    return dict(components=sorted(boms, key=lambda b:(b['name'], b['version'])),
                modelSources={s.get('coordinates'):raw_sha(s.get('pom')) for s in models.findall('source')})


def spdx(licences):
    # Exact declarations/URLs, not keyword or substring guesses. Unknown forms
    # require review; a list never invents AND/OR semantics.
    declarations = {
        'Apache-2.0': 'Apache-2.0',
        'Apache License, Version 2.0': 'Apache-2.0',
        'The Apache Software License, Version 2.0': 'Apache-2.0',
        'Apache License 2.0': 'Apache-2.0',
        'Apache 2.0': 'Apache-2.0',
        'Apache 2': 'Apache-2.0',
        'The Apache License, Version 2.0': 'Apache-2.0',
        'MIT': 'MIT',
        'MIT License': 'MIT',
        'The MIT License (MIT)': 'MIT',
        'The MIT License': 'MIT',
        'BSD-3-Clause': 'BSD-3-Clause',
        'Eclipse Public License - v 2.0': 'EPL-2.0',
        'Eclipse Public License v2.0': 'EPL-2.0',
    }
    values = {declarations.get(x['name']) for x in licences}
    if len(values) != 1 or None in values:
        raise ValueError('Unreviewed imported BOM licence declaration: ' + json.dumps(licences, sort_keys=True))
    return values.pop()


def enumerate_boms(root, evidence, add):
    classpaths = [m['allBom'] for m in evidence['modules'].values()] + [m['sbom'] for m in evidence['pluginModules']]
    observed = inputs(root, evidence['mavenHome'], Path.home()/'.m2/repository', root/evidence['effectivePom'], classpaths)
    if observed != evidence['importedBoms']:
        raise ValueError('Stale or incomplete imported BOM evidence')
    keys = set()
    reviews = json.loads((root/'security/maven-bom-licence-evidence.json').read_text(encoding='utf-8'))
    for bom in observed['components']:
        keys.add((bom['name'], bom['version']))
        review = reviews.get(bom['name']+':'+bom['version'])
        if review:
            if review['sha256'] != bom['sha256'] or review['licences'] != bom['licences']:
                raise ValueError('Imported BOM licence review no longer matches POM: ' + bom['name'])
            expression = review['spdx']
        else:
            expression = spdx(bom['licences'])
        add('maven', bom['name'], bom['version'], 'imported-bom', kind='bom-import', scope='import',
            type='pom', shippedReachable=False, packaged=False, testOnlyModule=False,
            spdx=expression, hashes=[bom['sha256']], pomURL=bom['pomURL'])
    return keys


def reject_packaged_boms(archive, imports):
    """A POM import never authorizes bundling that input in a service artifact."""
    with zipfile.ZipFile(archive) as jar:
        names = {Path(n).name for n in jar.namelist()}
        if 'META-INF/MANIFEST.MF' in jar.namelist():
            names.update(Path(n).name for n in jar.read('META-INF/MANIFEST.MF').decode('utf-8').split())
        for name, version in imports:
            if any(name.split(':')[1]+'-'+version+suffix in names for suffix in ('.jar','.pom')):
                raise ValueError('Imported BOM coordinate is packaged: ' + name+':'+version)
        for path in jar.namelist():
            if path.endswith(('.pom', '/pom.xml')):
                model = ET.fromstring(jar.read(path))
                g = model.findtext('m:groupId', '', NS) or model.findtext('m:parent/m:groupId', '', NS)
                a = model.findtext('m:artifactId', '', NS)
                v = model.findtext('m:version', '', NS) or model.findtext('m:parent/m:version', '', NS)
                if (g+':'+a, v) in imports:
                    raise ValueError('Imported BOM coordinate is packaged: ' + g+':'+a+':'+v)
