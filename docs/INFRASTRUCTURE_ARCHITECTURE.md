# Infrastructure, Credentials, Knowledge and Monitoring Architecture

## Purpose

This document defines the technical-operations architecture for the ADB
Business Platform. Read it with:

- `PLATFORM_MASTER_PLAN.md`;
- `PERMISSIONS_AND_ACCESS_MODEL.md`;
- `DOMAIN_MODEL_AUDIT.md`;
- `CURRENT_STATE_AND_FOUNDATION_CHECKLIST.md`;
- `CREDENTIAL_VAULT_ARCHITECTURE.md`.

The target is an IT Glue-style workspace for software development, web
delivery, DevOps, Linux/system administration and technical support.

It is **not** a generic asset table and it is not a set of disconnected CRUD
registers. The product goal is contextual technical navigation: from a resource,
an authorised operator should be able to understand what it is, who owns it,
what it depends on, what depends on it, how it is accessed, how it is monitored
and where its documentation lives.

---

## 1. Structured resource architecture

Technical records use a shared `InfrastructureResource` identity plus strongly
typed specialist records.

Conceptually:

```text
InfrastructureResource
├── Server / compute
├── Network resource
├── Database instance / logical database
├── Application / Application Environment
├── Website / endpoint
├── Domain / DNS / TLS
├── Kubernetes / container resources
├── Provider Account
├── storage / backup / service / scheduled job
└── other useful specialist families
```

`InfrastructureResource` owns cross-cutting identity/ownership/lifecycle. It
does not replace specialist relational models with EAV, arbitrary JSON or a
graph database.

Specialist models keep fields/invariants that belong to their technical domain.
The shared resource identity exists so cross-cutting systems can attach
consistently:

- Credentials;
- Knowledge Base documents;
- Monitoring checks/incidents;
- tags;
- Activity/audit context;
- generic technical relationships;
- search/topology/navigation.

---

## 2. Ownership

Every structured resource is deliberately:

```text
client-owned -> a real Client
internal     -> ADB itself, Client is null
```

Never create a fake ADB/Internal Client.

Validation must enforce:

- client-owned resources require a Client;
- Internal resources do not reference a Client;
- two resources owned by different Clients cannot have a direct generic
  relationship;
- Internal ADB resources may relate to Client resources where a genuine shared
  dependency exists.

Valid examples:

```text
Client Website -> hosted_on -> Internal ADB Server
Client Domain  -> managed_by -> Internal Cloudflare Provider Account
```

A future Client portal must not expose Internal resource details merely because
an Internal resource relates to a Client resource.

---

## 3. Capability and scope

Infrastructure follows the platform rule:

```text
Django capability + ownership scope
```

Authorised staff may access Internal resources according to Infrastructure
capability. Client-owned resources additionally require access to the owning
Client.

This applies to:

- collections;
- details/drawers;
- Client-context Infrastructure views;
- relationship selectors and mutations;
- specialist projections;
- Credentials/KB/Monitoring panels;
- search/topology.

Denied records are removed at service/queryset level. Frontend filtering is not
an access-control mechanism.

Credential metadata and secret actions add their own independent capability
boundary on top of Infrastructure visibility; seeing a Server does not grant
permission to reveal its linked password or SSH key. See
`CREDENTIAL_VAULT_ARCHITECTURE.md`.

---

## 4. `InfrastructureResource`

The shared resource record carries cross-cutting fields such as:

- Client/Internal ownership;
- name;
- resource type;
- lifecycle;
- environment;
- criticality;
- safe description;
- tags;
- creator/updater metadata;
- archive/create/update timestamps;
- future explicit portal-visibility metadata, private by default.

Normal operational views are **current-first**. Retired/Archived resources are
history and should not dominate the default register or Client context.

---

## 5. Strongly typed specialists

Prefer explicit relational fields for known semantics.

Examples:

- a logical Database belongs to/uses a Database Instance through a real
  relation;
- a self-hosted Database Instance may run on a Server;
- an Application Environment belongs to an Application;
- a Website endpoint may reference an Application Environment;
- a Kubernetes Namespace belongs to a Cluster;
- a repository/source relationship should carry an explicit role when useful.

Generic `ResourceRelationship` edges complement these known relationships. They
do not replace good specialist modelling.

Secret material is never a specialist-field concern. Specialist records link to
Vault Credentials rather than adding password/token/private-key columns.

### Implemented compute/network specialist boundary

`ServerProfile` is the compute model attached
one-to-one to a Server `InfrastructureResource`. It carries operational fields
such as hostname/FQDN, purpose/role, compute type, architecture, CPU/RAM/disk,
OS/kernel metadata, Provider Account/provider resource identifiers,
region/zone/datacentre, virtualisation, SSH port, timezone, patch/update policy
and commission/decommission dates.

Networking is represented by typed models rather than free-text Server fields:

- `Network` for VPC/LAN/VLAN/VPN/overlay/public network context;
- `Subnet` for CIDR/gateway/VLAN/AZ/purpose under a Network;
- `NetworkInterface` for Server interface/MAC/MTU/network/subnet membership;
- `IPAddress` for IPv4/IPv6 address/scope/primary/PTR metadata attached to a
  structured resource and optionally an interface.

The models validate resource type, Client/Internal boundaries, Network/Subnet
consistency, gateway/CIDR membership and IP/interface/subnet membership.
Provider/account relationships are explicit.

Specialist create/edit/archive APIs use the canonical `InfrastructureResource`
ID in their URL/API identity. Invalid specialist creation is atomic and must not
leave an orphan shared resource. Archive is a shared resource lifecycle change,
not hard deletion.

The resource workspace projects native specialist metadata. Linked active
Credentials are surfaced from the Vault through the same resource identity.

### Implemented Web/Domain/DNS/TLS specialist boundary

Web infrastructure is represented by typed specialists:

- `WebsiteProfile` represents the logical web property and explicit hosting/CDN/WAF Provider Accounts;
- `WebsiteEndpoint` represents a concrete URL and may link to its `ApplicationEnvironment`, `DomainProfile` and `TLSCertificate`;
- `DomainProfile` records deterministic registration/status/expiry information and an optional registrar Provider Account;
- `DNSZone` belongs to a Domain and may reference its DNS Provider Account;
- `DNSRecord` stores structured authoritative record data including TTL and MX/SRV/proxy/provider metadata;
- `TLSCertificate` stores non-secret certificate metadata only;
- `TLSCertificateDomain` records typed Domain coverage and primary-name context.

The model enforces one primary Website Endpoint per Website, one primary DNS Zone
per Domain and one primary Domain name per TLS Certificate. Additional endpoint,
zone and certificate-domain relationships remain available as non-primary
records.

The shared Resource workspace exposes nested Website Endpoint, DNS Record and
TLS Domain-coverage operations so these relationships are usable without
returning to flat specialist registers. Normal selectors are permission-scoped
and enforce the same Client/Internal boundaries as direct API mutations.

Private keys, certificate bundles, DNS/API tokens and registrar credentials are
not fields on these models. They remain encrypted Vault Credentials linked to
the relevant Website/Domain/Provider/TLS resource.

---

## 6. Generic resource relationships

`ResourceRelationship` supplies the cross-domain topology graph without a graph
database.

Relationship semantics include concepts such as:

- `depends_on`;
- `hosted_on`;
- `connects_to`;
- `managed_by`;
- `backed_up_to`;
- `protected_by`;
- `routes_to`;
- `uses`;
- `contains`;
- `related_to`.

Relationships are directed, may carry human context, and must enforce:

- no self-link;
- no duplicate equivalent relationship;
- target visibility;
- Client ownership boundaries.

The graph should ultimately support useful contextual/topology views such as:

```text
Website
  -> Application Environment
  -> Application
  -> Server/Provider Account
  -> Database
  -> Domain/DNS/TLS
  -> Monitoring
  -> Credentials
  -> Knowledge/runbooks
```

---

## 7. Providers and Provider Accounts

Provider identity is data, not a hard-coded choice list.

`ServiceProvider` represents organisations/services such as DigitalOcean, AWS,
Microsoft, Cloudflare, GitHub, Hetzner, registrars and other vendors.

`ProviderAccount` represents the actual account/tenant/project used by ADB or a
Client and is resource-backed so Credentials, Knowledge, Monitoring and
relationships attach consistently.

Safe account metadata may include:

- account/customer ID;
- tenant/project ID;
- portal URL;
- default region;
- support plan;
- billing/reference identifiers.

Passwords, API tokens, client secrets and private keys never belong directly on
ProviderAccount. They are stored in the Credential Vault and linked to the
Provider Account resource.

---

## 8. Resource-only infrastructure

This is a new system with no historical inventory to migrate. The obsolete flat
Server, Database, Website, Domain, SSL, Licence, Application, MobileApp, API, Bot,
EmailSystem and WebsiteTechStack models and their identity bridges are removed.
Reconciliation, promotion and fallback projections are removed with them.

`InfrastructureResource` is the sole operational identity. Typed specialist
profiles hold technical metadata. Credentials remain in the encrypted Vault.
All category pages use the scoped resource collection with a fixed resource type;
resource details, overview counts, topology and technology listings use the same
identity and Client/Internal scope. Technology listings project recorded native
CMS, framework, language, database, runtime and operating-system metadata.

Historical migrations remain intact. Migration `0010_retire_obsolete_inventory`
removes the redundant tables and obsolete capabilities. No data import or bridge
is required. The old reconciliation browser URL redirects to Resources.

---

## 9. Credential integration

Credentials are an implemented, separate security boundary attached to
resources rather than plaintext fields embedded in Infrastructure.

The authoritative Vault design is `CREDENTIAL_VAULT_ARCHITECTURE.md`.

### Resource links

A Credential may link to one or more Infrastructure resources with purpose and
primary semantics.

Examples:

```text
SSH Credential       -> Server
Database Login       -> Database + Application Environment
Cloudflare API Token -> Provider Account + managed Domains
Kubeconfig            -> Kubernetes Cluster
Certificate Keypair  -> TLS/Endpoint resource
```

Client-owned Credentials may link only to resources owned by that same Client.
Internal Credentials may link to Internal or Client resources where this
represents a real shared ADB operational credential.

### Security rules

- ordinary APIs/search return credential metadata only;
- secret values remain in the encrypted, versioned credential payload;
- `CREDENTIAL_ENCRYPTION_KEYS` supplies the ordered MultiFernet key ring;
- reveal/copy/download are explicit separately permissioned actions;
- audit records field/context only, never the secret value;
- revealed browser values are ephemeral and are not persisted to local/session
  storage, routes or normal application caches;
- Infrastructure must reference Credentials instead of duplicating plaintext
  secrets;
- missing/invalid encryption configuration fails closed.

### Implemented workspace integration

- `/admin/credentials` is Active-first with explicit history views;
- typed create/edit forms use credential-template schemas;
- Client workspaces surface active Client-owned Credentials;
- Infrastructure Resource workspaces surface linked active Credentials;
- legacy StoredCredential plaintext values can be atomically reconciled into
  the encrypted payload before legacy columns are removed later.

---

## 10. Knowledge Base integration

Structured resources and Knowledge documents are distinct but deeply linked.

The agreed KB direction is a Client/Internal filesystem-like documentation tree
with Markdown/controlled rich text, versions and secure attachments.

A document/resource relationship may express semantics such as:

- documentation;
- runbook;
- deployment procedure;
- troubleshooting;
- architecture;
- disaster recovery;
- restore procedure;
- configuration.

A mature Resource workspace should surface linked documentation. A KB document
should surface related resources.

The KB must not become an alternative plaintext password store. Sensitive
access material belongs in the Credential Vault; documentation can link to the
Credential record without embedding its secret value.

---

## 11. Monitoring architecture

Monitoring is a separate cross-cutting subsystem attached to Resources. It must
not be represented by a single `is_up` field on Server or Website.

Initial target check types:

- ICMP/ping;
- TCP port;
- HTTP/HTTPS;
- expected/forbidden text/regex;
- TLS certificate validity/expiry;
- DNS record checks;
- domain registration expiry.

Checks carry scheduling, timeout, failure/recovery thresholds and severity.
Historical results record observations; Incidents represent meaningful
failure-to-recovery periods.

Celery Beat/workers execute due checks through reusable monitoring services.

Domain and TLS inventory now receives daily public metadata discovery and
automatic stored-expiry checks. Renewals update observed inventory dates; lookup
errors preserve metadata and appear in resource details and Monitoring. The
workflow reuses scoped incidents/notifications and never performs provider
renewal transactions. See
[Domain and TLS expiry tracking](INFRASTRUCTURE_EXPIRY_TRACKING.md) for scheduling,
source authority, deployment and limitations.

The Monitoring UI should follow the platform's current-first rule:

- open incidents and unhealthy resources first;
- healthy history available but not dominant;
- global and Client-scoped health views;
- uptime/response history;
- expiring domain/TLS alerts.

If a check needs authentication, it references an encrypted Vault Credential.
Monitoring result/history records never copy the secret into their metadata.

Detailed retention/escalation/notification schema should be decided in the
Monitoring slice rather than guessed now.

---

## 12. Target specialist families

### Compute and networking

Implemented foundation:

- Servers/VMs/bare-metal/container hosts through `ServerProfile`;
- network interfaces/IP addresses;
- networks/VPCs/VLANs/subnets/VPNs;
- Provider Account links and Client/Internal boundary validation.

Later networking specialists may add firewall/load-balancer/network-device
records where they are operationally useful.

### Applications and source

Implemented foundation:

- logical Applications through `ApplicationProfile`;
- resource-backed `ApplicationEnvironment` records for deploy/runtime/release
  context;
- resource-backed `SourceRepository` records with Provider Account metadata;
- typed `ApplicationRepositoryLink` role/path relationships;
- Client/Internal boundary validation and resource-centric create/edit/archive
  APIs;
- Credentials remain Vault references rather than fields on these specialists.

Later application specialists may add richer API/background-service/bot/mobile
and technology/version relationships where operationally useful.

### Databases

Implemented foundation:

- `DatabaseInstance` for managed/self-hosted service context;
- `LogicalDatabase` as an explicit child of a Database Instance;
- Server/Provider/endpoint/port/TLS/HA/replica/backup/maintenance metadata;
- Client/Internal boundary validation and resource-centric create/edit/archive
  APIs;
- authentication material through linked Vault Credentials, never specialist
  secret fields.

### Web, domains and TLS

Implemented foundation:

- logical Websites through `WebsiteProfile`;
- resource-backed concrete `WebsiteEndpoint` records;
- Domains through `DomainProfile` with registrar/status/expiry context;
- resource-backed DNS Zones and structured DNS Records;
- non-secret TLS Certificate metadata and typed Domain coverage;
- one-primary invariants for Website endpoints, Domain DNS zones and TLS names;
- registrar/DNS/CDN/WAF/TLS Provider Account relationships;
- Application Environment/Domain/TLS links from concrete Website endpoints;
- resource-centric create/edit/archive flows plus nested endpoint/DNS/TLS
  management;
- administrative credentials, DNS/API tokens and keypairs through Vault
  references rather than specialist fields.

### Containers and Kubernetes

- Docker/Podman/container stacks/services;
- Kubernetes Clusters;
- Namespaces;
- workloads;
- Services/Ingresses;
- Helm releases;
- persistent storage links;
- kubeconfigs/service tokens/certificates through Vault Credentials.

Document the useful operational shape without manually cloning the Kubernetes
API into Django.

### Operations

- storage resources;
- backup plans;
- system services;
- scheduled jobs/cron/systemd timers;
- licences/subscriptions;
- email systems and other useful operational configuration.

---

## 13. Resource workspace UX

Mature resource workspaces should converge on a recognisable pattern:

```text
Resource
├── Overview / technical details
├── Relationships
├── Credentials
├── Monitoring
├── Knowledge / Documentation
└── Activity
```

Overview remains specialist-specific. Cross-cutting sections use the shared
resource identity.

Native Server/Network/Subnet, Database/Logical Database,
Application/Environment, Source Repository, Website/Endpoint, Domain/DNS and
TLS technical details are rendered directly in the shared Resource workspace
alongside active linked Credentials. Application workspaces surface typed Source
Repository links separately from the generic topology graph, while Website,
DNS Zone and TLS workspaces surface their useful nested technical records.

The Credentials section is backed by the Vault's scoped resource-link API and
retains independent secret-action permissions.

Normal clicks may open resources in the shared right-side Record drawer while
full-page deep links remain available.

Client workspaces should expose Client-scoped Infrastructure/Credentials/KB/
Monitoring through the same policies as the global modules.

---

## 14. Search and topology

Global and Client-context search should cover useful non-secret metadata such
as:

- resource names;
- hostnames/IPs;
- domains/URLs;
- provider identifiers;
- technology metadata;
- tags;
- linked KB metadata;
- credential metadata only.

PostgreSQL-backed search is acceptable initially. Dedicated search/graph
infrastructure should not be introduced until scale/quality justifies it.

Search never indexes decrypted Vault secrets and never bypasses normal scope.

---

## 15. Current implemented boundary

The technical foundation now provides:

- `InfrastructureResource`;
- tags;
- `ServiceProvider`;
- resource-backed `ProviderAccount`;
- `ResourceRelationship`;
- ownership/cross-Client validation;
- current-first global/Client resource collections;
- scoped resource detail/drawer workspaces;
- relationship target/options/create/delete APIs/UI;
- native `ServerProfile`, `Network`, `Subnet`, `NetworkInterface` and
  `IPAddress` specialist models;
- resource-centric create/edit/archive APIs for Server/Network/Subnet plus
  interface/IP management;
- deterministic development seed data for structured compute/network examples;
- native `DatabaseInstance`, `LogicalDatabase`, `ApplicationProfile`,
  `ApplicationEnvironment` and `SourceRepository` specialists;
- typed `ApplicationRepositoryLink` role/path relationships;
- resource-centric create/edit/archive APIs and scoped selectors for the
  data/application specialist family;
- deterministic Internal and Client-owned development seed data for databases,
  applications, environments and source repositories;
- native `WebsiteProfile`, `WebsiteEndpoint`, `DomainProfile`, `DNSZone`,
  `DNSRecord`, `TLSCertificate` and `TLSCertificateDomain` specialists;
- resource-centric create/edit/archive APIs and scoped selectors for Web,
  Domain, DNS and TLS resources;
- nested Website Endpoint, DNS Record and TLS Domain-coverage management in the
  shared Resource workspace;
- deterministic Internal and Client-owned development seed data for Website,
  Domain, DNS and TLS structures;
- the typed encrypted Credential Vault;
- Credential -> Infrastructure Resource links with ownership validation;
- Client and Resource contextual Credential registers;
- explicit reveal/copy/download audit boundaries;
- atomic legacy StoredCredential secret reconciliation;
- native storage, backup, container, Kubernetes, system-service and scheduled-job profiles;
- Domain/TLS metadata discovery and Monitoring expiry checks;
- scoped category and technology registers backed solely by resources.

It does **not** yet provide:

- firewall/load-balancer and other deeper networking specialists;
- final broad technical topology/search polish.

---

## 16. Technical-operations follow-up priorities

1. Monitoring history/incident and technical-dashboard refinement;
2. Knowledge Base folder/editor/version/attachment work;
3. KB/resource backlinks + contextual search foundations;
4. Docker/Kubernetes operational workflow refinement;
5. storage/backups/system services/scheduled jobs and remaining specialist
   workflow refinement;
6. unified topology/search/activity/audit polish;
7. Credential expiry/rotation health and bulk rotation tooling as operational
   follow-up rather than a blocker for typed Infrastructure.

Client Command Centre integration should continue incrementally as these domains
mature rather than waiting for one giant final integration PR.

Every slice must preserve Client/Internal ownership, capability/scope,
current-first UX, audit boundaries and the Credential Vault secret-handling
contract.

## Overview inventory counts

The Infrastructure overview, resource registers and technology listings use
the `view_infrastructureresource` capability and the same Client/Internal scope.
Retired and Archived
records are excluded from current views. Domain and certificate expiry counts
use native profiles. Licence resources currently have no typed renewal metadata;
the overview does not imply that licence renewal dates are being monitored.

## Creation and catalogue management

The Resources chooser exposes all 29 resource types through their existing typed
forms or the common general-inventory form. Provider Accounts have resource-backed
create/edit/archive APIs and a dedicated register. Service Providers have a
separate paginated catalogue and can be created inline in the account form.
Server workspaces expose interface/IP creation, and resource workspaces support
shared tag creation and scoped assignment. See `INFRASTRUCTURE_CREATION.md` for
the complete creation map and permission contracts.
