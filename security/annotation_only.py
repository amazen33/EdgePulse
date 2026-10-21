"""IOT-WO-08 ruling 2026-10-21: inspect exact annotation JARs, never execute.

This is exclusion evidence, not a runtime licence admission or gate exemption.
Only manifest, licence, notice and own-coordinate Maven metadata resources
are accepted by the ruling and its 2026-10-21 clarification.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import zipfile


def class_header(data):
    """Read JVM constant-pool entries to reach access_flags and this_class."""
    offset = 0

    def take(size):
        nonlocal offset
        if offset + size > len(data):
            raise ValueError('Truncated class file')
        result = data[offset:offset + size]
        offset += size
        return result

    def u2():
        return struct.unpack('>H', take(2))[0]

    if take(4) != b'\xca\xfe\xba\xbe':
        raise ValueError('Invalid class-file magic')
    take(4)  # minor_version and major_version
    count = u2()
    pool = [None] * count
    index = 1
    while index < count:
        tag = take(1)[0]
        if tag == 1:
            pool[index] = ('utf8', take(u2()))
        elif tag == 7:
            pool[index] = ('class', u2())
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            take(4)
        elif tag in (5, 6):
            take(8)
            index += 1
            if index >= count:
                raise ValueError('Invalid two-slot constant-pool entry')
        elif tag in (8, 16, 19, 20):
            take(2)
        elif tag == 15:
            take(3)
        else:
            raise ValueError('Unknown constant-pool tag: ' + str(tag))
        index += 1
    flags, this_class = u2(), u2()
    try:
        entry = pool[this_class]
        if entry[0] != 'class' or pool[entry[1]][0] != 'utf8':
            raise ValueError('Invalid this_class constant')
        # Internal names of these public artifacts use ASCII; modified UTF-8
        # names outside that set fail closed rather than being misidentified.
        name = pool[entry[1]][1].decode('ascii')
    except (IndexError, TypeError, UnicodeDecodeError) as error:
        raise ValueError('Invalid class name constant') from error
    return flags, name


def permitted_resource(name, coordinates):
    path = PurePosixPath(name)
    if name == 'META-INF/MANIFEST.MF':
        return True
    group, artifact, _ = coordinates
    if name in (f'META-INF/maven/{group}/{artifact}/pom.xml',
                f'META-INF/maven/{group}/{artifact}/pom.properties'):
        return True
    if path.parent.as_posix() not in ('.', 'META-INF'):
        return False
    return path.name.upper() in {
        stem + suffix for stem in ('LICENSE', 'LICENCE', 'NOTICE')
        for suffix in ('', '.TXT', '.MD')
    }


def inspect_jar(path, coordinates):
    path = Path(path)
    if len(coordinates) != 3 or any(not value or '/' in value or '\\' in value
                                    or ':' in value or value in ('.', '..') for value in coordinates):
        raise ValueError('Exact groupId:artifactId:version required')
    result = dict(coordinates=':'.join(coordinates), jar=path.name,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  status='passed', classes=[], resources=[], errors=[])
    seen = set()
    with zipfile.ZipFile(path) as jar:
        for item in jar.infolist():
            name = item.filename
            if (name in seen or '\\' in name or name.startswith('/')
                    or '..' in PurePosixPath(name).parts):
                result['errors'].append('Duplicate or unsafe JAR entry: ' + name)
                continue
            seen.add(name)
            if item.is_dir():
                continue
            if name.endswith('.class'):
                try:
                    flags, internal = class_header(jar.read(item))
                    parts = PurePosixPath(name).parts
                    expected = ('/'.join(parts[3:]) if len(parts) > 3 and
                                parts[:2] == ('META-INF', 'versions') and parts[2].isdigit()
                                else name)[:-6]
                    if internal != expected:
                        raise ValueError('Entry/internal class name mismatch')
                    annotation = bool(flags & 0x2000)
                    descriptor = internal.rsplit('/', 1)[-1] in ('package-info', 'module-info')
                    result['classes'].append(dict(entry=name, accessFlags=f'0x{flags:04x}',
                                                  annotation=annotation, descriptor=descriptor))
                    if not annotation and not descriptor:
                        result['errors'].append('Class lacks ACC_ANNOTATION: ' + name)
                except (ValueError, struct.error) as error:
                    result['errors'].append(name + ': ' + str(error))
            else:
                permitted = permitted_resource(name, coordinates)
                result['resources'].append(dict(entry=name, permitted=permitted))
                if not permitted:
                    result['errors'].append('Resource not permitted by ruling: ' + name)
    if not any(c['annotation'] for c in result['classes']):
        result['errors'].append('No annotation type found')
    if result['errors']:
        result['status'] = 'failed'
    return result


def require_annotation_only(path, coordinates):
    result = inspect_jar(path, coordinates)
    if result['status'] != 'passed':
        raise ValueError('; '.join(result['errors']))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', action='append', required=True,
                        help='Exact groupId:artifactId:version=JAR path (repeatable)')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    artifacts = [value.split('=', 1) for value in args.artifact]
    if any(len(value) != 2 for value in artifacts):
        parser.error('--artifact requires groupId:artifactId:version=JAR path')
    results = [inspect_jar(path, tuple(coordinate.split(':'))) for coordinate, path in artifacts]
    report = dict(rule='IOT-WO-08 annotation-only artifacts introduced by a refresh (2026-10-21)',
                  status='passed' if all(r['status'] == 'passed' for r in results) else 'failed',
                  artifacts=results)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    for result in results:
        print(result['jar'] + ': ' + result['status'] + '; sha256=' + result['sha256'])
        for entry in result['classes']:
            print('  ' + entry['entry'] + ' ' + entry['accessFlags'])
        for error in result['errors']:
            print('  REJECT: ' + error)
    return int(report['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())
