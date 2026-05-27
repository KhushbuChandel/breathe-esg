# Tradeoffs — Breathe ESG Prototype

Three things I deliberately did not build, and why.

---

## 1. Real API integrations (SAP OData, Concur OAuth, Green Button)

**What I built instead:** File upload with CSV parsing

**Why I skipped it:**
Real API integrations require client credentials, OAuth flows, firewall
rules, and vendor-specific SDKs. None of that is achievable in 4 days
without a real client. More importantly, the file upload approach is
actually more honest — most sustainability teams are not on real-time
API feeds. They export CSVs manually. Building a fake mock API would have
been less realistic, not more.

**What it would take in production:**
- SAP: ABAP RFC or OData endpoint, VPN or SAP BTP middleware
- Concur: OAuth 2.0 app registration, webhook for real-time booking events
- Green Button: Utility enrollment, ESPI API client

---

## 2. User authentication and role-based access control

**What I built instead:** Single hardcoded tenant, AllowAny permissions

**Why I skipped it:**
Auth is important but it is not what this assignment is evaluating. The
data model, ingestion logic, and review workflow are. Adding JWT auth,
refresh tokens, and role management (Analyst vs Admin vs Auditor) would
have cost a full day and added no insight into the core problem.

**What it would take in production:**
- Django SimpleJWT for token auth
- Three roles: Uploader, Analyst (can approve/flag), Auditor (read-only
  locked records only)
- Row-level permissions so analysts only see their tenant's data

---

## 3. Automated anomaly detection / flagging

**What I built instead:** Manual flag button with a reason field

**Why I skipped it:**
The assignment asks for a review dashboard where analysts can flag suspicious
rows. I implemented the flag workflow. What I did not build is automatic
detection — e.g. flagging any record where consumption is more than 2
standard deviations from the monthly average for that meter.

**What it would take in production:**
- Historical baseline per meter / plant / category
- Statistical rules (z-score, month-on-month delta threshold)
- Auto-flag on ingestion with a suggested reason
- Analyst can dismiss the auto-flag or confirm it

This would genuinely help analysts — most suspicious records are outliers
that are hard to spot in a table of hundreds of rows.