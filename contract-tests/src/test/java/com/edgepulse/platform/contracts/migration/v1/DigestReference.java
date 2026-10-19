package com.edgepulse.platform.contracts.migration.v1;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.io.IOException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import org.erdtman.jcs.JsonCanonicalizer;

/** MR-7 reference only, never a runtime dependency or a dataset generator. */
final class DigestReference {
    private DigestReference() { }

    static byte[] canonicalize(String input) throws IOException {
        JsonNode parsed = ContractFiles.JSON.readTree(input);
        if (parsed == null) throw new IllegalArgumentException("Missing JSON value");
        checkUnicode(parsed);
        // Version 1.1 accepts object/array roots. A fixed one-property object
        // also exercises its unchanged JCS serializer for scalar RFC vectors.
        boolean scalar = !parsed.isContainerNode();
        byte[] output = new JsonCanonicalizer(scalar ? "{\"value\":" + input + "}" : input).getEncodedUTF8();
        return scalar ? Arrays.copyOfRange(output, 9, output.length - 1) : output;
    }

    static String hash(byte[] bytes) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException(ex);
        }
    }

    static String digest(JsonNode records) throws IOException {
        if (!records.isArray()) throw new IllegalArgumentException("Records must be an array");
        var ordered = new ArrayList<JsonNode>();
        Set<String> keys = new HashSet<>();
        for (JsonNode record : records) {
            if (!record.isObject() || !record.path("record_id").isTextual()
                    || !record.path("record_id").asText().matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")) {
                throw new IllegalArgumentException("Missing stable record_id");
            }
            if (!keys.add(record.path("record_id").asText())) {
                throw new IllegalArgumentException("Duplicate stable record_id");
            }
            if (record.has("timestamp_epoch_ms")) {
                JsonNode timestamp = record.get("timestamp_epoch_ms");
                if (!timestamp.isIntegralNumber() || !timestamp.canConvertToLong()
                        || timestamp.longValue() < 0 || timestamp.longValue() > 9007199254740991L) {
                    throw new IllegalArgumentException("Timestamp must be a safe UTC epoch-millisecond integer");
                }
            }
            ordered.add(record);
        }
        ordered.sort(Comparator.comparing(n -> n.path("record_id").asText()));
        ArrayNode normalized = ContractFiles.JSON.createArrayNode();
        ordered.forEach(normalized::add);
        return hash(canonicalize(ContractFiles.JSON.writeValueAsString(normalized)));
    }

    private static void checkUnicode(JsonNode node) {
        if (node.isTextual()) requirePairedSurrogates(node.textValue());
        if (node.isObject()) node.fieldNames().forEachRemaining(DigestReference::requirePairedSurrogates);
        if (node.isContainerNode()) node.forEach(DigestReference::checkUnicode);
    }

    private static void requirePairedSurrogates(String value) {
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (Character.isHighSurrogate(c)) {
                if (++i >= value.length() || !Character.isLowSurrogate(value.charAt(i))) {
                    throw new IllegalArgumentException("Unpaired Unicode surrogate");
                }
            } else if (Character.isLowSurrogate(c)) {
                throw new IllegalArgumentException("Unpaired Unicode surrogate");
            }
        }
    }
}
