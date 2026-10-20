"""IOT-WO-02 invocation-scope ruling: fail closed on new Maven commands/bindings."""
import fnmatch
import json
from pathlib import Path
import re
import shlex
import xml.etree.ElementTree as ET
import zipfile

import yaml

NS = {'m': 'http://maven.apache.org/POM/4.0.0'}
PHASES = ('validate', 'initialize', 'generate-sources', 'process-sources', 'generate-resources',
          'process-resources', 'compile', 'process-classes', 'generate-test-sources',
          'process-test-sources', 'generate-test-resources', 'process-test-resources',
          'test-compile', 'process-test-classes', 'test', 'prepare-package', 'package',
          'pre-integration-test', 'integration-test', 'post-integration-test', 'verify', 'install', 'deploy')


def command(argv, root):
    goals, profiles, properties, flags = [], [], {}, []
    pom = 'pom.xml'
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in ('-B', '--batch-mode', '-ntp', '--no-transfer-progress'):
            flags.append(token)
        elif token in ('-version', '--version', '-v'):
            goals.append('--version'); pom = None
        elif token in ('-f', '--file'):
            i += 1
            if i >= len(argv):
                raise ValueError('Missing Maven POM argument')
            p = Path(argv[i])
            pom = p.resolve().relative_to(root.resolve()).as_posix() if p.is_absolute() else p.as_posix()
        elif token == '-P' or token.startswith('-P'):
            if token == '-P':
                i += 1; value = argv[i]
            else:
                value = token[2:]
            profiles.extend(value.split(','))
        elif token.startswith('-D'):
            key, sep, value = token[2:].partition('=')
            properties[key] = value if sep else 'true'
        elif token.startswith('-'):
            raise ValueError('Unreviewed Maven option: ' + token)
        else:
            if any(c in token for c in '$`{}'):
                raise ValueError('Dynamic Maven invocation is not reviewable')
            goals.append(token)
        i += 1
    return dict(goals=goals, profiles=sorted(profiles), properties=properties, pom=pom)


def check_invocation(root, argv, policy=None):
    policy = policy or json.loads((root / 'security/licence-policy.json').read_text(encoding='utf-8'))
    actual = command(argv, root)
    for allowed in policy['gatedMavenCommands']:
        pattern = allowed['pom']
        if (actual['goals'] == allowed['goals'] and actual['profiles'] == allowed['profiles']
                and actual['properties'] == allowed['properties']
                and (actual['pom'] == pattern or (pattern and actual['pom']
                     and fnmatch.fnmatchcase(actual['pom'], pattern)))):
            return actual
    raise ValueError('Unreviewed gated Maven invocation: ' + json.dumps(actual, sort_keys=True))


def workflow_commands(text):
    """Literal shell commands only; reject nested/dynamic spellings rather than ignore them."""
    joined = re.sub(r'(?:\\|`)\r?\n', ' ', text)
    lex = shlex.shlex(joined, posix=True, punctuation_chars=';&|\n')
    lex.whitespace = ' \t\r'
    lex.whitespace_split = True
    lex.commenters = '#'
    tokens = list(lex)
    result = []
    def separator(value):
        return re.fullmatch(r'[;&|\n]+', value) is not None
    for i, token in enumerate(tokens):
        if token in ('mvn', 'mvn.cmd', './mvnw', './mvnw.cmd', 'mvnw', 'mvnw.cmd'):
            if i and not separator(tokens[i-1]):
                raise ValueError('Indirect Maven invocation must be reviewed')
            if token not in ('mvn', 'mvn.cmd'):
                raise ValueError('Maven wrapper is not part of the reviewed gate toolchain')
            args = []
            for value in tokens[i+1:]:
                if separator(value):
                    break
                args.append(value)
            result.append(args)
        elif re.search(r'\b(?:mvn|mvnw)(?:\.cmd)?\b', token):
            raise ValueError('Nested/dynamic Maven invocation must be reviewed')
    return result


def guard_workflows(root, policy=None):
    found = []
    for path in sorted((root / '.github/workflows').glob('*')):
        if path.suffix not in ('.yml', '.yaml'):
            continue
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
        for job, body in data.get('jobs', {}).items():
            for step in body.get('steps', []):
                if isinstance(step.get('run'), str):
                    for argv in workflow_commands(step['run']):
                        found.append(dict(workflow=path.relative_to(root).as_posix(), job=job,
                                          command=check_invocation(root, argv, policy)))
    return found


def selected_plugins(root, effective, cache):
    """Read effective lifecycle bindings, including plugin-descriptor goal defaults."""
    doc = ET.parse(effective).getroot()
    projects = list(doc) if doc.tag.endswith('projects') else [doc]
    selected, candidates = {}, {}
    for project in projects:
        module = project.findtext('m:artifactId', '', NS)
        for section in ('m:build/m:plugins/m:plugin', 'm:profiles/m:profile/m:build/m:plugins/m:plugin'):
            for plugin in project.findall(section, NS):
                g = plugin.findtext('m:groupId', 'org.apache.maven.plugins', NS)
                a, v = (plugin.findtext('m:' + x, '', NS) for x in ('artifactId', 'version'))
                key = g + ':' + a + ':' + v
                bindings = []
                active = False
                for execution in plugin.findall('m:executions/m:execution', NS):
                    phase = execution.findtext('m:phase', '', NS)
                    goals = [x.text for x in execution.findall('m:goals/m:goal', NS)]
                    phases = [phase] if phase else []
                    if not phases:
                        jar = cache / g.replace('.', '/') / a / v / (a + '-' + v + '.jar')
                        if not jar.exists():
                            raise ValueError('Unresolved plugin descriptor; run verify: ' + key)
                        with zipfile.ZipFile(jar) as z:
                            descriptor = ET.fromstring(z.read('META-INF/maven/plugin.xml'))
                        phases = [m.findtext('phase', '') for m in descriptor.findall('mojos/mojo')
                                  if m.findtext('goal') in goals]
                    bindings.append(dict(phases=phases, goals=goals,
                                         profile='inactive' if 'profiles' in section else 'active'))
                    if ('profiles' not in section and any(p in PHASES[:PHASES.index('verify')+1]
                                                          for p in phases)):
                        active = True
                candidates.setdefault(key, []).extend(bindings or [dict(phases=[], goals=[], profile='unbound')])
                if active:
                    deps = []
                    for d in plugin.findall('m:dependencies/m:dependency', NS):
                        deps.append({k:d.findtext('m:' + k, '', NS) for k in
                                     ('groupId', 'artifactId', 'version', 'type', 'classifier')})
                    selected[key] = dict(name=g+':'+a, version=v, kind='plugin', module=module,
                                         dependencies=deps)
    # The reviewed invocation policy is the version authority for collector
    # plugins too. Include effective pluginManagement overrides in their realms.
    policy = json.loads((root / 'security/licence-policy.json').read_text(encoding='utf-8'))
    cli = {tuple(goal.split(':')[:3]) for command in policy['gatedMavenCommands']
           for goal in command['goals'] if len(goal.split(':')) == 4}
    for g, a, v in sorted(cli):
        key = g+':'+a+':'+v
        deps = []
        for project in projects:
            for plugin in project.findall('m:build/m:pluginManagement/m:plugins/m:plugin', NS):
                if (plugin.findtext('m:groupId', 'org.apache.maven.plugins', NS),
                    plugin.findtext('m:artifactId', '', NS), plugin.findtext('m:version', '', NS)) != (g,a,v):
                    continue
                values = [{k:d.findtext('m:'+k, '', NS) for k in
                           ('groupId','artifactId','version','type','classifier')}
                          for d in plugin.findall('m:dependencies/m:dependency', NS)]
                if deps and deps != values:
                    raise ValueError('Collector plugin realm differs between modules: '+key)
                deps = values
        selected[key] = dict(name=g+':'+a, version=v, kind='plugin', module='collector', dependencies=deps)
    exclusions = json.loads((root / 'security/maven-unexecuted-plugins.json').read_text(encoding='utf-8'))
    excluded = {e['coordinates'] for e in exclusions['plugins']}
    overlap = excluded & selected.keys()
    if overlap:
        raise ValueError('Listed unexecuted plugin became active: ' + ', '.join(sorted(overlap)))
    unexpected = candidates.keys() - selected.keys() - excluded
    if unexpected:
        raise ValueError('Unrecorded unexecuted Maven plugin: ' + ', '.join(sorted(unexpected)))
    return selected, candidates


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    commands = guard_workflows(root)
    print('Maven invocation guard: passed (' + str(len(commands)) + ' workflow invocations)')
