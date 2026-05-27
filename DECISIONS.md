# Decisions — Breathe ESG Prototype

Every ambiguity I resolved, what I chose, and why.

---

## SAP: Which export format?

**Options considered:** IDoc (XML), OData service, BAPI, flat file CSV

**Chose:** Flat file CSV

**Why:** IDoc is the native SAP format but requires an SAP middleware to
parse — not realistic for a 4-day prototype and not how most mid-market
clients export data anyway. Flat file exports (transaction MB51 for material
movements, or custom ABAP reports) are what sustainability teams actually
email around. The columns I used — WERKS, MENGE, MEINS, BLDAT, MATNR —
are standard SAP material document fields any SAP consultant would recognize.

**What I'd ask the PM:**
- Does the client have an ABAP developer who can write a standard extraction,
  or are they manually exporting from a report?
- Are they on SAP S/4HANA (OData APIs available) or legacy ECC?

**What I ignored:**
- Multi-currency conversion (all sample data is INR)
- SAP cost center hierarchy beyond a single KOSTL field
- German column headers (some SAP configs export Menge not MENGE)

---

## Utility: Which ingestion mode?

**Options considered:** PDF bill parsing, portal CSV export, Green Button API

**Chose:** Portal CSV export

**Why:** PDF parsing requires OCR and is fragile — every utility formats
bills differently. Green Button API is only available from some US utilities
and not at all from Indian utilities like MSEDCL or BSES. CSV portal exports
are universally available and what facilities teams actually use day-to-day.

**What I'd ask the PM:**
- Which utility providers does this client use?
- Does the facilities team export manually each month or is there an
  automated feed?

**What I ignored:**
- Multi-tariff bills (some meters have peak/off-peak splits)
- Reactive power / power factor charges (not relevant to carbon)
- Billing periods that span two months (handled period_start/end but
  not pro-rating)

---

## Travel: Which platform?

**Options considered:** Concur API, Navan API, manual CSV export

**Chose:** CSV export modeled on Navan/Concur format

**Why:** Both Concur and Navan expose APIs but require OAuth setup and
enterprise credentials — not possible to prototype against without a real
client account. Their CSV export formats are well-documented and realistic.
The key insight is that travel platforms export one row per segment
(flight, hotel, taxi separately), not one row per trip.

**How I handle missing distances:**
Flights only give airport codes, not distances. I implemented a Haversine
distance calculator using a lookup table of airport coordinates. For unknown
airports the record is still created but with distance = 0 and can be
flagged for manual review.

**What I'd ask the PM:**
- Does the client use Concur, Navan, or something else?
- Do they book through a TMC (Travel Management Company) that has its own
  export format?

**What I ignored:**
- Connecting flights (treated as direct)
- Train travel (no emission factor implemented)
- Car rental (no emission factor implemented)

---

## Review workflow: Why one-directional status?

PENDING → APPROVED → LOCKED is irreversible by design. Once locked, no one
can change the record — not even an admin. This mirrors how real audit
processes work: once data is submitted to an auditor, it cannot be quietly
edited. Any correction requires a new record and an audit log entry.

---

## Multi-tenancy: Row-level vs schema-level?

**Chose:** Row-level (tenant foreign key on every table)

**Why:** Schema-level (separate PostgreSQL schema per tenant) is more
isolated but far more complex to manage with Django ORM. For a prototype
with one client, row-level is correct. A real production system with
hundreds of tenants might revisit this.