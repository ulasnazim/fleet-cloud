# General Product Plan: Fleet Cloud long-term vision

Status: **long-term general product vision — not release-one scope.**
Origin: Birand Kilinc's original Fleet Cloud product proposal.
Recorded by: Forge (issue #13), for owner review by PR.

## Purpose and status of this document

This document records the complete original Fleet Cloud product proposal as the
durable **general product vision**: the full set of capabilities the product is
intended to grow into over its lifetime. It is a planning and orientation
document only.

**This is a long-term vision, not a commitment that all capabilities belong in
release one.** Nothing here is a release commitment, a schedule, an estimate or
a claim that any unbuilt capability already exists. The proposal describes
intended product direction. Delivery is decided separately, capability by
capability, against the reduced release-one scope.

### Relationship to release-one scope

The current, committed product scope is deliberately smaller than the vision in
this document. Release one is the **deployment foundation** only: upstream
**Traccar 6.15.3** (Apache-2.0) with a dedicated **MySQL 8.0.43** database,
served over HTTPS at `https://fleet.nazimlaw.com`, plus the isolated
**OpenCloud 7.2.4** file-sharing surface at `https://files.nazimlaw.com` for the
two named users. See `AGENTS.md` and `README.md` for the release-one facts, and
`docs/adr/0002-traccar-deployment-foundation.md` and
`docs/adr/0003-opencloud-file-sharing.md` for the decisions behind them.

Everything beyond that foundation — including every product area listed below
— is **future direction to be scoped, prioritised and approved separately**. The
listing order below follows the proposal; it is not a priority order or a
sequence of delivery. A capability appearing here does not mean it is planned
for release one, funded, staffed or scheduled.

## Proposed operational flow

The proposal describes the product operating as an end-to-end pipeline:

```text
Data collection
  → Vehicles / drivers / assets
    → Live tracking
      → Trips / routes / utilization
        → Event engine
          → Rules / alerts
            → Workflows
              → Reporting / analytics
                → Intelligence
                  → AI / automation
```

Data is collected from vehicles and devices, associated with the fleet's
vehicles, drivers and assets, and surfaced as live tracking. Tracking feeds
trips, routes and utilization; those feed an event engine whose rules and alerts
drive workflows, reporting and analytics, and ultimately intelligence and
AI/automation.

## Organization hierarchy

The proposal organizes the product around a single top-level organization that
owns its operating entities and access controls:

- **Organization**
  - Vehicles
  - Drivers
  - Assets
  - Sites
  - Users
  - Permissions

## Proposal areas

The 26 areas below reproduce the proposal's intended capabilities. Wording
preserves the proposal's intended meaning; no capability is added or removed.

### 1. Organization / Account Management
Organizations, fleets, groups, users, roles, permissions, locations/sites.

### 2. Vehicle & Asset Management
Vehicles, trailers, equipment, assets, vehicle profiles, asset groups, device
assignment, vehicle status.

### 3. Telematics / Data Collection
GPS location, speed, direction, ignition, engine hours, mileage, fuel data,
vehicle diagnostics, fault codes, device connectivity, sensor data, OEM data
integrations.

### 4. Live Fleet Tracking
Live map, vehicle locations/status, driver-to-vehicle association, location
details, map filtering, vehicle search, location history.

### 5. Trips & Routes
Trip detection/history, route history/replay/analysis, distance, duration,
stops, stop duration, idle time, driving time.

### 6. Geofencing
Geofences, sites, restricted areas, entry/exit events, dwell time, geofence
rules.

### 7. Event Engine
Speeding, idling, unauthorized movement, geofence, diagnostic, maintenance,
driver and vehicle events, custom rules.

### 8. Alerts & Notifications
Rules, thresholds, event-triggered/user notifications, email, SMS/messaging
integrations, escalation, history.

### 9. Driver Management
Profiles, vehicle assignment, activity/history, behavior/performance/status and
records.

### 10. Driver Safety
Speeding, harsh braking/acceleration/cornering, safety events/scores/trends and
coaching.

### 11. Compliance
Driver logs, hours of service, ELD, violations/events, inspection records and
regulatory reporting.

### 12. Dispatch
Jobs, stops, driver/vehicle assignments, status, progress and delivery workflow.

### 13. Routing & Navigation
Planning/optimization, stop sequencing, traffic, commercial routing, navigation
and constraints.

### 14. Maintenance
Preventive schedules/intervals, history/records/reminders, issues and work
orders.

### 15. Vehicle Diagnostics
Engine diagnostics/data, fault codes, health, alerts and health history.

### 16. Inspections
Vehicle/driver inspections, digital forms, defect reporting/history and
inspection-to-maintenance flow.

### 17. Fuel & Energy
Consumption, efficiency, transactions, cost, idling impact, EV
energy/charging/utilization.

### 18. Workforce / Driver Operations
Mobile application, tasks, forms, messaging, workflows, documentation and
training.

### 19. Documents
Digital forms and vehicle/driver/delivery/inspection documents, storage and
workflows.

### 20. Incident Management
Incidents, timelines/investigation, related vehicle/driver/location data and
history.

### 21. Workflow Engine
Trigger, condition, action, notification, task creation, form submission,
escalation and automation.

### 22. Reporting
Fleet, vehicle, driver, trip, safety, maintenance, fuel, utilization,
compliance and custom reports.

### 23. Analytics
Fleet KPIs, utilization, driver performance, safety/fuel/idle/maintenance/cost/
historical trends and benchmarking.

### 24. Integrations
OEM/telematics integrations, API, webhooks, third parties, ERP/business systems
and data integrations.

### 25. AI / Intelligence
Natural-language queries, insights, anomaly/trend detection, automated analysis,
summaries, workflows and agents.

### 26. Admin / Platform
Authentication, authorization, roles, permissions, audit logs, configuration,
API keys, integrations, data access and multi-tenant architecture.

## Governance

Changes to the release-one scope are decisions for the owner, recorded in
`AGENTS.md` and, where architectural, in an ADR under `docs/adr/`. This document
may be revised to keep the long-term vision accurate, but it does not by itself
authorize any capability, implementation, dependency or infrastructure change.