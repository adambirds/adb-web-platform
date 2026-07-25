# ADB Software Solutions – Website & Platform Build Plan

## 1. Overview

This document outlines the full technical and product plan for building **adbsoftwaresolutions.co.uk**. The platform will consist of:

- A **public-facing marketing website** built with **Next.js**
- A **secure internal admin platform** for managing clients, projects, time tracking, credentials, and leads
- A **Django-based backend API** that powers both the public site and the admin area

The goal is to create a professional, scalable agency website that also acts as an internal operations system, reducing reliance on third‑party tools.

---

## 2. Technology Stack

### Frontend

- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **SEO:** Built-in Next.js metadata, Open Graph, structured data
- **Forms:** Server Actions or API routes
- **Authentication (Admin):** Cookie-based session auth or JWT (depending on backend choice)

### Backend

- **Framework:** Django
- **API Layer:** Django REST Framework or GraphQL (decision deferred)
- **Database:** PostgreSQL
- **Authentication:** Django auth + custom roles/permissions
- **Admin UI:** Custom React/Next.js admin (not Django admin)

### Infrastructure (Later Phase)

- Dockerised services
- CI/CD via GitHub Actions
- Hosting on VPS or Kubernetes (future-proofed)

---

## 3. Brand Identity & Visual Design

### 3.1 Core Brand Colours

The logo establishes a clean, technical colour foundation built around **deep blue** and **bright cyan**. These should remain the primary brand anchors across the site.

**Primary Brand Colours (from logo):**

- **ADB Navy (Primary):** Deep, confident blue used for headers, navigation, and primary actions
- **ADB Cyan (Accent):** Bright cyan used for highlights, links, call-to-action emphasis, and visual interest

These colours communicate:

- Trust and reliability (navy)
- Technical clarity and modernity (cyan)

---

### 3.2 Supporting Tailwind Palette

To avoid a flat or overly corporate look, the brand colours should be layered on top of neutral and subtle Tailwind palettes.

Recommended supporting colours:

- **Slate (Primary Neutral):**
    - Backgrounds, body text, UI chrome
    - Provides a modern, technical feel without harsh contrast

- **Zinc or Gray (Secondary Neutral):**
    - Secondary text
    - Borders and dividers

- **Emerald (Success States):**
    - Success messages, confirmations

- **Amber (Warnings):**
    - Non-destructive warnings, attention states

- **Red (Errors):**
    - Errors and destructive actions only

---

### 3.3 Usage Guidelines

- **Navigation & Headers:** ADB Navy
- **Primary Buttons & Links:** ADB Cyan
- **Hover / Active States:** Darkened Navy or lightened Cyan
- **Backgrounds:** Slate-950 / Slate-900 (dark mode), Slate-50 / White (light mode)
- **Text:** Slate-100–300 (dark), Slate-700–900 (light)

Avoid overusing cyan — it should feel intentional and premium, not decorative.

---

### 3.4 Light & Dark Mode Strategy

The site should support **dark mode first**, with light mode as an optional alternative.

- Dark mode aligns with developer-focused audiences
- Cyan accents pop effectively on dark backgrounds
- Admin platform should default to dark mode

---

### 3.5 Visual Tone

Overall aesthetic goals:

- Minimal
- Technical
- Calm and confident
- No agency gimmicks or loud gradients
- Focus on typography, spacing, and clarity

---

## 4. Brand Positioning & Messaging

### 3.1 Positioning Statement

The marketing website should be explicit that **ADB Software Solutions is a solo-led consultancy**, not a large multi-person agency.

Key positioning points:

- Single senior engineer delivering **agency-level work**
- Direct access to the person doing the work (no account managers)
- Low overheads, high quality, pragmatic delivery
- Flexible engagement models: freelance, contract, white‑label

Tone should emphasise:

- Experience over headcount
- Outcomes over process theatre
- Partnership rather than vendor

---

### 3.2 Engagement Models

The site should clearly communicate the following ways of working:

- **Direct client work** – end clients engaging ADB Software Solutions directly
- **White‑label development** – acting as a behind‑the‑scenes engineer for agencies
- **Contract / fractional work** – fixed-term or ongoing contracts embedded into teams

Each model should explain:

- When it makes sense
- How engagement works
- Typical types of clients

---

## 4. Public Website Pages

### 4.1 Homepage

**Purpose:** Clear positioning and conversion

Content blocks:

- Hero section with value proposition
- Overview of services
- Key differentiators (experience, reliability, automation focus)
- Selected portfolio highlights
- Testimonials
- Call-to-action (Contact / Book a call)

---

### 4.2 About

**Purpose:** Set expectations, build trust, and clearly explain the solo‑led model.

The About page should be written in the **first person** and avoid any implication of a large team.

Key sections:

- **Who I Am**
    - Senior software engineer and consultant
    - Background in building and operating production systems
    - Experience delivering complex, agency‑level projects

- **How I Work**
    - Direct collaboration with clients
    - No account managers or hand‑offs
    - Pragmatic, outcome‑focused approach

- **Why Solo (and Why That’s a Strength)**
    - Lower overheads
    - Faster decision making
    - Deeper technical ownership

- **Who I Work With**
    - Founders and small teams
    - Established businesses
    - Agencies needing white‑label or overflow development

- **Engagement Options**
    - Freelance projects
    - Contract / fractional roles
    - White‑label agency partnerships

CTA:

- Contact or book a call

---

### 4.3 Services

Split into individual service sections (or sub-pages):

- **Software & Web Development**
    - Custom web apps
    - SaaS platforms
    - Internal tooling

- **Mobile App Development**
    - iOS / Android
    - Cross-platform solutions

- **Twitch & Discord Bots**
    - Custom moderation bots
    - Stream integrations
    - Community automation

- **Automation & DevOps**
    - CI/CD pipelines
    - Infrastructure automation
    - Cloud migrations

Each service should include:

- Description
- Typical use cases
- Example projects
- CTA

---

### 4.4 Portfolio

- List of past and current projects
- Filters by category / technology
- Individual project pages with:
    - Problem statement
    - Solution
    - Tech stack
    - Outcome/results

---

### 4.5 Blog

- SEO-focused technical articles
- Categories and tags
- Markdown-based content
- Admin-managed publishing
- Draft / published states

---

### 4.6 Testimonials

- Client quotes
- Optional star ratings
- Ability to feature testimonials on homepage

---

### 4.7 FAQs

- Common pre-sales questions
- Pricing approach
- Engagement models
- Support expectations

---

### 4.8 Contact

- Contact form
- Optional calendar booking integration
- Lead captured into backend CRM

---

## 4. Admin Platform (Internal Use)

The admin area is a **private operations system**, accessible only to authenticated staff.

### 4.1 Authentication & Roles

- Secure login
- Role-based access control:
    - Admin
    - Staff
    - Read-only (future)

---

### 4.2 Client Management

Each client record should include:

- Company details
- Contacts
- Active / inactive status
- Linked projects
- Notes & internal comments

---

### 4.3 Project & Time Tracking

- Projects linked to clients

- Time entries:
    - Date
    - Duration
    - Description
    - Billable flag

- Reporting:
    - Time per client
    - Time per project

---

### 4.4 Credential Storage

- Secure credential vault per client
- Encrypted at rest
- Access limited by role
- Examples:
    - API keys
    - Hosting logins
    - Service credentials

---

### 4.5 Client Knowledge Base

Per-client documentation system:

- Markdown editor
- Version history
- Sections (Setup, Deployments, Maintenance, Notes)
- Searchable

---

### 4.6 Lead Tracking (Mini CRM)

- Leads captured from contact forms

- Fields:
    - Source
    - Status (new, contacted, active, won, lost)
    - Notes

- Conversion of lead → client

---

### 4.7 Blog & Content Management

- Manage blog posts
- Drafts, publishing, scheduling
- SEO metadata
- Tag and category management

---

### 4.8 Task & Work Management

A lightweight but powerful task system inspired by tools like Asana, designed for **personal and small-team use**.

**Core concepts:**

- Tasks
- Task lists
- Projects

**Features:**

- Tasks can be:
    - Linked to a specific project
    - Attached to a client
    - Standalone (general personal / internal tasks)

- Task fields:
    - Title
    - Description (markdown)
    - Status (todo, in progress, blocked, done)
    - Priority
    - Due date
    - Assignee (initially just self, future-proofed)
    - Related project (optional)

- Task lists:
    - Project-specific lists
    - General lists (e.g. "Internal", "Ops", "Ideas")

- Views:
    - Project board
    - Global task list
    - Due-soon / overdue views

---

### 4.9 Infrastructure & Asset Management

The admin platform should act as a **structured infrastructure inventory**, not just free‑text notes.

---

### 4.9.1 Server Management

Servers can be attached to either a **client** or marked as **internal**.

**Server fields:**

- Client or internal
- Server hostname
- Shared or dedicated
- Server role/type (Web, Database, Management, CI, Backup, etc)
- Public IP address
- Private IP address
- Provider (dropdown, admin-managed list)
- Location / region (e.g. London, NYC, AWS us-east-1)
- Operating system
- CPU / RAM / disk (optional but useful)
- Virtualisation type (bare metal, VM, container host)
- Root / admin credentials (linked to credential system)
- Notes

---

### 4.9.2 Website Management

Websites can be linked to:

- A client
- One or more servers (shared hosting supported)

**Website fields:**

- Client or internal
- Website name
- Primary URL
- Environment type (production, staging, development)
- Associated server(s)

**Tech stack:**

- Multi-select tech stack
- Ability to tag items as:
    - Frontend
    - Backend
    - Database
    - CMS

- Predefined systems (e.g. WordPress, Django, Next.js)

**Credentials & integrations:**

- Admin username/password (credential system)
- Database used (linked database record)
- Database credentials (credential system)
- Server-level credentials (if applicable)
- GitHub repository link

**Additional metadata:**

- Aliases / redirects
- CDN usage
- Caching layer
- Notes

**WordPress-specific (conditional):**

- Installed plugins
- Theme
- Admin URL

**Staging & environments:**

- Linked staging sites
- Notes on differences from production

---

### 4.9.3 Database Management

Databases should support both **server-hosted** and **managed** solutions.

**Database fields:**

- Client or internal
- Database type (MySQL, PostgreSQL, etc)
- Hosting type (server-hosted, managed service)
- Provider (e.g. DigitalOcean, AWS RDS)
- Server (if self-hosted)
- Database name
- Version
- Credentials (credential system)
- Backup strategy notes
- Linked website(s)

---

### 4.9.4 Domains & SSL Tracking

Centralised tracking for domains and certificates to prevent expiry issues.

**Domain fields:**

- Domain name
- Client or internal
- Registrar
- Expiry date
- Auto-renew status
- Nameservers
- Linked websites / applications

**SSL fields:**

- Certificate provider (Let’s Encrypt, Cloudflare, etc)
- Certificate type
- Expiry date
- Linked domain(s)
- Renewal method

---

### 4.9.5 Licence Management

A centralised system for tracking **software, service, and plugin licences**, inspired by ITGlue-style documentation.

Licences can be linked to:

- Client or internal
- One or more websites
- Applications
- Servers (where applicable)

**Licence fields:**

- Licence name
- Licence type (subscription, perpetual)
- Vendor / provider
- Linked client or internal
- Licence key (optional, stored via credential system)
- Portal / management URL
- Renewal date
- Renewal cost (optional)
- Auto-renew enabled
- Notes

Use cases:

- WordPress plugin licences
- SaaS subscriptions
- Commercial libraries
- Infrastructure tooling

---

### 4.9.6 Application Management (Core Abstraction)

Applications represent **logical systems** that may span multiple components.

An application may include:

- One or more websites
- APIs / backend services
- Bots (Twitch, Discord)
- Mobile applications
- Databases
- Domains

This abstraction allows complex systems to be grouped under a single conceptual entity.

**Application fields:**

- Application name
- Client or internal
- Description
- Application type (web app, SaaS, bot, mobile, hybrid)
- Status (active, maintenance, archived)
- Linked websites
- Linked servers
- Linked databases
- Linked domains
- Linked repositories (GitHub)
- Linked licences
- Notes

Examples:

- A SaaS platform with multiple subdomains
- A web app + Twitch bot
- A mobile app backed by shared APIs

---

### 4.9.7 Mobile Application Management

Structured documentation for native and cross-platform mobile applications.

Mobile apps can be linked to:

- Client or internal
- Applications (core abstraction)
- APIs / backend services

**Mobile app fields:**

- App name
- Client or internal
- Platform (iOS, Android, both)
- Framework / stack (Swift, Kotlin, React Native, Flutter, etc)
- Application store links (App Store, Play Store)
- Bundle ID / package name
- Current version
- Release status (development, testing, live)
- Backend / API used (linked application or service)
- Credentials (store accounts, API keys via credential system)
- Notes

---

### 4.9.8 API & Service Management

Structured documentation for APIs and backend services, treated as **first‑class components** rather than implicit parts of websites.

APIs can be linked to:

- Client or internal
- Applications (core abstraction)
- Hosting website or service
- Servers
- Consumers (websites, mobile apps, bots, external clients)

**API fields:**

- API name
- Client or internal
- Description / purpose
- API type (REST, GraphQL, Webhooks, RPC, internal service)
- Visibility:
    - Public
    - Private (token / key based)
    - Private (session / internal only)

- Base URL
- Versioning strategy (none, URL-based, header-based)
- Authentication method (none, API key, OAuth, JWT, session)
- Rate limiting notes
- Hosting location (linked website, server, or application)
- Linked application(s)
- Linked repositories (GitHub)
- Documentation URL (Swagger, Redoc, custom)
- Credentials (tokens, secrets via credential system)
- Notes

---

### 4.9.9 Bot & Automation Management

Structured documentation for chat bots and automated agents (e.g. Twitch, Discord, Slack).

Bots can be linked to:

- Client or internal
- Applications
- Servers
- Credentials

**Bot fields:**

- Bot name
- Client or internal
- Platform (Twitch, Discord, Slack, custom)
- Bot type (chat bot, moderation, automation, integration)
- Hosting location (server, managed platform)
- Runtime / language (Python, Node.js, etc)
- Linked application(s)
- Permissions / scopes summary
- Credentials (tokens, secrets via credential system)
- Repository link
- Notes

---

### 4.9.10 Email & Messaging Systems

Documentation for client and internal email systems.

Email systems can be linked to:

- Client or internal
- Domains
- Applications

**Email system fields:**

- Provider (Exchange, Microsoft 365, Google Workspace, self-hosted)
- Client or internal
- Domains in use
- Admin portal URL
- Admin credentials (credential system)
- User accounts / mailboxes (summary only)
- Aliases / distribution lists
- SPF / DKIM / DMARC status
- Notes on configuration or quirks

---

### 4.10 Structured Documentation & Linking

To avoid information silos, all major entities should be linkable:

- Clients ↔ Projects ↔ Tasks
- Projects ↔ Applications
- Applications ↔ Websites ↔ APIs ↔ Mobile Apps ↔ Bots
- Applications ↔ Servers ↔ Databases
- Applications ↔ Licences
- Domains ↔ Websites / Applications / APIs ↔ SSL certificates
- Email systems ↔ Domains ↔ Applications

This creates a **navigable internal knowledge graph**, similar in spirit to ITGlue, but tailored to a solo consultancy.

---

### 4.11 ITGlue-Inspired Design Principles

The admin platform should intentionally mirror the **strengths of tools like ITGlue**, while remaining lightweight, opinionated, and developer-focused.

Core principles:

- Structured data over free-text wherever possible
- Strong relationships between entities (no silos)
- Credentials stored once, referenced everywhere
- Clear separation between **infrastructure**, **applications**, and **access**
- Markdown documentation for human context, decisions, and runbooks
- Designed for speed, clarity, and recoverability — not bureaucracy

The end goal is a **single source of truth** for:

- Clients
- Infrastructure (servers, domains, SSL, email)
- Applications and components (websites, APIs, bots, mobile apps)
- Access and credentials
- Operational and architectural knowledge

---

## 5. Backend Responsibilities (Django)

- API for all public and admin data
- Authentication & permissions
- Data validation
- Secure credential encryption
- Audit logging (future)

---

## 6. Security Considerations

- HTTPS everywhere
- Secure cookies
- CSRF protection
- Encrypted sensitive fields
- Rate limiting on public forms

---

## 7. Phased Build Approach

### Phase 1 – Marketing Site

- Homepage
- Services
- Portfolio
- Contact

### Phase 2 – Admin Core

- Auth
- Clients
- Projects
- Time tracking

### Phase 3 – Advanced Features

- Knowledge base
- Credential vault
- Lead CRM
- Blog CMS

---

## 8. Future Enhancements

- Client portal access
- Invoicing & billing
- Proposal generation
- Analytics dashboard
- AI-assisted documentation

---

## 9. Success Criteria

- Fast, SEO-friendly public site
- Secure and efficient internal tooling
- Reduced reliance on third-party SaaS tools
- Scalable foundation for future agency growth
