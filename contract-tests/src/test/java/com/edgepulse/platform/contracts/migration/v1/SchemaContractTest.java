package com.edgepulse.platform.contracts.migration.v1;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.networknt.schema.JsonSchema;
import com.networknt.schema.JsonSchemaFactory;
import com.networknt.schema.SpecVersion;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

class SchemaContractTest {
    private static JsonSchema schema(String stem) throws Exception {
        return JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V202012)
                .getSchema(ContractFiles.read(stem + ".schema.json"));
    }

    @ParameterizedTest
    @ValueSource(strings = {"legacy-inventory", "readiness-report", "migration-run-record"})
    void validFixturePasses(String stem) throws Exception {
        assertTrue(schema(stem).validate(ContractFiles.read("fixtures/" + stem + ".valid.json")).isEmpty());
    }

    @ParameterizedTest
    @CsvSource({"legacy-inventory,legacy-inventory.invalid.json",
            "legacy-inventory,legacy-inventory.invalid-personal-field.json",
            "readiness-report,readiness-report.invalid.json",
            "migration-run-record,migration-run-record.invalid.json"})
    void invalidFixtureFails(String stem, String fixture) throws Exception {
        assertFalse(schema(stem).validate(ContractFiles.read("fixtures/" + fixture)).isEmpty());
    }

    @ParameterizedTest
    @ValueSource(strings = {"password", "secret", "token", "apiKey", "privateKey", "credentialValue"})
    void manifestRejectsCredentialFieldsAtEveryRepresentativeObject(String field) throws Exception {
        JsonSchema schema = schema("legacy-inventory");
        for (String pointer : new String[] {"", "/tb", "/fork", "/devices", "/tenants/0", "/tenants/0/counts"}) {
            JsonNode manifest = ContractFiles.read("fixtures/legacy-inventory.valid.json");
            ((ObjectNode) manifest.at(pointer)).put(field, "SYNTHETIC-FORBIDDEN-VALUE");
            assertFalse(schema.validate(manifest).isEmpty(), pointer + ":" + field);
        }
    }

    @ParameterizedTest
    @ValueSource(strings = {"legacy-inventory", "readiness-report", "migration-run-record"})
    void everyObjectSchemaIsClosed(String stem) throws Exception {
        JsonNode document = ContractFiles.read(stem + ".schema.json");
        assertTrue(document.path("$comment").asText().contains("MR-"));
        assertTrue(document.path("$comment").asText().contains("com.edgepulse.platform.contracts.migration.v1"));
        assertClosed(document);
    }

    private static void assertClosed(JsonNode schema) {
        if (schema.path("type").asText().equals("object")) {
            assertEquals(false, schema.path("additionalProperties").asBoolean(true));
            assertTrue(schema.has("properties"));
        }
        if (schema.isContainerNode()) schema.forEach(SchemaContractTest::assertClosed);
    }

    @Test
    void manifestPermitsTypesButNotAValueSmuggledAsATypeOrBuild() throws Exception {
        JsonSchema schema = schema("legacy-inventory");
        JsonNode manifest = ContractFiles.read("fixtures/legacy-inventory.valid.json");
        ((com.fasterxml.jackson.databind.node.ArrayNode) manifest.path("devices").path("credential_types"))
                .add("SYNTHETIC-NOT-A-CREDENTIAL-TYPE");
        assertFalse(schema.validate(manifest).isEmpty());
        manifest = ContractFiles.read("fixtures/legacy-inventory.valid.json");
        ((ObjectNode) manifest.path("tb")).put("build", "SYNTHETIC-INVALID-BUILD!");
        assertFalse(schema.validate(manifest).isEmpty());
    }

    @Test
    void readinessFixtureCoversEachManifestLeafExactlyOnce() throws Exception {
        JsonNode manifest = ContractFiles.read("fixtures/legacy-inventory.valid.json");
        JsonNode report = ContractFiles.read("fixtures/readiness-report.valid.json");
        Set<String> expected = new HashSet<>();
        collectLeaves(manifest, "", expected);
        Set<String> actual = new HashSet<>();
        Set<String> statuses = new HashSet<>();
        for (JsonNode item : report.path("items")) {
            assertTrue(actual.add(item.path("manifest_pointer").asText()), "Duplicate manifest item");
            statuses.add(item.path("status").asText());
        }
        assertEquals(expected, actual);
        assertEquals(Set.of("supported", "needs-work", "blocked"), statuses);
        assertEquals(DigestReference.hash(DigestReference.canonicalize(ContractFiles.JSON.writeValueAsString(manifest))),
                report.path("manifest_sha256").asText());
    }

    private static void collectLeaves(JsonNode node, String path, Set<String> output) {
        if (node.isObject() && !node.isEmpty()) {
            node.fields().forEachRemaining(e -> collectLeaves(e.getValue(), path + "/" + e.getKey(), output));
        } else if (node.isArray() && !node.isEmpty()) {
            for (int i = 0; i < node.size(); i++) collectLeaves(node.get(i), path + "/" + i, output);
        } else output.add(path);
    }
}
