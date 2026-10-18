# Proposed ADR — Service-owned APIs and replaceable payment providers

Status: proposed. This records the owner's direction; implementation is
milestone-gated. Number at merge per `docs/adr/README.md`.

## Context

The platform uses independently deployable bounded contexts. ADR 0013
requires service autonomy and ADR 0017 defines per-service hexagonal
ports and adapters, but the repository does not state one consistent
contract for how a service exposes capabilities to callers and consumes
capabilities from other services. ADR 0018 already puts Stripe behind a
`PaymentGateway` outbound port; it does not yet define the owning service
or its full API boundary.

## Proposed decisions

1. **Every service owns both sides of its integration boundary.** A
   service publishes versioned provider contracts for authorized
   consumers, and defines consumer-side `port.out` interfaces for
   dependencies it calls. “Consumer API” means the stable client
   contract/port used by that service; it is not a second public server
   endpoint. Each contract has one owning service and is published in
   `contracts/`; no consumer accesses another service's database.
2. **Use the transport appropriate to the boundary.** REST/HTTPS is the
   default for frontend, BFF and external-client APIs. gRPC is the
   default synchronous service-to-service transport. Kafka events are
   for asynchronous facts and workflows. A service exposes only the
   transports that have real consumers; REST and gRPC adapters call the
   same inbound application port (ADR 0017). No transport-specific
   business logic is allowed.
3. **Contracts are governed.** REST contracts use OpenAPI and
   service-to-service gRPC contracts use Protobuf. Contracts specify
   authentication/authorization, tenant scope, errors, timeouts,
   compatibility/versioning, correlation, and idempotency for commands.
   Consumer adapters own bounded retries, circuit breaking and
   translation into local domain types. Cross-service calls propagate
   trace/correlation context and never trust tenant identifiers supplied
   without authorization.
4. **Payment is a replaceable bounded context.** When payment
   processing is implemented, a payments service owns provider-neutral
   payment operations and publishes its authorized service API. Its
   application/domain code depends on a provider-neutral outbound port
   such as `PaymentProvider`; each vendor is an isolated outbound
   adapter. Stripe may be the first adapter, but no Stripe SDK types,
   identifiers or semantics leak into shared contracts or core code.
   Adding or replacing a provider must not require changes to consumers'
   domain logic.
5. **Billing consumes finalized usage asynchronously.** Metering and
   monetization consume finalized, deduplicated usage events as already
   required by ADR 0018. Telemetry, alarms and device commands do not
   call payment providers and remain available when billing or a
   provider is unavailable. Provider webhooks enter through a dedicated
   adapter, with signature verification, replay protection and
   idempotency. Prefer provider-hosted checkout/tokenization; IOT-EE
   stores no raw card credentials. PCI scope and each provider's
   commercial/currency/tax coverage remain deployment/business review
   inputs.
6. **No shared runtime client library across services.** Each service
   owns its ports and adapters (ADR 0013). Generated contract clients
   are built from versioned contracts; shared domain logic is not
   introduced to simplify integrations.
7. **Replaceability is mandatory for selected technologies and tools.**
   Product/domain/application code depends on owned contracts and ports,
   not a vendor SDK or runtime implementation. A replacement is
   supported only after its adapter passes the same contract and
   operational conformance suite; “pluggable” does not imply that every
   alternative is a drop-in or has identical capabilities. This rule
   includes ThingsBoard CE: retain its version-specific customization
   inside an adapter/extension boundary, support tested CE upgrades by
   reapplying the declared customization set, and permit replacement by
   another implementation that conforms to the platform's owned device,
   rule, and integration contracts. Replacing TB CE may require an
   explicit migration and parity project; no one-click or semantic
   equivalence claim is made. This decision supersedes only ADR 0011
   Decision 2's statement that TB CE is “not replaceable”; the no-fork,
   thin-customization and tested-upgrade requirements remain.

## Consequences and acceptance criteria

- A service API inventory identifies each contract, owning service,
  authorized consumers, transport and version policy before M3 service
  decomposition is considered complete.
- Contract compatibility checks run in CI. A consumer contract test
  demonstrates a provider-compatible change; negative tests cover
  unauthorized and cross-tenant calls.
- Payment provider conformance tests run against a fake provider and
  each enabled provider adapter. Duplicate webhook/event delivery is
  harmless; provider failure cannot block telemetry, alarms or commands.
- The `com.stripe..` ban remains enforced outside the payment adapter;
  add corresponding bans for any future provider SDK in its own
  adapter. No real card data is present in tests, logs or persistence.
- Each selected tool/provider has a named owning port/contract, adapter
  conformance suite, supported-version policy, and documented replacement
  path before it is approved as a runtime choice. TB CE upgrade and
  alternative-implementation tests exercise required rule/device
  behavior, not merely interface shape.

## Open inputs

Provider order beyond Stripe, hosted checkout availability by provider,
PCI assessment and formal scope, supported currencies/tax/invoicing
responsibilities, and the exact consumer API inventory are to be
resolved before M7 provider implementation. These are not required to
keep the architecture replaceable.

## Related decisions

ADR 0013 (microservice autonomy), ADR 0017 (ports/adapters), ADR 0018
(usage events and payment boundary), ADR 0008 (M7 monetization), and
ADR 0011 Decision 2 (superseded in part by this proposal).
