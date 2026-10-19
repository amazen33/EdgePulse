package com.edgepulse.platform.contracts.migration.v1;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

class DigestContractTest {
    static Stream<Arguments> appendixB() throws Exception {
        var builder = Stream.<Arguments>builder();
        for (JsonNode sample : ContractFiles.read("fixtures/jcs-vectors.json").path("numbers")) {
            builder.add(Arguments.of(sample.path("ieee754").asText(), sample.path("canonical").isNull()
                    ? null : sample.path("canonical").asText()));
        }
        return builder.build();
    }

    @ParameterizedTest
    @MethodSource("appendixB")
    void allRfc8785AppendixBNumberSamples(String bits, String expected) throws Exception {
        double value = Double.longBitsToDouble(Long.parseUnsignedLong(bits, 16));
        String input = Double.toString(value);
        if (expected == null) {
            assertThrows(Exception.class, () -> DigestReference.canonicalize(input));
        } else {
            assertEquals(expected, new String(DigestReference.canonicalize(input), StandardCharsets.UTF_8));
        }
    }

    static Stream<Arguments> canonicalCases() throws Exception {
        var builder = Stream.<Arguments>builder();
        for (JsonNode sample : ContractFiles.read("fixtures/jcs-vectors.json").path("canonicalization")) {
            builder.add(Arguments.of(sample.path("name").asText(), sample.path("input").asText(), sample.path("canonical").asText()));
        }
        return builder.build();
    }

    @ParameterizedTest
    @MethodSource("canonicalCases")
    void appendixEPropertySortingAndOwnCanonicalVectors(String name, String input, String expected) throws Exception {
        byte[] actual = DigestReference.canonicalize(input);
        assertArrayEquals(expected.getBytes(StandardCharsets.UTF_8), actual, name);
        assertArrayEquals(actual, DigestReference.canonicalize(new String(actual, StandardCharsets.UTF_8)));
    }

    @Test
    void checkedInDigestsMatchDeterministicSortedRecordsAndOneFieldChangesTheDigest() throws Exception {
        JsonNode vectors = ContractFiles.read("fixtures/digest-vectors.json").path("vectors");
        for (JsonNode vector : vectors) {
            JsonNode records = vector.path("records");
            assertEquals(vector.path("sha256").asText(), DigestReference.digest(records));
            assertEquals(DigestReference.digest(records), DigestReference.digest(records));
            assertEquals(vector.path("sha256").asText(), DigestReference.hash(
                    vector.path("canonical_utf8").asText().getBytes(StandardCharsets.UTF_8)));
            ArrayNode reversed = ContractFiles.JSON.createArrayNode();
            for (int i = records.size() - 1; i >= 0; i--) reversed.add(records.get(i));
            assertEquals(DigestReference.digest(records), DigestReference.digest(reversed));
        }
        assertNotEquals(vectors.get(0).path("sha256"), vectors.get(1).path("sha256"));
    }

    @Test
    void invalidStableKeysAndNonIntegerTimestampRepresentationsAreRejected() throws Exception {
        ArrayNode records = (ArrayNode) ContractFiles.read("fixtures/digest-vectors.json").path("vectors").get(0).path("records");
        ArrayNode duplicate = records.deepCopy(); duplicate.add(duplicate.get(0));
        assertThrows(IllegalArgumentException.class, () -> DigestReference.digest(duplicate));
        ArrayNode missing = records.deepCopy(); ((ObjectNode) missing.get(0)).remove("record_id");
        assertThrows(IllegalArgumentException.class, () -> DigestReference.digest(missing));
        ArrayNode iso = records.deepCopy(); ((ObjectNode) iso.get(0)).put("timestamp_epoch_ms", "2026-04-01T00:00:00Z");
        assertThrows(IllegalArgumentException.class, () -> DigestReference.digest(iso));
        ArrayNode fraction = records.deepCopy(); ((ObjectNode) fraction.get(0)).put("timestamp_epoch_ms", 1.5);
        assertThrows(IllegalArgumentException.class, () -> DigestReference.digest(fraction));
    }

    @Test
    void duplicatePropertiesTrailingDataAndUnpairedUnicodeAreRejected() {
        assertThrows(Exception.class, () -> DigestReference.canonicalize("{\"a\":1,\"a\":2}"));
        assertThrows(Exception.class, () -> DigestReference.canonicalize("{} {}"));
        assertThrows(Exception.class, () -> DigestReference.canonicalize("{\"a\":\"\\ud800\"}"));
        assertThrows(Exception.class, () -> DigestReference.canonicalize("{\"\\udc00\":1}"));
    }
}
