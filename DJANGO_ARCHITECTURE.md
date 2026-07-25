# Django Architecture & App Structure

## Apps Overview

This document outlines the complete Django app structure needed for the ADB Software Solutions platform.

### 1. **authentication** (EXISTING)

Already exists. Handles:

- User authentication
- Sessions
- 2FA / Passkeys
- Email verification

---

### 2. **website** (NEW)

Public-facing website content management.

**Models:**

- `Portfolio` - Portfolio projects
- `Testimonial` - Client testimonials
- `BlogPost` - Blog articles
- `BlogCategory` - Blog post categories
- `BlogTag` - Blog post tags
- `FAQ` - FAQ items
- `FAQ Category` - FAQ categories

---

### 3. **clients** (NEW)

Client and project management.

**Models:**

- `Client` - Client/company information
- `ClientContact` - Contacts for clients
- `Project` - Projects linked to clients
- `TimeEntry` - Time tracking entries
- `ProjectNote` - Internal notes on projects

---

### 4. **infrastructure** (NEW)

Asset and infrastructure management (servers, databases, domains, etc).

**Models:**

- `Server` - Physical/virtual servers
- `Database` - Database instances
- `Website` - Websites/applications
- `Domain` - Domain registrations
- `SSLCertificate` - SSL certificate tracking
- `Licence` - Software licenses
- `Application` - Logical application abstraction
- `MobileApp` - Mobile applications
- `API` - API endpoints
- `Bot` - Chat bots and automations
- `EmailSystem` - Email configurations

**Nested/Related:**

- `ServerCredential` - Server login credentials
- `DatabaseCredential` - Database login credentials
- `WebsiteTechStack` - Tech stack for websites
- `ApplicationComponent` - Components within an application

---

### 5. **crm** (NEW)

Mini CRM for lead management.

**Models:**

- `Lead` - Sales leads
- `LeadStatus` - Lead status tracking
- `LeadSource` - Where leads come from

---

### 6. **credentials** (NEW)

Secure credential management (encrypted).

**Models:**

- `StoredCredential` - Encrypted credential vault
- `CredentialType` - Types of credentials

---

### 7. **knowledge_base** (NEW)

Per-client documentation system.

**Models:**

- `KnowledgeBaseDocument` - Documentation pages
- `KnowledgeBaseSection` - Document sections
- `DocumentVersion` - Version history

---

### 8. **tasks** (NEW)

Task and work management.

**Models:**

- `Task` - Individual tasks
- `TaskList` - Collections of tasks
- `TaskProject` - Task-specific project linking
- `TaskStatus` - Task status types

---

## API Structure

The Django Ninja or DRF API will expose endpoints for:

### Public API (`/api/public/`)

- Portfolio items (read-only)
- Blog posts (read-only)
- Testimonials (read-only)
- FAQs (read-only)
- Contact form submission

### Admin API (`/api/admin/`)

- All CRUD operations for authenticated admin users
- Protected by authentication middleware

### Website API (`/api/website/`)

- Website form submissions (contact, lead capture)

---

## Database Relationships

```
Client (1) ──→ (Many) Project
Client (1) ──→ (Many) TimeEntry
Client (1) ──→ (Many) Server
Client (1) ──→ (Many) Website
Client (1) ──→ (Many) Database
Client (1) ──→ (Many) Domain
Client (1) ──→ (Many) Application
Client (1) ──→ (Many) MobileApp
Client (1) ──→ (Many) Bot
Client (1) ──→ (Many) EmailSystem
Client (1) ──→ (Many) KnowledgeBaseDocument
Client (1) ──→ (Many) Licence
Client (1) ──→ (Many) Task

Application (1) ──→ (Many) Website
Application (1) ──→ (Many) Database
Application (1) ──→ (Many) MobileApp
Application (1) ──→ (Many) API
Application (1) ──→ (Many) Bot
Application (1) ──→ (Many) Domain
Application (1) ──→ (Many) Server
Application (1) ──→ (Many) Licence

Website (1) ──→ (Many) Server (through many-to-many)
Website (1) ──→ (Many) Database
Website (1) ──→ (Many) Domain

Server (1) ──→ (Many) Database
Server (1) ──→ (Many) Website

Domain (1) ──→ (Many) Website
Domain (1) ──→ (Many) SSLCertificate

StoredCredential (1) ──→ (Many) Server (as root credentials)
StoredCredential (1) ──→ (Many) Database (as login credentials)
StoredCredential (1) ──→ (Many) Website (as admin credentials)
```

---

## Implementation Phases

### Phase 1: Core Backend Setup

1. Create all Django apps
2. Define core models (Client, Project, Application, Server, Website, Database, Domain)
3. Set up API endpoints for CRUD operations
4. Add permission system (admin-only access to sensitive data)

### Phase 2: Website Models & API

1. Create website models (Portfolio, BlogPost, FAQ, Testimonial)
2. Create public API endpoints (read-only)
3. Integrate with frontend

### Phase 3: Admin Features

1. Create infrastructure models and APIs
2. Create CRM models and APIs
3. Create credentials system
4. Create task management system

### Phase 4: Advanced Features

1. Knowledge base system
2. Lead tracking and conversion
3. Reporting and analytics

---

## Security & Encryption

- **Credentials**: All `StoredCredential` data encrypted at rest using `django-encrypted-model-fields` or similar
- **Sensitive Fields**: Email, phone numbers encrypted where applicable
- **Access Control**: Role-based permissions (admin, staff, read-only)
- **Audit Logging**: Track all changes to critical data (clients, credentials, infrastructure changes)

---

## Frontend Integration Points

### Website Frontend

- Portfolio API (public)
- Blog API (public)
- FAQ API (public)
- Testimonials API (public)
- Contact form submission

### Admin Frontend

- All admin APIs (auth-protected)
- Real-time task updates (potential WebSocket)
- Dashboard with client/project overview
- Credential management (view, create, update, delete)
- Infrastructure inventory
- Lead tracking
