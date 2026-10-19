package com.edgepulse.platform.contracts.migration.v1;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class OpenApiContractTest {
    private static final String MEDIA = "application/vnd.edgepulse.migration.v1+json";
    private static final Set<String> METHODS = Set.of("get", "post", "put", "delete", "patch", "head", "options");

    @ParameterizedTest
    @ValueSource(strings = {"tenant-lifecycle.openapi.yaml", "reconciliation.openapi.yaml"})
    void parserValidatesAndLintAcceptsEachDocument(String file) throws Exception {
        var options = new ParseOptions();
        options.setResolve(true);
        var result = new OpenAPIV3Parser().readLocation(ContractFiles.ROOT.resolve(file).toUri().toString(), null, options);
        assertNotNull(result.getOpenAPI(), () -> "OpenAPI did not parse: " + result.getMessages());
        assertTrue(result.getMessages().isEmpty(), () -> "Parser validation messages: " + result.getMessages());
        lint(ContractFiles.read(file));
    }

    static void lint(JsonNode document) {
        assertEquals("v1.0.0-draft", document.path("info").path("version").asText());
        assertEquals("com.edgepulse.platform.contracts.migration.v1", document.path("x-namespace").asText());
        assertEquals("migration.operator", document.path("security").get(0).path("MigrationOAuth").get(0).asText());
        Set<String> ids = new HashSet<>();
        document.path("paths").fields().forEachRemaining(path -> {
            assertTrue(path.getKey().contains("{tenant_id}"), "Tenant path required");
            path.getValue().fields().forEachRemaining(entry -> {
                if (!METHODS.contains(entry.getKey())) return;
                JsonNode operation = entry.getValue();
                assertTrue(!operation.path("operationId").asText().isBlank(), "operationId required");
                assertTrue(ids.add(operation.path("operationId").asText()), "Duplicate operationId");
                boolean tenantParameter = false;
                for (JsonNode parameter : operation.path("parameters")) {
                    if (parameter.path("name").asText().equals("tenant_id")) {
                        tenantParameter = parameter.path("in").asText().equals("path")
                                && parameter.path("required").asBoolean();
                    }
                }
                assertTrue(tenantParameter, "Required tenant path parameter missing");
                operation.path("responses").fields().forEachRemaining(response -> {
                    String code = response.getKey();
                    if (code.matches("[45][0-9]{2}")) {
                        assertEquals(Set.of("application/problem+json"), fieldSet(response.getValue().path("content")));
                    } else if (code.startsWith("2")) {
                        assertEquals(Set.of(MEDIA), fieldSet(response.getValue().path("content")));
                    } else fail("Explicit success or problem response required: " + code);
                    inspectSchemas(response.getValue());
                });
                inspectSchemas(operation.path("requestBody"));
            });
        });
        assertFalse(ids.isEmpty());
        inspectSchemas(document.path("components").path("schemas"));
    }

    private static Set<String> fieldSet(JsonNode object) {
        Set<String> names = new HashSet<>();
        object.fieldNames().forEachRemaining(names::add);
        return names;
    }

    private static void inspectSchemas(JsonNode node) {
        if (node.has("properties")) {
            node.path("properties").fieldNames().forEachRemaining(name -> {
                String normalized = name.replaceAll("[^A-Za-z]", "").toLowerCase(java.util.Locale.ROOT);
                for (String forbidden : Set.of("password", "secret", "token", "apikey", "privatekey", "credentialvalue")) {
                    assertFalse(normalized.contains(forbidden), "Forbidden request/response property: " + name);
                }
            });
            assertEquals(false, node.path("additionalProperties").asBoolean(true), "Object schemas must be closed");
        }
        if (node.has("$ref")) assertTrue(node.path("$ref").asText().startsWith("#/components/"), "Only local reviewed references");
        if (node.isContainerNode()) node.forEach(OpenApiContractTest::inspectSchemas);
    }

    @Test
    void lintActuallyRejectsBadErrorMediaMissingTenantAndSensitiveProperty() throws Exception {
        ObjectNode bad = (ObjectNode) ContractFiles.read("tenant-lifecycle.openapi.yaml");
        JsonNode operation = bad.path("paths").elements().next().path("get");
        ((ObjectNode) operation.path("responses").path("400").path("content"))
                .set(MEDIA, ContractFiles.JSON.createObjectNode());
        assertThrows(AssertionError.class, () -> lint(bad));

        ObjectNode missingTenant = (ObjectNode) ContractFiles.read("tenant-lifecycle.openapi.yaml");
        ((ObjectNode) missingTenant.path("paths").elements().next().path("get").path("parameters").get(0))
                .put("required", false);
        assertThrows(AssertionError.class, () -> lint(missingTenant));

        for (String name : Set.of("password", "secret", "token", "apiKey", "privateKey", "credentialValue")) {
            ObjectNode secretProperty = (ObjectNode) ContractFiles.read("tenant-lifecycle.openapi.yaml");
            ((ObjectNode) secretProperty.path("components").path("schemas").path("Tenant").path("properties"))
                    .set(name, ContractFiles.JSON.createObjectNode().put("type", "string"));
            assertThrows(AssertionError.class, () -> lint(secretProperty));
        }
    }

    @Test
    void lifecycleBindsStepUpPurgeAndRunScopedAccess() throws Exception {
        JsonNode api = ContractFiles.read("tenant-lifecycle.openapi.yaml");
        assertTrue(api.path("components").path("securitySchemes").path("MigrationOAuth")
                .path("flows").has("authorizationCode"), "A machine-only grant cannot satisfy human step-up");
        assertEquals(Set.of("cutover", "active"), textSet(api.path("x-step-up-transitions")));
        assertEquals(Set.of("importing", "shadow"), textSet(api.path("x-purge-states")));
        assertFalse(textSet(api.path("x-state-transitions").path("active")).contains("importing"));
        JsonNode transition = api.path("paths").path("/tenants/{tenant_id}/migration/v1/state").path("post");
        String challenge = transition.path("responses").path("401").path("headers")
                .path("WWW-Authenticate").path("example").asText();
        assertEquals("Bearer error=\"insufficient_user_authentication\", acr_values=\"urn:edgepulse:acr:tier1-step-up\"", challenge);
        JsonNode access = api.path("components").path("schemas").path("RunAccessReference");
        assertEquals(Set.of("reference_id", "tenant_id", "run_id", "expires_at_epoch_ms", "revoked"),
                fieldSet(access.path("properties")));
    }

    @Test
    void reconciliationIsReadOnlyBoundedAndHasAnExplicitWatermarkAndSelection() throws Exception {
        JsonNode api = ContractFiles.read("reconciliation.openapi.yaml");
        var path = api.path("paths").elements().next();
        assertEquals(Set.of("get"), fieldSet(path));
        JsonNode operation = path.path("get");
        boolean selection = false, watermark = false, pagination = false;
        for (JsonNode parameter : operation.path("parameters")) {
            switch (parameter.path("name").asText()) {
                case "selection" -> {
                    selection = parameter.path("required").asBoolean() && parameter.path("schema").path("oneOf").size() == 2;
                    assertTrue(parameter.path("description").asText().contains("from < to"));
                }
                case "watermark" -> watermark = parameter.path("required").asBoolean();
                case "page_size" -> pagination = parameter.path("schema").path("maximum").asInt() == 500;
                default -> { }
            }
        }
        assertTrue(selection && watermark && pagination);
        assertTrue(operation.path("description").asText().contains("403, never empty success"));
    }

    private static Set<String> textSet(JsonNode values) {
        Set<String> set = new HashSet<>();
        values.forEach(v -> set.add(v.asText()));
        return set;
    }
}
