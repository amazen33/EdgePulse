# ADR XXXX (proposed) -- Roles and privileged environment access: four roles; only system admins grant VM environment-admin channels; tenancy record

> Deferred until after the TB CE core runs on Twinfra.

Status: proposed. Unnumbered draft per `docs/adr/README.md`; the number
is assigned at merge. Encodes direction given by the repository owner on
2026-09-25.

Refines ADR 0016 Decision 6 (2-tier RBAC) and ADR 0011 Decisions 4 and 5
(bastion-VM channels). Records, for the Java platform, that ADR 0016
Decision 1 supersedes ADR 0003 Decision 1. Neither ADR is edited.

## Context

- ADR 0016 Decision 6 defines two tiers: Tier 1 (Product) **Product
  Admin** (`PRODUCT_ADMIN`) and **Product Operator**; Tier 2 (Tenant)
  **Tenant Admin** and **Tenant Operator**. The owner and
  `docs/requirements-addendum.md` call the Tier 1 roles "system admin"
  and "system operator".
- ADR 0011 Decisions 4 and 5: the sys-admin (`PRODUCT_ADMIN`) opens SSH
  channels through a bastion VM; lower-level access is reached only
  through that channel. Neither ADR says who may *grant* such a channel
  to someone else.
- The addendum: tenant admins grant operator roles within their tenant,
  cannot grant beyond their authority, no self-escalation or
  cross-tenant delegation; system-admin access is separately privileged
  and audited.
- Tenancy: ADR 0003 (accepted, M2 Python spec) chose **hybrid**
  isolation (schema-per-tenant for enterprise tenants, shared schema +
  RLS otherwise). ADR 0016 (accepted, 2026-09-24) chose **pooled
  `tenant_id` + PostgreSQL RLS** and rejected schema-per-tenant, but
  describes schema-per-tenant as wording "no merged ADR had adopted",
  which overlooks ADR 0003. `contracts/cfg/cfg.schema.json` still
  defaulted to `schema-per-tenant`.

## Decision

1. **Four roles, two tiers, kept distinct.**

   | Role (owner's name) | ADR 0016 name | Scope |
   | --- | --- | --- |
   | System admin | Product Admin (`PRODUCT_ADMIN`) | Platform-wide |
   | System operator | Product Operator | Platform-wide, operational; no role or access administration unless a system admin grants a specific right |
   | Tenant admin | Tenant Admin | One tenant |
   | Tenant operator | Tenant Operator | One tenant, within what its tenant admin granted |

   The ADR 0016 identifiers stay the code names. "System" and "Product"
   name the same tier. A tenant operator is not a ThingsBoard customer
   user (addendum).

2. **VM environment-admin channels: system admins only grant and
   revoke.** Access to a VM environment-admin channel (the bastion-VM
   SSH channel of ADR 0011 Decisions 4-5, and any successor channel that
   gives administrative access to a deployment environment's VMs) may be
   granted or revoked **only by a system admin**. This holds for grants to
   system operators and to tenant operators alike.
   - A tenant admin cannot grant, extend or revoke such access, including
     for its own tenant's operators.
   - A system operator cannot grant it to anyone, including itself.
   - No role can grant it to itself.
   - Every grant and revocation is audited as a privileged action
     (addendum: system-admin access is separately privileged and
     audited).
   - A tenant-scoped grant does not widen that operator's tenant scope
     anywhere else in the platform.

3. **Tenancy for the Java platform is ADR 0016's pooled `tenant_id` +
   RLS**, and it supersedes ADR 0003 Decision 1 (hybrid isolation) for
   the Java platform. ADR 0003 remains the record of the frozen Python
   spec. `contracts/cfg/cfg.schema.json`'s `tenant_mode` accepts only
   `pooled-rls`; any other mode needs a new ADR.

## Consequences

- The channel-grant rule is a design requirement for the identity
  service and for Deployment Studio (M8). No channel, bastion, grant
  API or audit trail exists yet: all **planned**, none verified.
- Negative tests are required when the grant path is implemented:
  tenant admin grant rejected, system operator grant rejected,
  self-grant rejected, revoked grant ends access, tenant-scoped grant
  does not widen tenant scope.
- ADR 0016's statement that no merged ADR had adopted schema-per-tenant
  is inaccurate (ADR 0003 had, as hybrid). Its decision is unaffected;
  this ADR is the correcting record.

## Open questions

- Whether a grant is time-bounded by default, and whether revocation
  must terminate an open session immediately (the addendum requires this
  for device access; it does not say so for VM channels).
- Whether system operators get their own console/login entry point. The
  addendum names system-admin, tenant-admin and tenant-operator
  experiences only.
- The audited cross-tenant path for Tier 1 roles (ADR 0016
  Consequences; C3 design work).
