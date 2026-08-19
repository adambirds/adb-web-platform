# ADB Software Solutions Website & Platform Build Plan

> **Historical document — superseded.**
>
> This root-level plan predates the current multi-brand ADB Business Platform architecture and contains decisions that are no longer true, including deferred API/auth choices and a separate admin-application assumption.
>
> Do not use this file as implementation guidance.

The canonical/current documentation is:

- `docs/PLATFORM_MASTER_PLAN.md` — product vision, application architecture and ordered roadmap;
- `docs/CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md` — current implementation state and operational gaps;
- `docs/PERMISSIONS_AND_ACCESS_MODEL.md` — permissions and access scope;
- `docs/DOMAIN_MODEL_AUDIT.md` — model/domain decisions;
- `docs/TICKETING_ARCHITECTURE.md` — ticketing/communications architecture;
- `docs/MICROSOFT_GRAPH_TICKETING_SETUP.md` — Microsoft 365/Graph deployment runbook.

Current high-level decisions include:

- one shared Django backend using Django Ninja;
- Django session authentication and backend-authoritative permissions;
- `sites/adb-software-solutions/` combines public Software Solutions routes with authenticated operations under `/admin`;
- `sites/auth-adb-software-solutions/` remains the dedicated authentication/account application;
- ADB Software Solutions, ADB Web Designs and ADB Technology are first-class Brands on one shared business platform;
- operational resources use Client/Internal ownership rather than Brand as an ownership substitute;
- communications unify around Tickets;
- public website development is not the immediate primary phase while substantial internal operational CRUD/workflow work remains.

This file is retained only so old links/history clearly redirect developers to the current plans instead of silently presenting obsolete architecture.
