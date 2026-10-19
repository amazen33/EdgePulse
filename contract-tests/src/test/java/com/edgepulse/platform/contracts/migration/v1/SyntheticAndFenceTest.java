package com.edgepulse.platform.contracts.migration.v1;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.Instant;
import java.time.ZoneId;
import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;

class SyntheticAndFenceTest {
    static void requireSyntheticCredential(JsonNode node) {
        if (node.isTextual()) {
            assertTrue(node.textValue().startsWith("SYNTHETIC-"), "Credential-shaped fixture values need the prefix");
            assertTrue(node.textValue().matches("SYNTHETIC-[A-Za-z0-9-]+"), "Only plainly fake text is allowed");
        } else if (node.isContainerNode()) node.forEach(SyntheticAndFenceTest::requireSyntheticCredential);
        else fail("Credential fixtures contain plainly synthetic text only");
    }

    @Test
    void twoTenantsEachHaveAllCredentialTypesWithFakePrefixedValues() throws Exception {
        JsonNode tenants = ContractFiles.read("fixtures/dataset.json").path("tenants");
        assertEquals(2, tenants.size());
        Set<String> allIds = new HashSet<>();
        for (JsonNode tenant : tenants) {
            assertTrue(allIds.add(tenant.path("id").asText()));
            Set<String> types = new HashSet<>();
            for (JsonNode device : tenant.path("devices")) {
                assertTrue(allIds.add(device.path("id").asText()));
                types.add(device.path("credential_type").asText());
                assertTrue(device.path("credentials").isObject() && !device.path("credentials").isEmpty());
                requireSyntheticCredential(device.path("credentials"));
                if (device.path("credential_type").asText().equals("access-token")) {
                    assertEquals(1, device.path("credentials").size());
                    assertTrue(device.path("credentials").has("value"));
                }
                if (device.path("credential_type").asText().equals("mqtt-basic")) {
                    assertEquals(2, device.path("credentials").size());
                    assertTrue(device.path("credentials").has("username"));
                    assertTrue(device.path("credentials").has("password"));
                }
                if (device.path("credential_type").asText().equals("x509")) {
                    assertEquals(1, device.path("credentials").size());
                    assertTrue(device.path("credentials").has("fingerprint"));
                }
            }
            assertEquals(Set.of("access-token", "x509", "mqtt-basic"), types);
            assertFalse(tenant.path("rule_chain").path("enabled").asBoolean(true));
            assertFalse(tenant.path("historical_alarms").get(0).path("re_raise").asBoolean(true));
            assertTrue(tenant.has("dashboard"));
        }
    }

    @Test
    void syntheticCredentialAssertionRejectsNonTextValues() {
        assertThrows(AssertionError.class, () -> requireSyntheticCredential(
                ContractFiles.JSON.getNodeFactory().booleanNode(false)));
    }

    @Test
    void telemetrySpansMonthAndBothEuropeanDstBoundaries() throws Exception {
        for (JsonNode tenant : ContractFiles.read("fixtures/dataset.json").path("tenants")) {
            JsonNode samples = tenant.path("telemetry");
            ZoneId berlin = ZoneId.of("Europe/Berlin");
            assertNotEquals(at(samples.get(0)).atZone(berlin).getOffset(), at(samples.get(1)).atZone(berlin).getOffset());
            assertNotEquals(at(samples.get(4)).atZone(berlin).getOffset(), at(samples.get(5)).atZone(berlin).getOffset());
            assertEquals("2026-03-31T23:59:59.999Z", at(samples.get(2)).toString());
            assertEquals("2026-04-01T00:00:00Z", at(samples.get(3)).toString());
        }
    }

    private static Instant at(JsonNode sample) {
        return Instant.ofEpochMilli(sample.path("timestamp_epoch_ms").longValue());
    }

    @Test
    void chainHasExactlyTheTwoReviewedSaveNodesAndNoNotificationPaths() throws Exception {
        JsonNode chain = ContractFiles.read("import-safe-root-rule-chain.json");
        JsonNode metadata = chain.path("metadata");
        assertEquals(true, chain.path("ruleChain").path("root").asBoolean());
        assertEquals(false, chain.path("ruleChain").path("debugMode").asBoolean(true));
        assertEquals(0, metadata.path("firstNodeIndex").asInt());
        assertEquals(2, metadata.path("nodes").size());
        Set<String> types = new HashSet<>();
        for (JsonNode node : metadata.path("nodes")) {
            assertTrue(types.add(node.path("type").asText()), "No duplicate or extra save node");
            JsonNode settings = node.path("configuration").path("processingSettings");
            assertEquals("ADVANCED", settings.path("type").asText());
            assertEquals("SKIP", settings.path("webSockets").path("type").asText());
            assertEquals("SKIP", settings.path("calculatedFields").path("type").asText());
        }
        assertEquals(Set.of("org.thingsboard.rule.engine.telemetry.TbMsgTimeseriesNode",
                "org.thingsboard.rule.engine.telemetry.TbMsgAttributesNode"), types);
        assertEquals("ON_EVERY_MESSAGE", metadata.path("nodes").get(0).path("configuration")
                .path("processingSettings").path("timeseries").path("type").asText());
        JsonNode attributes = metadata.path("nodes").get(1).path("configuration");
        assertEquals("ON_EVERY_MESSAGE", attributes.path("processingSettings").path("attributes").path("type").asText());
        assertFalse(attributes.path("notifyDevice").asBoolean(true));
        assertFalse(attributes.path("sendAttributesUpdatedNotification").asBoolean(true));
        assertEquals(1, metadata.path("connections").size());
        JsonNode edge = metadata.path("connections").get(0);
        assertEquals(0, edge.path("fromIndex").asInt());
        assertEquals(1, edge.path("toIndex").asInt());
        assertEquals("Failure", edge.path("type").asText());
        assertTrue(metadata.path("ruleChainConnections").isNull());
    }
}
