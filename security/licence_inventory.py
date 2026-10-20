"""Offline inventory of locked/source-rendered inputs; no network or code execution."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess
import tarfile
from urllib.parse import unquote, urlparse

import yaml


def digest(path):
    data = path.read_bytes()
    # Git text checkout conversion must not change an evidence finding's identity.
    if path.suffix not in ('.gz', '.tgz', '.zip'):
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def files(root):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others',
                             '--exclude-standard'], capture_output=True, text=True, check=True)
    return sorted(set(result.stdout.splitlines()))


def identity(ecosystem, name, version):
    return f'{ecosystem}|{name}|{version}'


def normal_image(value):
    for mirror in ('registry.vcloud.example.com/','registry.twinfra.example.com/'):
        value = value.removeprefix(mirror)
    if '/' not in value.split('@')[0]:
        value = 'docker.io/library/' + value
    elif '.' not in value.split('/')[0] and ':' not in value.split('/')[0]:
        value = 'docker.io/' + value
    return value


def image_parts(value):
    value = normal_image(value)
    base, sep, sha = value.partition('@')
    last = base.rsplit('/', 1)[-1]
    tag = last.split(':', 1)[1] if ':' in last else None
    name = base.rsplit(':', 1)[0] if tag else base
    return name, sha if sep else tag or 'UNPINNED'


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def source_identity(url):
    parsed = urlparse(url)
    module = re.fullmatch(r'https://proxy\.golang\.org/(.+)/@v/(.+)\.(?:zip|mod|info)', url)
    if module:
        name, version = module.groups()
        repo = 'golang/' + name.removeprefix('golang.org/x/') if name.startswith('golang.org/x/') else name.removeprefix('github.com/')
        return name, version, repo
    sdk = re.fullmatch(r'https://go\.dev/dl/(go[0-9.]+)\.(?:linux|windows)-amd64\.(?:tar\.gz|zip)', url)
    if sdk:
        return 'golang/go', sdk[1], 'golang/go'
    parts = [unquote(x) for x in parsed.path.strip('/').split('/')]
    if parsed.netloc == 'raw.githubusercontent.com' and len(parts) >= 4:
        return '/'.join(parts[:2] + parts[3:]), parts[2], '/'.join(parts[:2])
    if parsed.netloc == 'github.com' and len(parts) >= 6 and parts[2:4] == ['releases', 'download']:
        return '/'.join(parts[:2] + parts[5:]), parts[4], '/'.join(parts[:2])
    return parsed.netloc + parsed.path, 'sha256', None


def production_npm(packages):
    """Resolve nested lockfile nodes, including optional dependencies, from prod roots."""
    pending = [('', name) for kind in ('dependencies', 'optionalDependencies')
               for name in packages.get('', {}).get(kind, {})]
    reached = set()
    while pending:
        parent, name = pending.pop()
        candidates = []
        current = parent
        while current:
            candidates.append(current + '/node_modules/' + name)
            current = current.rsplit('/node_modules/', 1)[0] if '/node_modules/' in current else ''
        candidates.append('node_modules/' + name)
        location = next((p for p in candidates if p in packages), None)
        if location is None or location in reached:
            continue
        reached.add(location)
        node = packages[location]
        pending.extend((location, dep) for kind in ('dependencies', 'optionalDependencies', 'peerDependencies')
                       for dep in node.get(kind, {}))
    return reached


def argocd_cache_override(root):
    """Only the exact WO-25 upstream default may be treated as inert.

    Source checks plus real base/overlay/WSL render checks in CI prevent this
    exclusion from admitting the old cache into a deployable workload.
    """
    lock_path = root / 'deploy/registry-images.lock.json'
    transform_path = root / 'deploy/kustomize/base/argocd/kustomization.yaml'
    if not lock_path.is_file() or not transform_path.is_file():
        return False
    cache = json.loads(lock_path.read_text()).get('images', {}).get('valkey', {})
    canonical = cache.get('canonical', '')
    prefix = 'registry.vcloud.example.com/docker.io/valkey/valkey@'
    if not canonical.startswith(prefix):
        return False
    sha = canonical.removeprefix(prefix)
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', sha):
        return False
    transforms = yaml.safe_load(transform_path.read_text()).get('images', [])
    return any(t.get('name') == 'public.ecr.aws/docker/library/redis'
               and t.get('newName') == 'docker.io/valkey/valkey'
               and t.get('digest') == sha and not t.get('newTag')
               for t in transforms)


def enumerate_inputs(root, rendered=()):
    root = Path(root)
    tracked = files(root)
    components, findings, aliases = {}, {}, {}
    cache_overridden = argocd_cache_override(root)
    preserved_cache_sources = {
        'deploy/kustomize/base/argocd/install.yaml',
        'deploy/vendor/argocd-v3.5.3-install.yaml.gz',
        'lab/wsl/vendor/argocd-core.yaml.gz',
        'deploy/common/vendor/argocd-core.yaml.gz',
    }

    def finding(kind, path, detail):
        key = f'{kind}:{path}'
        findings[key] = dict(id=key, kind=kind, path=path, detail=detail,
                             fingerprint=digest(root / path))

    def add(eco, name, version, path, **extra):
        key = identity(eco, name, version)
        item = components.setdefault(key, dict(id=key, ecosystem=eco, name=name,
                                               version=version, locations=[], observations=[]))
        if path not in item['locations']:
            item['locations'].append(path)
        item['observations'].append(dict(path=path, **extra))
        return item

    # Locks establish tag/digest equivalence. A mirror spelling is not another component.
    for path in tracked:
        if not path.endswith('.json') or not ('lock' in path or path == 'security/node-exceptions.json'):
            continue
        data = json.loads((root / path).read_text(encoding='utf-8'))
        for obj in objects(data):
            candidates = [v for k, v in obj.items() if k in ('source', 'canonical', 'release', 'image')
                          and isinstance(v, str) and not v.startswith('http')]
            with_hash = [x for x in candidates if '@sha256:' in x]
            if with_hash:
                target = normal_image(with_hash[0])
                for candidate in candidates:
                    aliases[normal_image(candidate)] = target
        for key, obj in data.get('images', {}).items() if isinstance(data.get('images'), dict) else []:
            if isinstance(obj, dict) and obj.get('canonical'):
                release = data.get('imageSources', {}).get(key)
                if release:
                    aliases[normal_image(release)] = normal_image(obj['canonical'])

    def image(value, path):
        if not isinstance(value, str) or re.search(r'[\s${}]', value) or value.endswith(':'):
            return
        if (cache_overridden and path in preserved_cache_sources
                and value == 'public.ecr.aws/docker/library/redis:8.2.3-alpine'):
            finding('inert-default', path, 'WO-25 upstream cache default replaced by digest-pinned Valkey')
            return
        value = normal_image(value)
        if value.startswith(('docker.io/vcloud/', 'vcloud/', 'docker.io/twinfra/', 'twinfra/')):
            return  # first-party outputs: dependencies/base images are enumerated separately
        value = aliases.get(value, value)
        name, version = image_parts(value)
        add('oci-image', name, version, path, image=value)
        if not version.startswith('sha256:') and not path.startswith('rendered:'):
            finding('image-digest', path, 'Existing image references need immutable digest evidence')

    def walk_images(value, path):
        for obj in objects(value):
            if isinstance(obj.get('repository'), str) and (obj.get('tag') or obj.get('digest')):
                repository = obj.get('registry', '') + ('/' if obj.get('registry') else '') + obj['repository']
                image(repository + ('@' + obj['digest'] if obj.get('digest') else ':' + str(obj['tag'])), path)
            for key in ('image', 'imageName'):
                if isinstance(obj.get(key), str):
                    image(obj[key], path)

    for path in tracked:
        file = root / path
        if path.startswith(('security/licence', 'security/licences/')):
            continue
        if path.endswith('package-lock.json'):
            data = json.loads(file.read_text(encoding='utf-8'))
            packages = data.get('packages', {})
            production = production_npm(packages)
            for location, package in packages.items():
                if not location:
                    continue
                name = package.get('name') or location.rsplit('node_modules/', 1)[-1]
                add('npm', name, package['version'], path, node=location,
                    spdx=package.get('license'), dev=package.get('dev', False),
                    production=location in production, integrity=package.get('integrity'))
        if re.search(r'requirements[^/]*\.txt$', path):
            for line in file.read_text().splitlines():
                if re.search(r';\s*python_version\s*<\s*[\"\x27]3\.11[\"\x27]', line):
                    finding('inert-default', path, 'Python <3.11 fallback is inactive on the pinned Python 3.14 target')
                    continue
                match = re.match(r'^([\w.-]+)(?:\[[^]]+\])?==([^\s;]+)', line)
                if match:
                    name = re.sub(r'[-_.]+', '-', match[1]).lower()
                    add('pip', name, match[2], path,
                        hashes=re.findall(r'--hash=sha256:([a-f0-9]{64})', line))
                elif re.match(r'^\w.* @ https://', line):
                    name, _, url, *_ = line.split()
                    filename = unquote(url.rsplit('/', 1)[-1])
                    version = filename.split('-')[1]
                    add('pip', name, version, path, url=url,
                        hashes=re.findall(r'--hash=sha256:([a-f0-9]{64})', line))
                elif line.strip() and not line.startswith(('#', '--', ' ', '\\')):
                    raise ValueError('Unpinned/unrecognized requirement: ' + path + ': ' + line)
        if path.startswith('.github/workflows/'):
            for name, sha in re.findall(r'uses:\s*([^\s@]+)@([\w.-]+)', file.read_text()):
                if not re.fullmatch(r'[0-9a-f]{40}', sha):
                    raise ValueError('GitHub Action is not pinned by SHA: ' + path + ': ' + name)
                add('github-action', name, sha, path)
            # EdgePulse CI tool versions are checked against the owned tool lock below.
        if path.endswith('.json') and path != 'security/toolchain.lock.json' and not path.endswith('package-lock.json') and ('lock' in path or path in ('lab/wsl/profile.json', 'security/node-exceptions.json')):
            data = json.loads(file.read_text(encoding='utf-8'))
            walk_images(data, path)
            for obj in objects(data):
                url = obj.get('url') or (obj.get('imageUrl') if path=='deploy/hyperv/ubuntu-image.lock.json' else None)
                if not isinstance(url, str) or not url.startswith('https://'):
                    continue
                if url.startswith('https://files.pythonhosted.org/'):
                    continue  # same pinned pip distribution
                if 'pr-baselines.json' in path:
                    continue
                name, version, repo = source_identity(url)
                artifact_hash = obj.get('sha256') or obj.get('sourceSHA256')
                if version == 'sha256':
                    version = artifact_hash or 'UNPINNED'
                if path == 'tools/ci/toolchain.lock.json' and obj.get('goBuildInput') is True:
                    if not (url.startswith('https://proxy.golang.org/') or url.startswith('https://go.dev/dl/')):
                        raise ValueError('Unreviewed Go build-input origin')
                    eco = 'tool'
                elif url.endswith('.tgz'):
                    eco = 'helm-chart'
                elif '/releases/download/' in url and not re.search(r'\.(yaml|json|txt)$', url):
                    eco = 'tool'
                elif 'get.helm.sh/' in url or re.fullmatch(r'https://dl\.k8s\.io/release/v[0-9.]+/bin/linux/amd64/(?:kubeadm|kubectl)', url):
                    eco = 'tool'
                else:
                    eco = 'manifest'
                # Vendored chart headers are the canonical chart identity below.
                if eco == 'helm-chart' and any((root / p).name == url.rsplit('/', 1)[-1] for p in tracked if '/vendor/' in p and p.endswith('.tgz')):
                    continue
                add(eco, name, version, path, url=url, sha256=artifact_hash, repo=repo)
                if '/master/' in url or '/main/' in url:
                    finding('schema-source', path, 'Resolve schema licence source to the artifact commit')
            images = data.get('images', {})
            for key, obj in images.items() if isinstance(images, dict) else []:
                if isinstance(obj, dict):
                    image(obj.get('canonical') or obj.get('source') or obj.get('release'), path)
                elif isinstance(obj, str):
                    image(obj, path)
            for value in data.get('imageSources', {}).values():
                image(value, path)
            if isinstance(data.get('base'), str):
                image(data['base'], path)
            for key in ('smokeImage', 'pauseImage', 'corednsImage', 'dnsImage'):
                if data.get(key):
                    image(data[key], path)
            if path == 'module-4a/artifacts.lock.json':
                for key, eco, name in [('openbaoHelm', 'helm-chart', 'openbao/openbao-helm'),
                                       ('openbaoCSIProvider', 'tool', 'openbao/openbao-csi-provider')]:
                    add(eco, name, data['versions'][key], path)
        if path.endswith('.tgz') and '/vendor/' in path:
            with tarfile.open(file, 'r:gz') as archive:
                for member in archive.getmembers():
                    if member.isfile() and member.name.endswith('/Chart.yaml'):
                        if '/charts/' in member.name:
                            continue  # APISIX etcd/ingress subcharts are disabled by the site values
                        chart = yaml.safe_load(archive.extractfile(member).read())
                        add('helm-chart', chart['name'], str(chart['version']), path,
                            member=member.name, sha256=digest(file))
            finding('inert-default', path, 'Site overrides/disabled chart defaults; rendered images checked separately')
        if path == 'lab/wsl/endpoints/vendor/kourier.yaml.gz':
            finding('inert-default', path, 'Site pins the gateway; upstream latest default must stay inert')
        if path.endswith('.yaml.gz') and '/vendor/' in path:
            # Operator release bundles are real inputs. Ignore CRD schemas/prose,
            # and only omit the exact gateway default replaced by the site lock.
            text = gzip.decompress(file.read_bytes()).decode('utf-8')
            for block in re.split(r'^---\s*$', text, flags=re.M):
                if not re.search(r'^kind: (Deployment|StatefulSet|DaemonSet|Pod|Job|CronJob)\s*$', block, re.M):
                    continue
                doc = yaml.safe_load(block)
                for obj in objects(doc):
                    if path == 'lab/wsl/endpoints/vendor/kourier.yaml.gz' and obj.get('image') == 'docker.io/envoyproxy/envoy:v1.37-latest':
                        continue
                    if isinstance(obj.get('image'), str):
                        image(obj['image'], path)
        if path.endswith(('.yaml', '.yml')) and not path.endswith('.template.yaml') and not path.startswith(('docs/', 'tests/', '.github/')) and '/vendor/' not in path:
            text = file.read_text(encoding='utf-8')
            if '{{' not in text:
                for doc in yaml.safe_load_all(text):
                    walk_images(doc, path)
        if 'Dockerfile' in file.name and not file.name.endswith('.dockerignore'):
            text = file.read_text()
            for base in re.findall(r'^FROM\s+(\S+)', text, re.M):
                image(base, path)
            if 'apt-get install' in text:
                finding('apt-pins', path, 'Record distribution snapshot and exact installed package versions')
        if path.endswith('.txt') and 'images' in file.name and not path.startswith('docs/'):
            for line in file.read_text().splitlines():
                if line.strip() and not line.startswith('#'):
                    image(line.strip(), path)
        if path == '00-setup-ubuntu-host.sh':
            for value in re.findall(r'IMAGE:=\$IMAGE_REGISTRY/([^}\s]+)', file.read_text()):
                image(value, path)
    for file in rendered:
        for doc in yaml.safe_load_all(Path(file).read_text(encoding='utf-8')):
            walk_images(doc, 'rendered:' + Path(file).name)
    # EdgePulse ADRs 0024/0025: Maven joins and the explicitly requested pin inventory.
    from edgepulse_inventory import enumerate_edgepulse
    enumerate_edgepulse(root, tracked, add, image)
    from maven_inventory import enumerate_maven
    register = json.loads((root / 'security/licence-register.json').read_text(encoding='utf-8'))
    enumerate_maven(root, register, add)
    return components, findings
