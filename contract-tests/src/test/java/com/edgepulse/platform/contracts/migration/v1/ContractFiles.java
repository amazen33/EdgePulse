package com.edgepulse.platform.contracts.migration.v1;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.file.Path;

final class ContractFiles {
    static final Path ROOT = Path.of("..", "contracts", "migration", "v1");
    static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    private ContractFiles() { }

    static JsonNode read(String name) throws IOException {
        // The .yaml documents intentionally use JSON syntax, a YAML 1.2 subset.
        return JSON.readTree(ROOT.resolve(name).toFile());
    }
}
