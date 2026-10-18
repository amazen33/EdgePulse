# Proposed ADR -- Tenant-scoped device maps and live location updates

> Deferred until after the TB CE core runs on Twinfra.

Status: proposed. Adds a map capability to M2/M3/M4; does not alter
accepted ADR 0016 tenancy or the proposed communication-direction
default of one multiplexed WebSocket per full-console browser session.
No device-map UI, spatial persistence or live feed is implemented.

## Decision

1. **Tenant and scope first.** Device ownership and hierarchy remain in
   the device/asset contexts. A map marker is a projection of an
   authorized device and its approved location, not an independent
   source of tenant ownership. Every location and spatial read model
   row has `tenant_id` and `device_id`; application RBAC/ABAC, device
   scope and PostgreSQL RLS apply to REST snapshots and every pushed
   update. A viewport or geofence query cannot widen visibility.
2. **Model location explicitly.** Distinguish a configured installation
   point from a reported position for a moving device. Use WGS84
   latitude/longitude, with longitude in x and latitude in y order for
   spatial storage; validate ranges, coordinate reference, source,
   observed time, accuracy and stale status. Altitude, heading and
   speed are optional reported values. A missing or unreliable fix is
   displayed as unknown/stale, never as `(0, 0)` or a fabricated point.
   Preserve raw location telemetry separately from the latest map
   projection and its provenance. Movement does not change tenant or
   hierarchy assignment.
3. **Spatial capability is an adapter.** Start with service-owned
   PostgreSQL persistence; use PostGIS in the location/read-model
   adapter for indexed bounding-box, radius and geofence queries when
   required. Keep domain location types and query ports independent of
   PostGIS SQL so another spatial implementation can pass the same
   contract tests. Index tenant/device identity and spatial point;
   bound viewport size, time range and result count. No service reads
   another service's database.
4. **Snapshot plus deltas.** `GET /devices/map` (illustrative API)
   returns a tenant-authorized, viewport-filtered snapshot with a
   version/watermark. Location and status changes flow through the
   approved event/read-model pipeline. The existing multiplexed
   WebSocket is the default live channel for the full console. A
   read-only SSE endpoint may serve map-only/embedded clients instead
   of that WebSocket; do not open both for the same map. REST handles
   writes and filters. Each delta carries device ID, monotonic
   version/event ID, observation time and location quality. Recheck
   authorization at subscription and delivery, enforce bounded
   backpressure, and resnapshot after a gap, expired cursor, role
   change or reconnect. The browser must not receive raw Kafka events
   or device credentials.
5. **Map rendering is replaceable.** MapLibre GL JS is an initial
   open-source browser renderer behind a map component boundary.
   Basemap tiles/styles are separately configured per deployment; an
   on-prem profile can use a self-hosted or approved provider. Do not
   assume public OpenStreetMap Foundation tile servers provide a 24/7
   production SLA. Preserve attribution and provider terms. Marker
   clustering, accessible device lists and non-map navigation remain
   available at high device counts and to users who cannot use a map.

## Required proofs

- Cross-tenant, unassigned-device and revoked-grant tests for map
  snapshots, spatial searches, SSE and WebSocket delivery; RLS remains
  effective under pooled connections.
- Coordinate range/order, source/accuracy, duplicate/out-of-order,
  stale fix, static-versus-mobile and hierarchy-change tests.
- Snapshot-to-delta, reconnect/cursor-gap and resnapshot tests, plus
  viewport/cluster performance and backpressure tests at approved
  tenant scale.
- Equivalent tenant-scoped bounding-box/radius/geofence results for
  every supported spatial adapter; map rendering and tile-provider
  replacement tests before claiming those alternatives supported.

## Open inputs

Which device classes are fixed or mobile; their location source and
update frequency; precision/privacy and retention rules; whether
geofencing is in scope; expected markers per tenant/viewport; offline
tile requirements and basemap provider for each deployment profile.

## Mechanism references

- [PostGIS spatial indexing](https://postgis.net/documentation/faq/spatial-indexes/) and [radius queries](https://postgis.net/docs/ST_DWithin.html).
- [MapLibre GL JS](https://maplibre.org/projects/gl-js/).
- [Server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) are a one-way browser feed.
- [OpenStreetMap Foundation tile policy](https://operations.osmfoundation.org/policies/tiles/) limits use of its public tile service.
