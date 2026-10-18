# ADR XXXX (proposed) -- AI integration: provider-neutral port, adapter boundary, read-only controls

> Deferred until after the TB CE core runs on Twinfra.

Status: proposed. Unnumbered draft per `docs/adr/README.md`; the number is
assigned at merge. Encodes direction given by the repository owner on
2026-09-26. Refines Decisions 1 and 2 of
`XXXX-proposed-ai-and-device-adapter-boundaries.md` without replacing
that draft. Works within ADR 0011 Decision 1 (Python only for the RAG
subsystem and standalone adapters), ADR 0019 (Flink synthesis, mandatory
redaction, pgvector in production, never on the edge) and ADR 0016
(tenancy and identity).

**No AI code exists.** No provider, model, adapter, RAG agent, Flink job,
redaction stage or vector store is implemented. Every provider and model
in `docs/inventory/ai-integrations.yaml` is `unimplemented`, and stays so
until its contract tests and evaluations pass.

## Context

- The owner requires deployments to integrate with several approved AI
  environments: on-prem model runtimes and cloud providers, chosen per
  deployment profile. Spring AI is acceptable only as an optional
  implementation detail inside a Java adapter.
- The enterprise readiness review (goal 11) found no model-provider
  port, provider list, residency rule or evaluation approach.
- The platform controls physical equipment (tanks, valves) and carries
  tenant data. A model is an untrusted component: its output can be
  wrong, and its input (retrieved documents, device-reported strings,
  user text) can carry injected instructions.

## Decision

1. **A provider-neutral port, owned by the consuming service.** The service
   that offers AI features (a future assistant service, or the RAG
   subsystem for retrieval) owns two outbound ports in plain Java types:
   - `ModelPort.complete(ModelRequest) -> ModelResult`. The request carries
     the tenant, purpose, messages with explicit roles, retrieved-context
     references, limits and the read-only tools offered. The result carries
     text, citations (read-model record id and version), usage and the
     provider/model ids.
   - `EmbeddingPort.embed(EmbeddingRequest) -> EmbeddingResult`.

   Each provider is an outbound adapter in `adapter.out.ai.<provider>`.
   Spring AI, if selected, lives inside such an adapter and nowhere else.
   No Spring AI or provider SDK type appears in domain, application,
   ports or published contracts (`contracts/`). The assistant's own
   published API (OpenAPI for the BFF) uses only IOT-EE types. Per ADR
   0013 each service owns its copy of the port; there is no shared AI
   library.
2. **Python stays inside the approved scope.** Python is used only for the
   RAG subsystem (ADR 0011 Decision 1, ADR 0019) and approved standalone
   adapters. The RAG agent keeps provider SDKs in its own `adapters`
   package and exchanges data with the Java platform through versioned
   contracts. Any other Python needs a new ADR. `tools/policy/check.py`
   enforces the allowed Python areas.
3. **Multiple AI environments, selected by profile, fail closed.** Each
   integration is declared in the AI inventory (schema
   `contracts/ai/ai-integration-profile.schema.json`) with:
   - hosting, adapter kind and pinned model version;
   - capabilities, data residency, retention and egress;
   - the tenant data classes it may receive.

   A deployment profile selects approved integrations, and tenant policy
   may narrow them. A disallowed or unavailable provider disables the AI
   feature for that request and nothing else. Certified tenant read
   models never go to an internet provider whose residency or retention
   is unknown.
4. **Retrieval is tenant-authorized, from certified sources, with
   attribution.** Retrieval reads only certified read models (reporting)
   and redacted, windowed insights (ADR 0019), never raw telemetry,
   device secrets or another service's database.
   - Each retrieval is authorized by the policy decision point with the
     user's own authority, and is scoped by tenant through RLS (ADR 0016).
   - Every answer cites the read-model records it used, by id and version.
     An answer with no supporting citation is marked unsupported and is
     not presented as fact.
5. **Redaction before embedding, before prompting and on output** (ADR
   0019 Decision 3 extended). No credentials, device secrets or raw
   personal data reach a model or a vector store. Output is filtered and
   encoded before display.
6. **Prompt-injection defenses.**
   - Retrieved content and device-reported strings are passed as delimited
     data, never as instructions.
   - The system policy cannot be overridden by content.
   - Which tools are offered depends on the user's request and
     authorization, never on retrieved content.
   - Tool calls are authorized as the user, not as the model.
   - There is no outbound fetch of URLs found in content.
7. **Tools: allowlisted, read-only, audited, authorized per call.** Only
   tools in the inventory's allowlist exist for a model. Every allowed
   tool has effect `read`, and every call is audited with the user, tool,
   arguments digest, decision and correlation id. The following
   capabilities are forbidden and cannot be declared as tools at all:
   - issuing device commands or writing device properties;
   - modifying rules;
   - approving migrations;
   - rolling out firmware;
   - granting access;
   - applying configuration;
   - executing payments.

   Any future action-drafting capability ("prepare a command for a human
   to review") needs its own ADR, and a human submits the action through
   the normal authorized, audited path.
8. **Evaluations gate every provider and model version.**
   - An integration moves from `unimplemented` to `contract-tested` only
     with adapter contract tests against a fake provider.
   - It moves to `evaluated` only with an offline evaluation suite
     covering groundedness and citation accuracy, cross-tenant leakage,
     redaction leakage, injection resistance and refusal of forbidden
     actions.
   - It moves to `approved` only with a pinned model version and known
     residency, retention and egress.
   - A model version change re-runs the suite.
9. **Rate and cost controls.** AI usage has per-tenant and per-user rate
   limits and token/cost budgets. Exhaustion degrades the AI feature only.
10. **AI outages never block IoT operations.** AI runs in its own
    deployable (the AI cluster of ADR 0019). No telemetry, alarm, rule,
    command, firmware, identity or billing path calls it synchronously.
    Fault-injection tests prove that telemetry, alarms and commands
    continue while the AI path is down.

## Consequences

- `tools/policy/check.py` (unit-tested) and `services/identity`'s ArchUnit
  denylist (CI) enforce:
  - the AI inventory rules: read-only mode, constitutional forbidden
    capabilities, no mutating tool ids, status gated on evidence, and no
    certified data to providers with unknown terms;
  - the Python scope;
  - that AI and provider SDKs stay in AI adapter packages;
  - that published contracts stay provider-neutral.
- Every other decision above is **unimplemented** and has acceptance
  criteria in `docs/ai-device-traceability.md`.
- The listed providers (on-prem OpenAI-compatible runtime, Azure OpenAI,
  Amazon Bedrock, Google Vertex AI, Anthropic API) are candidates, not
  selections.

## Alternatives rejected

- **Spring AI types as the port.** Rejected: it ties domain and contracts
  to one framework's abstractions and release cadence.
- **A shared AI client library across services.** Rejected by ADR 0013.
- **Letting the model call write tools with its own service identity.**
  Rejected: it bypasses the user's authorization and the audit trail, and
  turns a prompt injection into a device action.
- **Retrieval over raw telemetry or OLTP tables.** Rejected: uncertified,
  unredacted and hard to cite.

## Open questions for the owner

- Which AI environments to support first, per deployment profile
  (on-prem runtime, which cloud providers), and the tenant data classes
  each may receive.
- Where the assistant feature lives (a new Java service calling the RAG
  subsystem, or the RAG subsystem alone behind the BFF).
- Evaluation datasets and pass thresholds; who signs off an `approved`
  integration.
- Cost budgets per tenant and who pays for them (optional monetization,
  ADR 0008).
