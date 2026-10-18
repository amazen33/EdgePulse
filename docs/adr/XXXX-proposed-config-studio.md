# Proposed ADR — Backend-first Config Studio

> Deferred until after the TB CE core runs on Twinfra.

Status: proposed; product scope and implementation require roadmap
approval. Number at merge per `docs/adr/README.md`.

## Context

The repository has versioned deployment profiles, service `cfg.yaml`
schemas, Migration Studio mappings, and a Deployment Studio plan-only
lifecycle. It has no Config Studio bounded context. Treating these as
one generic editor would blur operational risk and ownership.

## Proposed decisions

1. Build a provider-neutral configuration domain and API before a GUI.
   Every change is typed and schema-validated and follows
   `draft -> validate -> preview -> approve -> apply -> rollback`, with
   tenant/environment scope, optimistic version checks and an immutable
   audit record. No raw secret values are configuration; use vault
   references.
2. Scope Config Studio to platform/service settings and tenant-level
   product configuration, each governed by explicit schema and
   authorization. Device desired properties and commands remain in the
   device-management bounded context; deployment topology and IaC
   profiles remain in Deployment Studio; source mapping, shadow parity
   and legacy cutover remain in Migration Studio.
3. Config Studio calls owning service APIs and never writes their
   databases or device state directly. Services validate/apply their
   own configuration. A central registry may track schema, versions,
   approvals and status, but does not become a universal runtime
   configuration store.
4. Support rollback only when the owning service declares the operation
   reversible and the prior version remains valid. Irreversible
   operations require a compensating action and an explicit preview;
   rollback never promises reversal of an already-delivered device
   command.
5. Introduce the API and lifecycle in a backend milestone after identity,
   tenant authorization and audit APIs are in place. Ship the studio UI
   only after API contracts and lifecycle are exercised independently.

## Acceptance criteria

Invalid or stale configurations cannot be applied; unauthorized
cross-tenant changes are rejected; every approval and application is
auditable; preview shows impact before approval; rollback restores a
previous supported version or reports why it cannot; secrets do not
appear in API responses, logs or events. API tests run without the UI.

## Related decisions

ADR 0002 (Migration Studio), ADR 0009 (Deployment Studio), ADR 0016
(identity/tenancy), ADR 0017 (service ports and adapters), ADR 0013
(service autonomy).
