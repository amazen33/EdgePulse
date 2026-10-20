# Exact build-tool licence evidence

Read on 2026-10-20. Custom permissive grants are allowed only for build tools
under the IOT-WO-02 ruling and ADR 0026. The gate checks their stored full text
and its SHA-256; they do not admit a shipped component.

| Component | Recorded licence | Full text | Exact source |
| --- | --- | --- | --- |
| `io.github.x-stream:mxparser:1.2.2` | `LicenseRef-Indiana-Extreme-mxparser-1.2.2` | [LicenseRef-Indiana-Extreme-mxparser-1.2.2.txt](LicenseRef-Indiana-Extreme-mxparser-1.2.2.txt) | [Artifact/version](https://repo.maven.apache.org/maven2/io/github/x-stream/mxparser/1.2.2/mxparser-1.2.2.jar) |
| `org.jdom:jdom2:2.0.6.1` | `LicenseRef-JDOM-2.0.6.1` | [LicenseRef-JDOM-2.0.6.1.txt](LicenseRef-JDOM-2.0.6.1.txt) | [Artifact/version](https://repo.maven.apache.org/maven2/org/jdom/jdom2/2.0.6.1/jdom2-2.0.6.1.jar) |
| `org.tukaani:xz:1.9` | `LicenseRef-public-domain-xz-1.9` | [LicenseRef-public-domain-xz-1.9.txt](LicenseRef-public-domain-xz-1.9.txt) | [Artifact/version](https://repo.maven.apache.org/maven2/org/tukaani/xz/1.9/xz-1.9.pom) |
| `xmlpull:xmlpull:1.1.3.1` | `LicenseRef-public-domain-xmlpull-1.1.3.1` | [LicenseRef-public-domain-xmlpull-1.1.3.1.txt](LicenseRef-public-domain-xmlpull-1.1.3.1.txt) | [Artifact/version](https://repo.maven.apache.org/maven2/xmlpull/xmlpull/1.1.3.1/xmlpull-1.1.3.1.pom) |

The stored root dom4j 1.1 BSD-style grant is historical investigation evidence
only. It **does not cover bundled AElfred terms** and admits no dom4j artifact.
dom4j 1.1 remains unclassified and is absent from executed-plugin inventory.
The stored oro and AOP Alliance source texts likewise do not create register
components: they are not in the gated graph. Their excluded plugin paths are
recorded separately. XZ 1.9 retains its exact public-domain dedication; it is
not relabelled using the 0BSD licence of later XZ versions.

[Jakarta API notice](jakarta-annotation-api-NOTICE.md) records ADR 0025 and
its exact-version source archive, without claiming separate-unit status.
