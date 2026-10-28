# Java 21 build baseline — IOT-WO-02 Part C

The root Maven compiler target is release 21. All four Java-running CI
workflows use Temurin 21.0.12.1+1, a stable release published 2026-08-19;
the selected Windows asset was published 2026-08-21. Both precede the
2026-10-22 pin review by more than 14 days. Exact asset hashes, source
licence evidence and publication timestamps are in the
[tool evidence](../../security/evidence/iot-wo-02-c/temurin-21-2026-10-22.json).

The pinned setup-java action uses Adoptium's SemVer spelling
`21.0.12+101.0.LTS`, while the actual JDK reports `21.0.12.1+1-LTS`.
The official package metadata binds those representations. The action's
existing `isVersionSatisfies` uses exact `compareBuild` matching when a
build-qualified version is provided; omitting `.LTS` would not be the same
exact pin. The action SHA is unchanged.

Temurin remains a `build-tool` under ADR 0026 Decision 1, elected
`GPL-2.0-only WITH Classpath-exception-2.0`. Its register entry binds both
Linux x64 and Windows x64 archive SHA-256 values. Official checksum-file
bytes and asset digests were compared; the local Windows archive was
hashed before extraction. No JDK is added to an application archive, and
no container image or runtime dependency version is changed.

Spring Boot 3.3.4, Spring Cloud 2023.0.3, the Log4j BOM override and all
Maven dependency/plugin versions remain unchanged. The supported Spring
line upgrade and re-evaluation of the Log4j override are separate Part C
work. No Part D quality tooling or gate relaxation is included. The existing
Part C trial worktree is outside this task's scope.

## Java 21 test instrumentation

The first local Java 21 run failed Mockito's dynamic attachment. The failed
initialization then produced secondary logging recursion in Spring test
context setup. A diagnostic using the existing registered Byte Buddy agent
at JVM startup passed all 214 identity and 61 contract tests.

The identity module now runs the already-registered Dependency Plugin
3.11.0 `properties` goal at `initialize`, exposing resolved artifact paths.
Surefire starts its test JVM with that resolved `byte-buddy-agent` JAR.
There is no dependency version or framework change, no dynamic-attach waiver,
no skipped test and no application JVM/packaging change. The empty parent
`argLine` and late evaluation preserve other explicitly configured test agents.
The plugin's existing full classpath remains in the gated inventory.

## Verification and limits

The Java-only PR links the full `mvn -B -f pom.xml verify` result, test counts,
resolved dependency comparison, licence/supply-chain gates and exact CI head.
The Java 17 baseline dependency trees were saved before the compiler/JDK
change for comparison with the Java 21 collector. The comparison covers
coordinates, versions, resolved scopes, classifiers and dependency edges.

These are build/CI compatibility checks. A green Java-only PR does not
accept MS1, establish a supported Spring baseline, authorize deployment or
prove real-environment integration. Amendment 5 moves Part C before Part D;
the owner still reviews and merges each PR, and accepts the eventual MS1
receipt. Accepted ADRs and existing legacy admissions/deadlines are unchanged.
