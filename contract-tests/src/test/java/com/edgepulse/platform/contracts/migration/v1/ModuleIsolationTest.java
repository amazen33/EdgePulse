package com.edgepulse.platform.contracts.migration.v1;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Files;
import java.nio.file.Path;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.xpath.XPathConstants;
import javax.xml.xpath.XPathFactory;
import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;

class ModuleIsolationTest {
    private static Document pom(Path path) throws Exception {
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        return factory.newDocumentBuilder().parse(path.toFile());
    }

    @Test
    void moduleHasNoMainCodeAndNoReactorModuleConsumesIt() throws Exception {
        assertFalse(Files.exists(Path.of("src", "main")), "Only test sources belong here");
        var xpath = XPathFactory.newInstance().newXPath();
        Document root = pom(Path.of("..", "pom.xml"));
        NodeList modules = (NodeList) xpath.evaluate("/project/modules/module", root, XPathConstants.NODESET);
        assertTrue(modules.getLength() >= 3);
        for (int i = 0; i < modules.getLength(); i++) {
            Document module = pom(Path.of("..").resolve(modules.item(i).getTextContent()).resolve("pom.xml"));
            NodeList forbidden = (NodeList) xpath.evaluate(
                    "//dependencies/dependency[artifactId='edgepulse-contract-tests']", module, XPathConstants.NODESET);
            assertEquals(0, forbidden.getLength(), "No dependency allowed, including test scope");
        }
    }

    @Test
    void inheritedEnforcerBanHasNoScopeOrTransitivityEscape() throws Exception {
        var xpath = XPathFactory.newInstance().newXPath();
        Document root = pom(Path.of("..", "pom.xml"));
        String rule = "/project/build/plugins/plugin[artifactId='maven-enforcer-plugin']/executions/"
                + "execution[id='enforce-contract-tests-not-consumable']/configuration/rules/bannedDependencies";
        assertEquals("com.edgepulse.platform:edgepulse-contract-tests", xpath.evaluate(rule + "/excludes/exclude", root));
        assertEquals("", xpath.evaluate(rule + "/includes", root));
        assertNotEquals("false", xpath.evaluate(rule + "/searchTransitive", root));
    }
}
