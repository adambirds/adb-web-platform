# Lead retention and manual deletion review

Unsuccessful enquiry history is reviewed after **36 calendar months** without
activity. The current policy always requires human approval; there is no setting
that enables automatic deletion. Returning enquiries retain their earlier notes
and correspondence while within this period.

## Review workflow

Open `/admin/retention` in the Software operations application. The daily Celery
task `crm.refresh_retention_reviews` adds eligible records to the queue. **Scan
for due records** runs the same service immediately and does not delete records.

Review the lead, previous notes, last activity and included conversation count.
**Review deletion** opens a second confirmation; **Approve and delete** performs
the deletion. **Reject deletion / keep** requires a documented reason and a new
review date in 3, 6 or 12 months (default 6). The record returns for review after
that date if still eligible. Pending, kept, cancelled and deleted views are
paginated. The queue refreshes through the shared server-sent events stream when
reviews, Leads or Tickets change. Recent activity cancels pending reviews on the next scan and blocks
approval immediately.

## Eligibility and scope

Only explicitly Lost, unconverted, Brand-owned Leads are candidates. Active
leads, converted records, matching Client/Contact email addresses, open or
unrelated conversations, queued outgoing mail, Client/vendor-linked tickets,
and conversations linked to time entries or running timers are protected.

Activity includes Lead creation/modification, same-Brand same-email Lead
modification, exact-address inbound/outbound correspondence, Ticket changes and
Ticket notes. Matching is case insensitive. Administrative edits conservatively
restart the period too. Closed/resolved/spam conversations must be contact-form
enquiries or classified Sales. Shared conversations are retained until the last
associated same-Brand/email Lead is approved. The service reassesses eligibility
inside the deletion transaction rather than trusting an old browser preview.

Approval removes the Lead and eligible platform conversations, including their
messages, notes and attachments. Failed storage deletions retain object keys in
the review record and are retried by the daily job. A non-personal decision
record and audit event remain; deletion history does not retain the original
Lead name, email or notes. Microsoft 365 mailbox copies and backups are outside
this operation and require their own retention arrangements. Active/client
records and unrelated operational domains have no new deletion policy here.

## Permissions and deployment

Viewing requires active staff with `crm.view_lead` and
`crm.view_leadretentionreview`. Scanning/keeping requires `crm.view_lead` and
`crm.change_leadretentionreview`. Approval additionally requires
`crm.delete_lead`; included conversations require `ticketing.view_ticket`,
`ticketing.delete_ticket` and access to every affected Ticket Queue. Django
remains authoritative; hiding/disabling buttons is not the access check.

Apply migration `crm.0006_lead_retention_reviews`, run Celery workers and the
existing single Beat scheduler, and grant the appropriate capabilities through
Users & Access. No additional environment variables or Redis databases are
required. Reviews use the existing database, audit system and attachment storage.

Implementation: `backend/apps/crm/retention.py`,
`backend/apps/crm/ninja/retention_views.py`, `backend/apps/crm/tasks.py`, and
`sites/adb-software-solutions/src/app/(admin)/admin/retention/`.
