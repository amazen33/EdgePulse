#!/usr/bin/env python3
"""Linux CI tool staging: fixed URLs, verified bytes, and explicit archive members.

Nothing is extracted wholesale or installed on the host. A checksum failure is
fatal; mutable upstream URLs never silently advance the selected dependency.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent


def verified(data, digest):
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Downloaded artifact SHA256 mismatch')
    return data


def extract_member(archive, member):
    path = PurePosixPath(member)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe archive member path')
    with tarfile.open(archive, 'r:*') as stream:
        info = stream.getmember(member)
        if not info.isfile() or info.issym() or info.islnk():
            raise ValueError('Only a regular archive file may be staged')
        return stream.extractfile(info).read()


def extract_runtime(archive, destination):
    """Stage a checksum-verified multi-file runtime; reject links and escapes."""
    with tarfile.open(archive,'r:*') as stream:
        seen=set();size=0
        for info in stream.getmembers():
            path=PurePosixPath(info.name)
            if path.is_absolute() or '..' in path.parts or '\\' in info.name or ':' in info.name or info.issym() or info.islnk():
                raise ValueError('Unsafe runtime archive member')
            if info.isdir():continue
            if not info.isfile() or path in seen:
                raise ValueError('Runtime requires unique regular files')
            seen.add(path);size+=info.size
            if len(seen)>20000 or size>1024**3:raise ValueError('Runtime archive exceeds bounds')
            target=destination/Path(*path.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(stream.extractfile(info).read())
            target.chmod(0o755 if info.mode & 0o111 else 0o644)


def stage(destination, only=None):
    destination.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / 'toolchain.lock.json').read_text())
    if only and set(only)-set(lock['artifacts']):raise ValueError('Unknown tool selection')
    for name, artifact in lock['artifacts'].items():
        if only and name not in only:continue
        relative = PurePosixPath(artifact['output'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe artifact output path')
        cache = destination / 'downloads' / name
        cache.parent.mkdir(parents=True, exist_ok=True)
        if cache.exists():
            data = verified(cache.read_bytes(), artifact['sha256'])
        else:
            with urllib.request.urlopen(artifact['url'], timeout=120) as response:
                data = verified(response.read(), artifact['sha256'])
            cache.write_bytes(data)
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        if artifact.get('runtimeArchive'):
            extract_runtime(cache,output.parent)
            output.chmod(0o755)
            launcher=destination/'bin/pwsh';launcher.parent.mkdir(parents=True,exist_ok=True)
            launcher.write_text('#!/usr/bin/env bash\nset -Eeuo pipefail\nexec '+shlex.quote(str(output))+' "$@"\n',encoding='utf-8')
            launcher.chmod(0o755)
        else:
            binary=extract_member(cache, artifact['member']) if artifact.get('member') else data
            if artifact.get('binarySHA256'):verified(binary,artifact['binarySHA256'])
            output.write_bytes(binary)
        if relative.parts[0] == 'bin':
            output.chmod(0o755)
        print('Verified ' + name, flush=True)


def wrapper(destination, source):
    # The bootstrap's embedded post-renderer requests default schemas. Prepend
    # local strict schemas so the tests exercise it without schema network calls.
    templates = [destination / 'schemas' / '{{.ResourceKind}}.json',
                 source / 'module-2/schemas' / '{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json',
                 source / 'module-2/schemas' / '{{.ResourceKind}}_{{.ResourceAPIVersion}}.json']
    # Module 2's actual schema locations are included explicitly by its validator.
    flags = ' '.join('-schema-location ' + shlex.quote(str(path)) for path in templates)
    script = '#!/usr/bin/env bash\nset -Eeuo pipefail\nexec ' + shlex.quote(str(destination / 'bin/kubeconform-real')) + ' ' + flags + ' "$@"\n'
    target = destination / 'bin/kubeconform'
    target.write_text(script, encoding='utf-8', newline='\n')
    target.chmod(0o755)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--only', nargs='+', help='Stage only named pinned artifacts')
    args = parser.parse_args()
    stage(args.destination.resolve(),args.only)
    if not args.only or 'kubeconform' in args.only:
        wrapper(args.destination.resolve(), args.source.resolve())
