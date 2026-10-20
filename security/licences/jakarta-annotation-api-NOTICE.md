# Jakarta Annotations API 2.1.1 — ADR 0025

`jakarta.annotation:jakarta.annotation-api:2.1.1` is an unmodified linked API
JAR. EdgePulse elects **EPL-2.0** from its dual licence. Exact-version sources:

- [Published POM](https://repo.maven.apache.org/maven2/jakarta/annotation/jakarta.annotation-api/2.1.1/jakarta.annotation-api-2.1.1.pom)
- [Upstream source archive](https://repo.maven.apache.org/maven2/jakarta/annotation/jakarta.annotation-api/2.1.1/jakarta.annotation-api-2.1.1-sources.jar)
- [Eclipse Public License 2.0](https://www.eclipse.org/legal/epl-2.0/)

Read on 2026-10-20. No EPL source is modified. ADR 0025 authorizes this
artifact alone; other shipped EPL artifacts need their own decision.

The linked API JAR is **not a separate unit** under the ported tier-3 rule.
The register truthfully records `separateUnit: false`. The owner-approved
legacy-pending mechanism requires a follow-up ADR and full enterprise-grade
evidence before **2027-04-20**, without extending that deadline. Recheck the
exception during the Part C Spring upgrade. This notice is not a claim that
Part B supply-chain or Part C support evidence exists.
