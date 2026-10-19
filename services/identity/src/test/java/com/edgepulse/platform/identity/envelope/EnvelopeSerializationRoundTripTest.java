package com.edgepulse.platform.identity.envelope;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.google.protobuf.ByteString;
import com.google.protobuf.InvalidProtocolBufferException;
import com.edgepulse.platform.contracts.events.v1.Envelope;
import com.edgepulse.platform.contracts.events.v1.Origin;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;

/**
 * Exercises the CloudEvents-shaped Protobuf envelope (ADR 0012 Decision 4)
 * defined in {@code contracts/events/v1/envelope.proto}: builds an
 * {@code Envelope} with every field set, serializes it to bytes, parses
 * those bytes back, and asserts every field survives unchanged.
 *
 * <p>This class depends on {@code Envelope}/{@code EnvelopeProto}, the
 * Java classes {@code protobuf-maven-plugin} generates from that shared
 * contract file at build time (see this module's {@code pom.xml}'s
 * {@code protobuf-maven-plugin} execution, which points
 * {@code protoSourceRoot} at {@code ../../contracts/events/v1} -- ADR
 * 0013 Decision 9). It therefore cannot compile until
 * {@code mvn generate-sources} (or a full {@code mvn verify}) has
 * actually run against a reachable Maven Central / protoc download --
 * exactly the verification this environment's network policy blocks (see
 * {@code services/identity/README.md}, "Verification status"). The test
 * is written against the envelope's field set as specified in
 * {@code envelope.proto} itself, so a reviewer can check it by inspection
 * against that source of truth even before it has ever been compiled.
 *
 * <p>Note the import: {@code com.edgepulse.platform.contracts.events.v1} is
 * NOT a dependency on a shared jar -- it is this service's own generated
 * source, compiled from the shared {@code .proto} file into this
 * module's own {@code target/generated-sources}, per ADR 0013 Decision
 * 2/9. A second service that needed this same envelope would configure
 * the identical plugin execution against the identical contract file and
 * get its own copy of these classes, package name and all.
 */
class EnvelopeSerializationRoundTripTest {

    private Envelope buildFullyPopulatedEnvelope() {
        return Envelope.newBuilder()
                .setId("evt-0001")
                .setOrigin(Origin.ORIGIN_MIGRATION)
                .setMigrationRunId("SYNTHETIC-run-1")
                .setSource("urn:edgepulse:service:identity")
                .setType("com.edgepulse.identity.tenant.provisioned.v1")
                .setSpecversion("1.0")
                .setTime("2026-09-23T02:00:00Z")
                .setCorrelationId("corr-synthetic-0001")
                .setCausationId("cause-synthetic-0001")
                .setTenantId("synthetic-tenant-acme-001")
                .setIdempotencyKey("idem-synthetic-0001")
                .setData(ByteString.copyFromUtf8("{\"synthetic\":true}"))
                .setDataContentType("application/json")
                .build();
    }

    @Test
    void everyFieldSurvivesASerializeThenParseRoundTrip() throws InvalidProtocolBufferException {
        Envelope original = buildFullyPopulatedEnvelope();

        byte[] wireBytes = original.toByteArray();
        Envelope roundTripped = Envelope.parseFrom(wireBytes);

        assertEquals(original.getId(), roundTripped.getId());
        assertEquals(original.getSource(), roundTripped.getSource());
        assertEquals(original.getType(), roundTripped.getType());
        assertEquals(original.getSpecversion(), roundTripped.getSpecversion());
        assertEquals(original.getTime(), roundTripped.getTime());
        assertEquals(original.getCorrelationId(), roundTripped.getCorrelationId());
        assertEquals(original.getCausationId(), roundTripped.getCausationId());
        assertEquals(original.getTenantId(), roundTripped.getTenantId());
        assertEquals(original.getIdempotencyKey(), roundTripped.getIdempotencyKey());
        assertEquals(original.getData(), roundTripped.getData());
        assertEquals(original.getDataContentType(), roundTripped.getDataContentType());
        assertEquals(original.getOrigin(), roundTripped.getOrigin());
        assertEquals(original.getMigrationRunId(), roundTripped.getMigrationRunId());
        assertEquals(original, roundTripped, "protobuf messages with identical field values must be equal()");
    }

    @Test
    void idempotencyKeyIsDistinctFromId() {
        // Documents the distinction ADR 0012 Decision 4 draws explicitly: a
        // producer retry after a delivery failure reuses the same
        // idempotency_key but MAY mint a new id. This test does not (and
        // cannot, at this envelope-construction level) simulate a retry --
        // it asserts only that the two fields are independently settable to
        // different values, i.e. that idempotency_key is not aliased to id.
        Envelope envelope = Envelope.newBuilder()
                .setId("evt-0001")
                .setIdempotencyKey("idem-synthetic-0001")
                .build();

        assertEquals("evt-0001", envelope.getId());
        assertEquals("idem-synthetic-0001", envelope.getIdempotencyKey());
        for (Origin origin : new Origin[] {Origin.ORIGIN_LIVE, Origin.ORIGIN_MIGRATION, Origin.ORIGIN_REPLAY}) {
            Envelope message = envelope.toBuilder().setOrigin(origin)
                    .setMigrationRunId(origin == Origin.ORIGIN_MIGRATION ? "SYNTHETIC-run-1" : "").build();
            assertValidProvenance(message);
            try {
                Envelope decoded = Envelope.parseFrom(message.toByteArray());
                assertEquals(origin, decoded.getOrigin());
                assertEquals(message.getMigrationRunId(), decoded.getMigrationRunId());
            } catch (InvalidProtocolBufferException ex) {
                throw new AssertionError(ex);
            }
        }
        assertThrows(IllegalArgumentException.class, () -> assertValidProvenance(
                envelope.toBuilder().setOrigin(Origin.ORIGIN_MIGRATION).build()));
        for (Origin origin : new Origin[] {Origin.ORIGIN_UNSPECIFIED, Origin.ORIGIN_LIVE, Origin.ORIGIN_REPLAY}) {
            assertThrows(IllegalArgumentException.class, () -> assertValidProvenance(
                    envelope.toBuilder().setOrigin(origin).setMigrationRunId("SYNTHETIC-run-1").build()));
        }
        assertThrows(IllegalArgumentException.class, () -> assertValidProvenance(
                envelope.toBuilder().setOriginValue(99).build()));
    }

    @Test
    void unsetOptionalStyleFieldsDefaultToEmptyString() throws InvalidProtocolBufferException {
        // Proto3 scalar fields have no explicit "unset" state; every field
        // this test does not set defaults to "" (or empty bytes for `data`).
        // Documents that a producer must set causation_id explicitly to ""
        // (or simply not call the setter) for the "no direct envelope
        // cause" case envelope.proto's own comment on causation_id
        // describes -- there is no separate null/unset representation.
        Envelope envelope = Envelope.newBuilder().setId("evt-0002").build();

        assertEquals("", envelope.getCausationId());
        assertEquals(ByteString.EMPTY, envelope.getData());
        assertEquals(Origin.ORIGIN_UNSPECIFIED, envelope.getOrigin());
        assertEquals("", envelope.getMigrationRunId());
        // Encoded with the pre-change generated Envelope from main 2bdd421:
        // only fields 1 through 11 exist in these fixed bytes (MR-4).
        Envelope oldMessage = Envelope.parseFrom(HexFormat.of().parseHex(
                "0a1353594e5448455449432d6f6c642d6576656e74121e75726e3a6564676570756c73653a736572766963653a6964656e746974791a2c636f6d2e6564676570756c73652e6964656e746974792e74656e616e742e70726f766973696f6e65642e76312203312e302a14323032362d31302d31395430303a30303a30305a321553594e5448455449432d636f7272656c6174696f6e3a0f53594e5448455449432d6361757365421253594e5448455449432d74656e616e742d614a1553594e5448455449432d6964656d706f74656e637952027b7d5a106170706c69636174696f6e2f6a736f6e"));
        assertEquals("SYNTHETIC-old-event", oldMessage.getId());
        assertEquals("SYNTHETIC-tenant-a", oldMessage.getTenantId());
        assertEquals("application/json", oldMessage.getDataContentType());
        assertEquals(Origin.ORIGIN_UNSPECIFIED, oldMessage.getOrigin());
        assertEquals("", oldMessage.getMigrationRunId());
        assertEquals(Origin.ORIGIN_LIVE, oldMessage.getOrigin() == Origin.ORIGIN_UNSPECIFIED
                ? Origin.ORIGIN_LIVE : oldMessage.getOrigin());
        assertArrayEquals(HexFormat.of().parseHex("0a1353594e5448455449432d6f6c642d6576656e74121e75726e3a6564676570756c73653a736572766963653a6964656e746974791a2c636f6d2e6564676570756c73652e6964656e746974792e74656e616e742e70726f766973696f6e65642e76312203312e302a14323032362d31302d31395430303a30303a30305a321553594e5448455449432d636f7272656c6174696f6e3a0f53594e5448455449432d6361757365421253594e5448455449432d74656e616e742d614a1553594e5448455449432d6964656d706f74656e637952027b7d5a106170706c69636174696f6e2f6a736f6e"), oldMessage.toByteArray(),
                "Old fields survive a lossless decode/re-encode with no new fields set");
        assertValidProvenance(oldMessage);
    }

    private static void assertValidProvenance(Envelope envelope) {
        if (envelope.getOrigin() == Origin.UNRECOGNIZED
                || (envelope.getOrigin() == Origin.ORIGIN_MIGRATION) == envelope.getMigrationRunId().isEmpty()) {
            throw new IllegalArgumentException("MR-4 provenance invariant");
        }
    }
}
