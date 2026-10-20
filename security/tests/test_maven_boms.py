"""IOT-WO-06 ruling 2026-10-21: exercise real pinned Maven model semantics."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'security'))
from maven_boms import inputs, raw_sha


class ImportedModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT/'target', prefix='bom-model-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'security').mkdir()
        (self.root/'security/ImportedBoms.java').write_bytes((ROOT/'security/ImportedBoms.java').read_bytes())
        (self.root/'security/licence-policy.json').write_text(json.dumps(dict(gatedMavenCommands=[dict(profiles=[])])))
        self.cache = self.root/'cache'
        self.home = ROOT/'target/licence-tools/apache-maven-3.9.11'
        self.effective = self.root/'effective.xml'
        self.effective.write_text(self.model('<dependencyManagement><dependencies>' + self.library() +
            '</dependencies></dependencyManagement>'))
        (self.root/'pom.xml').write_text(self.model('<groupId>org.synthetic</groupId>'
            '<artifactId>SYNTHETIC-project</artifactId><version>1</version>'
            '<dependencyManagement><dependencies>'+self.imported('direct-bom','1.0')+
            '</dependencies></dependencyManagement>'))
        self.pom('parent','1.0','<properties><nested.version>1.1</nested.version></properties>'
            '<dependencyManagement><dependencies>'+self.imported('nested-bom','${nested.version}')+
            '</dependencies></dependencyManagement>')
        self.pom('nested-bom','1.1','<dependencyManagement><dependencies>'+self.library()+
            '</dependencies></dependencyManagement>')
        self.pom('direct-bom','1.0','<parent><groupId>org.synthetic</groupId><artifactId>parent</artifactId>'
            '<version>1.0</version><relativePath/></parent>')

    @staticmethod
    def model(body):
        return '<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion>'+body+'</project>'

    @staticmethod
    def imported(name, version):
        return '<dependency><groupId>org.synthetic</groupId><artifactId>'+name+'</artifactId><version>'+version+\
            '</version><type>pom</type><scope>import</scope></dependency>'

    @staticmethod
    def library():
        return '<dependency><groupId>org.synthetic</groupId><artifactId>SYNTHETIC-library</artifactId>'\
            '<version>2.0</version></dependency>'

    def pom(self, artifact, version, body, packaging='pom'):
        path = self.cache/'org/synthetic'/artifact/version/(artifact+'-'+version+'.pom')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model(body+'<groupId>org.synthetic</groupId><artifactId>'+artifact+
            '</artifactId><version>'+version+'</version><packaging>'+packaging+'</packaging>'
            '<licenses><license><name>MIT</name><url>https://example.invalid/SYNTHETIC-licence</url>'
            '</license></licenses>'))
        return path

    def test_nested_import_inherited_from_parent_is_mechanically_discovered(self):
        result = inputs(self.root, self.home, self.cache, self.effective)
        self.assertEqual({('org.synthetic:direct-bom','1.0'),('org.synthetic:nested-bom','1.1')},
                         {(c['name'],c['version']) for c in result['components']})
        for c in result['components']:
            artifact = c['name'].split(':')[1]
            self.assertEqual(raw_sha(self.cache/'org/synthetic'/artifact/c['version']/
                             (artifact+'-'+c['version']+'.pom')), c['sha256'])
        self.assertIn('org.synthetic:parent:1.0',result['modelSources'])

    def test_effective_model_disagreement_fails(self):
        self.effective.write_text(self.effective.read_text().replace('<version>2.0</version>','<version>2.1</version>'))
        with self.assertRaisesRegex(ValueError, 'differs from gated Maven effective model'):
            inputs(self.root, self.home, self.cache, self.effective)

    def test_imported_non_pom_packaging_fails(self):
        self.pom('nested-bom','1.1','',packaging='jar')
        with self.assertRaisesRegex(ValueError, 'Imported BOM is not POM-only'):
            inputs(self.root, self.home, self.cache, self.effective)


if __name__ == '__main__':
    unittest.main()
