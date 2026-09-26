# Phase 1: Fleet Cloud release-one product scope

Status: **proposed release-one product scope.**
Origin: scope agreed with Birand Kilinc (Fleet Cloud product proposal).
Recorded by: Forge (issue #15), for review by PR.

This document proposes the selected **release-one subset** of the long-term
Fleet Cloud vision. The long-term vision — the full set of capabilities the
product is intended to grow into over its lifetime — is recorded in
[`docs/plans/GENERAL_PLAN.md`](GENERAL_PLAN.md). That general plan is an
orientation document, not a release commitment; this file proposes which part of
it constitutes release one.

This is a **scope proposal and planning document only**. It contains no dates,
estimates, schedules or implementation commitments, and it does not assert that
any unbuilt capability already exists. Nothing here authorizes an
implementation, dependency or infrastructure change.

## Current delivered baseline

What exists today is a deployment foundation, not the release-one product:

- Upstream **Traccar 6.15.3** (Apache-2.0) tracking core with a dedicated
  **MySQL 8.0.43** database, served over HTTPS at
  `https://fleet.nazimlaw.com`.
- An isolated upstream **OpenCloud 7.2.4** file-sharing surface at
  `https://files.nazimlaw.com` for two named users (Ulaş, Birand).

See `AGENTS.md`, `README.md`,
[`docs/adr/0002-traccar-deployment-foundation.md`](../adr/0002-traccar-deployment-foundation.md)
and
[`docs/adr/0003-opencloud-file-sharing.md`](../adr/0003-opencloud-file-sharing.md)
for the current facts and the decisions behind them.

The Fleet Cloud-specific capabilities proposed below are **not** part of the
delivered baseline. Traccar today provides device tracking, its own web map and
reports and a REST API; the OpenCloud surface provides isolated file sharing.
The release-one scope below is the work Fleet Cloud proposes to add on top of
that foundation. Upstream Traccar and OpenCloud features are named only where
they are useful context; they are not claimed as Fleet Cloud deliverables.

## Release-one outcome

Release one turns tracking and telematics data into **accountable operational
action**, not merely a map that shows where vehicles are. The product should let
an organization receive live data, detect meaningful trips and events, notify
the responsible people, create assignable tasks, maintenance items and incident
cases, investigate and resolve them, preserve an audit history, and measure the
results.

## Release-one scope

Release one covers the following capability areas. These are the proposed
release-one subset of the general plan's areas; the wording preserves the agreed
intended meaning.

1. **Organization and access foundation.** Organizations, fleets/groups, users,
   roles and permissions, sites, authentication, tenant isolation and audit
   history.
2. **Vehicles and assets.** Vehicles, trailers/equipment, profiles and groups,
   device assignment and operational status.
3. **Core telematics.** GPS, speed, direction, ignition, mileage, engine hours,
   connectivity, and device-supported sensors, diagnostics and fuel data.
4. **Live tracking.** Map, search and filtering, status/location details, and
   driver-to-vehicle association.
5. **Trips and routes.** Trip detection and history, replay, stops,
   distance/duration, and idle/driving time.
6. **Geofences and events.** Sites and restricted areas, entry/exit/dwell,
   speeding, idling, harsh driving and unauthorized movement.
7. **Alerts and notifications.** Configurable rules and thresholds, in-app and
   email notifications, history and basic escalation. SMS/messaging only through
   supported integrations.
8. **Driver management and basic safety** based on telematics, excluding
   camera-based systems.
9. **Action Center.** Turn alerts/events into assignable, prioritized,
   due-dated tasks with status, ownership, resolution notes and audit history.
10. **Maintenance and cost management.** Schedules and reminders, issues and
    work orders, service history, mileage/time triggers, downtime and basic cost
    recording.
11. **Inspections and documents.** Basic forms and records, and
    defect-to-maintenance linkage, using the existing isolated file-sharing
    boundary where appropriate.
12. **Incident and evidence cases.** Timeline, vehicle/driver/trip/location
    association, notes, status, and manually uploaded or externally linked
    photos/short videos.
13. **Customer delivery/status portal.** Narrowly shared ETA/live delivery
    status and proof of service, without exposing the wider fleet.
14. **Essential reports and KPIs.** Fleet, vehicle, driver, trip, safety,
    maintenance, fuel/idle and utilization summaries, with export where
    supported.
15. **Integration foundation.** Documented API/webhook boundaries for
    ERP/business, OEM and future camera integrations, without promising every
    integration in release one.

## End-to-end release-one flow

Release one is designed around this agreed operational flow:

```text
Create organization
  → add users / sites / vehicles / devices / drivers
    → receive live data
      → detect trips / events
        → notify responsible people
          → create a task, maintenance item or incident
            → investigate and resolve
              → preserve audit history
                → measure results
```

## Non-goals and deferred scope

The following are explicitly **out of scope** for release one:

- Integrated dashcam hardware, live/continuous streaming, or automatic vehicle
  video transfer.
- Forward Collision Warning, Lane Departure Warning, drowsiness/distraction,
  pedestrian detection, or other camera-AI safety.
- Advanced route optimization or commercial navigation.
- A full ELD/HOS/regulatory compliance suite.
- A native driver mobile app (responsive workflows may be used first).
- A generic no-code workflow engine.
- A custom report builder, benchmarking, and advanced predictive/cost analytics.
- A broad OEM/third-party integration marketplace.
- Natural-language fleet queries, anomaly detection, AI agents, or autonomous AI
  decisions.

## Dependencies and constraints

- Fuel, diagnostics, engine hours and sensor data depend on the installed
  device/OEM support; not every vehicle will expose every signal.
- Customer-facing access (for example the delivery/status portal) requires
  server-side authorization and tenant isolation before any external sharing.
- Camera evidence in release one is **manual upload or external link only** —
  there is no integrated camera system or camera-AI.
- The existing isolated OpenCloud file-sharing boundary is used where
  appropriate for documents and evidence, without widening its public exposure.

## Governance

Scope decisions — including any change to this release-one subset — must be
recorded in the appropriate planning and decision documents (for example, update
`AGENTS.md` and, where architectural, add or amend an ADR under `docs/adr/`).
This document does not by itself authorize any capability, implementation,
dependency or infrastructure change.
