# Per-class reconciliation digest (MR-7)

Version: **v1.0.0-draft**. Namespace:
`com.edgepulse.platform.contracts.migration.v1`. Additive changes only within v1;
the canonicalization, key, projection interpretation and byte framing below
cannot change within this major version.

1. Select one authorized tenant, one `data-classes.json` class and one fixed
   source position/watermark. Select either a half-open UTC interval
   `[from_epoch_ms, to_epoch_ms)` with `from < to`, or an as-of snapshot. Refuse
   cross-tenant device filters and mixed/moving watermarks. `to` is excluded;
   snapshot records are taken at the stated as-of position. Count and digest
   describe the entire selection, regardless of transport page boundaries.
2. Both sides construct the same versioned, approved **redacted projection**.
   Each record has `record_id`: an immutable, tenant/class-scoped stable source
   key, encoded as ASCII `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`. Where TB IDs change,
   use the consumer's authoritative identity map before projecting. Duplicate or
   absent keys are errors, never silently deduplicated. No secrets, personal
   fields, raw dumps or executable scripts are part of a projection. Credential
   reconciliation uses approved salted fingerprints only, never credential values.
   A projection version and field mapping must be agreed before a real run;
   this specification does not invent the unknown legacy mapping.
3. Temporal records use **integer UTC epoch milliseconds** in
   `timestamp_epoch_ms`, from 0 through 9007199254740991 inclusive. Convert source
   time zones and higher precision at the mapping boundary under an explicit
   agreed policy; the digest reference rejects strings, fractions and out-of-range
   timestamps instead of silently changing precision. Non-temporal records omit
   this property and use the snapshot selector. DST/local display has no effect
   on the integer representation.
4. Sort all selected records by `record_id`, ascending lexicographic order of
   UTF-16 code units (identical to ASCII ordering for the stated key alphabet).
   Do not sort arrays inside a projected record. JSON objects are not compared
   by their original property order.
5. Put the ordered records in **one JSON array** and canonicalize that entire
   array using [RFC 8785 JCS](https://www.rfc-editor.org/rfc/rfc8785.html).
   JCS recursively sorts object property names by UTF-16 code units, preserves
   array order, normalizes finite binary64 numbers using ECMAScript serialization,
   emits negative zero as zero, and applies its string escaping rules. Reject
   duplicate properties, lone Unicode surrogates, non-finite numbers, malformed
   JSON and trailing values. Do not apply Unicode normalization. Identifiers or
   exact quantities that cannot be represented by the agreed binary64 domain
   must be mapped to strings before reconciliation, never silently rounded by
   a different decimal algorithm.
6. Encode the canonical array as UTF-8 with **no BOM, separator or trailing
   newline**. The array brackets/commas provide unambiguous record boundaries;
   do not hash concatenated unframed record texts. Compute **SHA-256**, rendered
   as exactly 64 lowercase hexadecimal characters. The empty selection hashes
   the two bytes `[]`; its digest is
   `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.

The response binds tenant, class, selector, watermark, count and digest together.
Comparators verify those scope fields before comparing digests. Cursors are
opaque, bound to that scope and page size, and cannot be moved between tenants
or selections. A server must not compute a separate digest for each transport
page and present it as the per-class result.

## Test-scope reference and vectors

`contract-tests/src/test/java/com/edgepulse/platform/contracts/migration/v1/DigestReference.java`
uses the pinned Apache-2.0 JCS implementation and the JDK SHA-256 implementation.
Its strict input checks and stable-key sorter are test code only. The JCS library
version accepts object/array roots; scalar conformance vectors are wrapped in a
fixed one-property object and its framing removed after canonicalization. Number
and string serialization still use the library without reimplementing JCS.

`fixtures/jcs-vectors.json` includes every RFC 8785 Appendix B IEEE-754 sample,
including rejection cases, Appendix E string subtype handling, section 3.2.3
UTF-16 ordering, and our own nested ordering/number example. The address and key
illustrations from other appendices are not copied into fixtures; no personal
data or key material is needed for canonicalization tests. The numeric values
and expected canonical bytes are standards conformance vectors.

`fixtures/digest-vectors.json` fixes the ordered canonical array and SHA-256 for
our own small month-boundary projections, a one-field change and the empty
selection. The digest expectations were independently calculated from the
checked-in canonical UTF-8 strings. Tests compare them with the Java reference,
repeat the same input, reverse input order, and show that a one-field change
changes the digest. These vectors are portable acceptance inputs for the consumer;
no runtime Java library is shared with it.
