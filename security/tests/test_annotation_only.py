"""IOT-WO-08: synthetic bytecode fixtures; never execute a scanned class."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zipfile

SECURITY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SECURITY))
from annotation_only import inspect_jar, require_annotation_only

COORDINATES = ('org.synthetic', 'annotations', '1.0.0')


def synthetic_class(name, annotation=True):
    def utf8(value):
        data = value.encode('ascii')
        return b'\x01' + struct.pack('>H', len(data)) + data
    pool = utf8(name) + b'\x07\x00\x01' + utf8('java/lang/Object') + b'\x07\x00\x03'
    if annotation:
        pool += utf8('java/lang/annotation/Annotation') + b'\x07\x00\x05'
    return (b'\xca\xfe\xba\xbe' + struct.pack('>HHH', 0, 52, 7 if annotation else 5)
            + pool + struct.pack('>HHHH', 0x2601 if annotation else 0x0021, 2, 4,
                                 1 if annotation else 0)
            + (b'\x00\x06' if annotation else b'') + b'\x00\x00' * 3)


class AnnotationOnlyTest(unittest.TestCase):
    def setUp(self):
        work = SECURITY.parent / 'target'
        work.mkdir(exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix='annotation-test-', dir=work)
        self.addCleanup(temp.cleanup)
        self.jar = Path(temp.name) / 'SYNTHETIC-annotations.jar'

    def write_jar(self, extra=None):
        with zipfile.ZipFile(self.jar, 'w') as jar:
            jar.writestr('synthetic/Marker.class', synthetic_class('synthetic/Marker'))
            jar.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\n')
            jar.writestr('META-INF/LICENSE', 'SYNTHETIC-licence-text')
            for name, data in (extra or {}).items():
                jar.writestr(name, data)

    def test_annotation_jar_with_manifest_and_licence_passes(self):
        self.write_jar()
        self.assertEqual('passed', require_annotation_only(self.jar, COORDINATES)['status'])

    # Ruling planted violation 1: an annotation-labelled JAR is not enough.
    def test_excluding_jar_with_non_annotation_class_fails(self):
        self.write_jar({'synthetic/Executable.class': synthetic_class('synthetic/Executable', False)})
        with self.assertRaisesRegex(ValueError, 'Class lacks ACC_ANNOTATION: synthetic/Executable.class'):
            require_annotation_only(self.jar, COORDINATES)

    def test_service_loader_and_foreign_maven_metadata_are_not_exempted(self):
        for name in ('META-INF/services/synthetic.Provider', 'META-INF/maven/synthetic/pom.properties'):
            with self.subTest(name=name):
                self.write_jar({name: 'SYNTHETIC-resource'})
                with self.assertRaisesRegex(ValueError, 'Resource not permitted by ruling'):
                    require_annotation_only(self.jar, COORDINATES)

    def test_own_coordinate_maven_metadata_is_permitted(self):
        self.write_jar({'META-INF/maven/org.synthetic/annotations/pom.xml': '<project/>',
                        'META-INF/maven/org.synthetic/annotations/pom.properties':
                        'groupId=org.synthetic\nartifactId=annotations\nversion=1.0.0\n'})
        self.assertEqual('passed', require_annotation_only(self.jar, COORDINATES)['status'])

    def test_truncated_class_fails_closed(self):
        self.write_jar({'synthetic/Truncated.class': b'\xca\xfe\xba\xbe'})
        self.assertIn('synthetic/Truncated.class: Truncated class file', inspect_jar(self.jar, COORDINATES)['errors'])

    def test_renamed_non_annotation_class_cannot_use_descriptor_exception(self):
        self.write_jar({'package-info.class': synthetic_class('synthetic/Executable', False)})
        with self.assertRaisesRegex(ValueError, 'Entry/internal class name mismatch'):
            require_annotation_only(self.jar, COORDINATES)


if __name__ == '__main__':
    unittest.main()
