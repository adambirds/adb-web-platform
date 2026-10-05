# Creating infrastructure records

Open **Infrastructure → Resources → Add resource**. The chooser lists the types
that your permissions allow. Category pages open the appropriate form directly.
Each created record opens in its resource workspace.

## Resource types

| Family               | Types                                                                                                                               | Where to create                                                         |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Compute/network      | Server, Network, Subnet                                                                                                             | Resources → Add resource                                                |
| Data/applications    | Database instance, Logical database, Application, Application environment, Source repository                                        | Resources → Add resource                                                |
| Web/DNS/TLS          | Website, Website endpoint, Domain, DNS zone, TLS certificate                                                                        | Resources → Add resource                                                |
| Providers            | Provider account                                                                                                                    | Provider Accounts → Add resource, or the Resources chooser              |
| Technical operations | Storage, Backup plan, Container stack, Kubernetes cluster, Kubernetes namespace, Kubernetes workload, System service, Scheduled job | Resources → Add resource, or Specialist operations                      |
| General inventory    | API, Bot, Mobile app, Licence, Email system, Network device, Other                                                                  | Resources → Add resource; existing category pages also support creation |

General inventory types use the common resource's ownership, lifecycle,
environment, criticality, description and workspace relationships. These records
can later gain typed specialist profiles without creating a second identity.

## Provider accounts and service providers

A **Service Provider** is a reusable vendor entry, such as a cloud host or domain
registrar. A **Provider Account** identifies a particular account, tenant or
project with that vendor and has its own Client/Internal resource identity.

1. Open **Infrastructure → Provider Accounts → Add resource**.
2. Choose Internal or an accessible Client and name the account.
3. Select its Service Provider. If the vendor does not exist, use **Add service
   provider** in the form; the new vendor is selected automatically and your
   account fields are retained.
4. Record account/tenant/project identifiers, portal URL, region and optional
   support/billing references, then create the resource.

The vendor catalogue can also be searched and populated at
**Infrastructure → Service Providers**. Account details are editable from the
resource workspace. New accounts use active vendors; an existing account can
retain its inactive vendor when being edited.

Passwords, API tokens and private keys belong in linked Vault Credentials.

## Nested records

| Record                                                        | Creation location                                   |
| ------------------------------------------------------------- | --------------------------------------------------- |
| Network interface, IP address                                 | Server resource → Interfaces and IP addresses       |
| Application/repository link                                   | Application resource → Repository links             |
| Website endpoint                                              | Website resource → Endpoints, or Resources chooser  |
| DNS record                                                    | DNS zone resource → DNS records                     |
| TLS/domain coverage                                           | TLS certificate resource → Domain coverage          |
| Container service                                             | Container stack resource → Operational records      |
| Kubernetes service, ingress, Helm release, persistent storage | Kubernetes namespace resource → Operational records |
| Backup source                                                 | Backup plan creation/edit form                      |
| Resource relationship                                         | Resource workspace → Relationships                  |
| Infrastructure tag                                            | Resource workspace → Resource tags → Create new tag |

Operational panels appear on full resource pages. Resource tags and server
networking are available in both full pages and resource drawers.

## Permissions and API boundaries

The browser creation chooser requires `view_infrastructureresource` and
`add_infrastructureresource`, plus its specialist's `add_*` capability when it
has a typed profile. Provider Accounts also require `view_serviceprovider`;
creating a vendor requires the separate `add_serviceprovider` capability.
Provider account edit reads require `view_provideraccount`; edits additionally
require `change_infrastructureresource`, `change_provideraccount` and
`view_serviceprovider`. All Client-owned creates and edits obey Client scope.

General inventory writes use `POST /api/admin/infrastructure/resources` and
`PATCH /api/admin/infrastructure/resources/{id}`. These accept only the seven
general inventory types; they cannot bypass specialist permissions or create
an incomplete typed resource. GET and PATCH resource routes share one Ninja
router so existing resource reads remain available.

Provider account operations use `/api/admin/infrastructure/provider-accounts`;
the vendor catalogue uses `/api/admin/infrastructure/service-providers`.
`/api/admin/infrastructure/catalogue-options` supplies scoped Client choices and
active vendors visible under `view_serviceprovider`.

Tag creation uses `add_infrastructuretag`. Tag assignment/removal requires
resource view/change, `view_infrastructuretag` and access to that resource.
All new provider/general inventory/tag writes record audit events. Invalid
provider profile writes roll back the shared resource too.

## Editing records

All 29 resource types use **Edit resource** in their workspace, including resource
list drawers. This opens the matching native form and refreshes the workspace
after saving. Ownership is retained; edits do not transfer records between Clients.

Use **Service Providers → Edit** to update vendor details, URLs, notes or active
status. Deactivating a vendor preserves linked accounts and prevents selection
for new accounts. Vendor editing requires both `view_serviceprovider` and
`change_serviceprovider`; updates use `PATCH /service-providers/{id}`.

Server interfaces and IP addresses have individual Edit controls. Application
repository links and TLS Domain coverage also support editing in place. DNS,
container and Kubernetes nested records retain their existing edit forms; backup
sources are maintained in the Backup Plan form. Each nested edit requires its
own `change_*` capability and checks the scope of linked resources server-side.

Outgoing resource relationships can be edited from their source workspace,
including type, target, label and notes, using `change_resourcerelationship`.
Incoming relationships link back to that source resource. Existing targets remain
selectable even if they fall outside the initial options page.

Resource tags have **Edit** controls under `change_infrastructuretag`. Tags form
a shared catalogue: renaming a tag updates every resource using it. Assignment
and removal remain separate resource-scoped actions. Tag metadata updates use
`PATCH /tags/{id}`. Vendor, tag, repository-link, TLS-coverage and relationship
updates validate before saving and append audit events.

### Networks while adding a server interface

The Server resource's **Interfaces and IP addresses** card supports **Add network**
and **Add subnet** directly in the interface form. Choose a network before adding
its subnet. These actions use the existing native resource APIs, inherit the
Server's Client/Internal ownership, and require the corresponding resource and
specialist creation capabilities. Saving refreshes the choices and selects the
new record; cancelling or saving preserves the pending interface draft.
The dropdowns show compatible Internal or same-Client records. Selecting a
subnet also selects its parent network.

A Network describes a LAN/VPC/VLAN or other network context; a Subnet describes
an address range within it. An interface is the Server's network adapter, and IP
addresses can attach to that interface or directly to the Server.
