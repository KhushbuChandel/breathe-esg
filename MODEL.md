# Data Model — Breathe ESG Prototype

## Overview

The data model is built around one central question: **how do you take messy,
inconsistent data from three completely different sources and produce a single,
auditable, trustworthy emissions record?**

The answer is a clean separation between:
- What came in (raw, never touched)
- What we computed (normalized, explainable)
- What an analyst decided (review workflow)
- What happened over time (immutable audit trail)

---

## Tables

### `Tenant`
Represents a client company. Every record in the system belongs to a tenant.
This is the foundation of multi-tenancy — no data ever crosses tenant boundaries
because every query filters by tenant foreign key.

| Field | Type | Why |
|-------|------|-----|
| name | CharField | Human-readable company name |
| slug | SlugField (unique) | URL-safe identifier e.g. `acme-corp` |
| created_at | DateTimeField | Onboarding timestamp |

---

### `DataIngestion`
One upload event. If a facilities manager uploads a utility CSV on Jan 15,
that is one DataIngestion row. It tracks the file, who uploaded it, when,
and whether parsing succeeded or failed.

| Field | Type | Why |
|-------|------|-----|
| tenant | FK → Tenant | Ownership |
| source_type | CharField | SAP / UTILITY / TRAVEL |
| file | FileField | Original file stored for re-processing |
| original_filename | CharField | Audit trail — what the user actually uploaded |
| status | CharField | PROCESSING / COMPLETED / FAILED |
| error_message | TextField | Why it failed, if it did |
| row_count | IntegerField | How many rows were successfully parsed |
| error_count | IntegerField | How many rows were skipped |
| uploaded_at | DateTimeField | When the upload happened |
| uploaded_by | FK → User | Who uploaded it |

**Why store the original file?**
Because parsers can have bugs. If we discover our SAP parser miscalculated
units in February, we need to be able to re-parse from the original source
without asking the client to re-upload.

---

### `EmissionRecord`
The core of the system. One normalized row of emission data, regardless of
whether it came from SAP, a utility bill, or a travel platform.

#### Traceability fields
| Field | Type | Why |
|-------|------|-----|
| tenant | FK → Tenant | Multi-tenancy |
| ingestion | FK → DataIngestion | Which upload produced this row |
| source_row_id | CharField | Original row identifier from source system |

#### Classification (GHG Protocol)
| Field | Type | Why |
|-------|------|-----|
| scope | CharField | SCOPE_1 / SCOPE_2 / SCOPE_3 |
| category | CharField | e.g. FUEL_STATIONARY, ELECTRICITY, BUSINESS_TRAVEL_AIR |

Scope follows the GHG Protocol Corporate Standard — the global framework
all carbon auditors use. Scope 1 = direct emissions (fuel burned on-site),
Scope 2 = indirect from purchased electricity, Scope 3 = value chain
(travel, supply chain).

#### Raw values — never modified
| Field | Type | Why |
|-------|------|-----|
| raw_quantity | DecimalField | Exactly as it came in — 5000.000 |
| raw_unit | CharField | Exactly as it came in — L, KG, kWh |
| raw_data | JSONField | The entire original row as JSON |

Raw values are sacred. We never overwrite them. If an analyst edits a record,
we write a new version and log the change — we do not mutate raw_quantity.

#### Normalized values
| Field | Type | Why |
|-------|------|-----|
| normalized_quantity | DecimalField | Always in kg CO2e |
| normalized_unit | CharField | Always kg_co2e |
| emission_factor_used | DecimalField | The factor applied e.g. 2.6391 |
| emission_factor_source | CharField | e.g. DEFRA 2023 — Diesel |

Every emission record stores the exact factor used and its source. This is
non-negotiable for auditors — they need to verify the calculation themselves.

#### Review workflow
| Field | Type | Why |
|-------|------|-----|
| status | CharField | PENDING → APPROVED → LOCKED (or FLAGGED) |
| flag_reason | TextField | Why an analyst flagged it |
| reviewed_by | FK → User | Who approved it |
| reviewed_at | DateTimeField | When they approved it |
| locked_at | DateTimeField | When it was locked for audit |

Status transitions are one-directional: you cannot un-lock a locked record.
This protects audit integrity.

---

### `AuditLog`
An append-only log of every state change on every EmissionRecord. Rows are
never deleted or edited. This is what makes the system auditable.

| Field | Type | Why |
|-------|------|-----|
| record | FK → EmissionRecord | Which record changed |
| action | CharField | CREATED / EDITED / FLAGGED / APPROVED / LOCKED |
| performed_by | FK → User | Who did it |
| note | TextField | Optional human explanation |
| before_state | JSONField | Snapshot of record before change |
| after_state | JSONField | Snapshot of record after change |
| performed_at | DateTimeField | auto_now_add — immutable timestamp |

---

## Scope 1 / 2 / 3 Mapping

| Source | Scope | Category |
|--------|-------|----------|
| SAP — Diesel | Scope 1 | FUEL_STATIONARY |
| SAP — Petrol | Scope 1 | FUEL_MOBILE |
| SAP — LPG | Scope 1 | FUEL_STATIONARY |
| Utility — kWh | Scope 2 | ELECTRICITY |
| Travel — Flight | Scope 3 | BUSINESS_TRAVEL_AIR |
| Travel — Hotel | Scope 3 | BUSINESS_TRAVEL_HOTEL |
| Travel — Ground | Scope 3 | BUSINESS_TRAVEL_GROUND |

---

## Unit Normalization

All quantities are normalized to **kg CO2e** (kilograms of CO2 equivalent).
This is the standard unit used in GHG reporting.

Conversion pipeline:  raw_quantity (any unit) × emission_factor (kg CO2e per unit) = normalized_quantity (kg CO2e) 


Example: Understanding an assignment step by stepClaude finished the responseYou said: Explain me this assignment in the most simplest form and also tell step by step how to do itpdfExplain me this assignment in the most simplest form and also tell step by step how to do itMay 25Claude responded: The Assignment in Simple TermsThe Assignment in Simple Terms
You're building a data collection and review tool for a company that tracks carbon emissions.
The problem they're solving: Big companies need to report how much CO₂ they emit. That data comes from messy, real-world sources — fuel bills, electricity bills, flight records. Someone needs to collect all of it, clean it up, and let an expert check it before it's official.
Your job: Build a web app that does exactly that.

What You're Building
Think of it like a 3-step pipeline:
Raw messy data → Your app cleans it → Analyst approves it → Locked for auditors
Three data sources you handle:
SourceWhat it isWhy it's messySAPCompany's fuel & purchasing softwareWeird formats, German headers, bad datesUtility portalElectricity billsUnits vary, billing periods are irregularConcur/NavanFlight & hotel bookingsNo distances, just airport codes

Step-by-Step Plan
Step 1 — Research First (Day 1 morning)
Before writing a single line of code, understand the real data:

SAP: Google "SAP flat file export format emissions" — you'll find it exports as .csv or .txt with columns like WERKS (plant code), MENGE (quantity), MEINS (unit). Pick flat file CSV — simplest to justify.
Utility data: Google "utility bill CSV export format" — look at what Green Button Data (a US standard) looks like. Columns: meter ID, interval start, interval end, kWh.
Concur/Navan: Look at Navan or Concur's API docs or export formats. You'll see: traveler name, origin airport, destination airport, trip date, hotel name, nights stayed.

Write fake but realistic sample data based on what you find.

Step 2 — Design Your Data Model (Day 1 afternoon)
This is worth 35% of your grade — spend serious time here.
You need these core database tables:
Tenant (the client company)
└── DataSource (SAP / Utility / Travel)
    └── RawIngestion (one upload/pull event)
        └── EmissionRecord (one cleaned row of data)
            └── AuditLog (who changed what, when)
Each EmissionRecord needs:

Which scope it is (Scope 1 = fuel burned, Scope 2 = electricity, Scope 3 = travel)
Original raw value + unit
Normalized value (always in kg CO₂e)
Source file/API that produced it
Status: pending → approved → locked
Who approved it and when


Step 3 — Django Backend (Day 2)
Set up:
Django project
├── apps/
│   ├── ingestion/     ← handles file uploads, parsing
│   ├── emissions/     ← the core EmissionRecord model
│   └── review/        ← approve/reject API endpoints
Build in this order:

Models first (your data model from Step 2)
File upload endpoint (accepts CSV)
Parsers for each source type (SAP parser, Utility parser, Travel parser)
Review endpoints (GET records, PATCH to approve/flag)


Step 4 — React Frontend (Day 3)
Three screens:

Upload screen — drag & drop a file, pick source type (SAP / Utility / Travel)
Review dashboard — table showing all records, color-coded by status (pending = yellow, suspicious = red, approved = green)
Record detail — see raw vs normalized value, approve or flag it

Keep it simple. A clean table with filters beats a fancy UI you can't explain.

Step 5 — Write Your Docs (Day 3 evening)
Four markdown files the graders care about:
FileWhat to writeMODEL.mdExplain every table and why it existsDECISIONS.md"I chose flat-file SAP because...", "I ignored hotel emissions because..."TRADEOFFS.md3 things you skipped (e.g., real API integration, multi-currency, PDF parsing) and whySOURCES.mdWhat you researched for each source, what your fake data looks like, what would break in production

Step 6 — Deploy (Day 4)
Easiest path:

Backend: Railway — Django + PostgreSQL, free tier, deploys from GitHub
Frontend: Vercel — React, free, also deploys from GitHub

Steps:

Push code to GitHub
Connect Railway → deploy Django, add a Postgres database
Connect Vercel → deploy React, set API URL env variable
Test the live URLs
Email the links


What They're Really Testing

"Submit less, but submit work you understand and can defend."

They don't want a huge app. They want to see that you thought carefully about:

Why SAP data is hard
Why unit normalization matters (kWh vs MWh vs BTU)
Why an audit trail is non-negotiable in ESG reporting

Every choice you make — write down why you made it. That's 60% of your grade.

Want me to help you start with any specific step — like designing the data model, writing the parsers, or setting up the Django project?You said: yes help me to build this entire projectyes help me to build this entire projectMay 25Claude responded: Let's plan this out properly before writing any code.Let's plan this out properly before writing any code.You said: Q: What's your experience level with Django and React?Q: What's your experience level with Django and React?
A: Beginner (I'll need detailed explanations)Q: What's your local development setup?
A: WindowsQ: Do you have these installed already? (Select all that apply)
A: Python 3.10+, Node.js 18+, PostgreSQL, GitMay 25Claude responded: Perfect — you have everything needed.Perfect — you have everything needed. Let's build this together, step by step, in the right order.
Here's our full game plan before we touch any code:

🗺️ Master Plan (4 Days)
Day 1 → Project setup + Database models (the most important part)
Day 2 → Django backend (file upload + parsers + API)
Day 3 → React frontend (upload screen + review dashboard)
Day 4 → Docs + Deployment
We'll go one step at a time. I'll explain every single command and decision.

Let's Start — Day 1, Step 1: Project Structure
Open your Command Prompt or PowerShell and run these commands one by one:
1. Create the main project folder
bashmkdir breathe-esg
cd breathe-esg
2. Create and activate a Python virtual environment
bashpython -m venv venv
venv\Scripts\activate

You should see (venv) appear at the start of your terminal line. This keeps your Python packages isolated.

3. Install Django and required packages
bashpip install django djangorestframework django-cors-headers psycopg2-binary python-dotenv pillow
4. Create the Django project
bashdjango-admin startproject breathe_backend
cd breathe_backend
5. Create the Django apps
bashpython manage.py startapp tenants
python manage.py startapp ingestion
python manage.py startapp emissions
python manage.py startapp review
6. Go back to root and create the React app
bashcd ..
npx create-react-app breathe-frontend

Your folder structure should now look like this:
breathe-esg/
├── venv/
├── breathe_backend/
│   ├── breathe_backend/     ← Django settings
│   ├── tenants/             ← Client companies
│   ├── ingestion/           ← File uploads & parsers
│   ├── emissions/           ← Core EmissionRecord model
│   ├── review/              ← Approve/flag endpoints
│   └── manage.py
└── breathe-frontend/        ← React app

Tell me once you've done these steps (or paste any error you see) and we'll move to Step 2 — setting up PostgreSQL and writing the data models.

💡 The data model is 35% of your grade, so we'll spend solid time designing it right before writing a single line of code.
You said: move to Step 2move to Step 2May 25Claude responded: Step 2: PostgreSQL Setup + Data ModelsStep 2: PostgreSQL Setup + Data Models
First, set up your database
Open pgAdmin (comes with PostgreSQL) or use PowerShell:
bashpsql -U postgres
Then run:
sqlCREATE DATABASE breathe_esg;
CREATE USER breathe_user WITH PASSWORD 'breathe123';
GRANT ALL PRIVILEGES ON DATABASE breathe_esg TO breathe_user;
\q

Now let's configure Django
Navigate to your settings file and let's set everything up. In your breathe_backend/breathe_backend/ folder, create a .env file:
breathe-esg/
└── breathe_backend/
    └── breathe_backend/
        └── .env          ← create this file here
Put this inside .env:
envDEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production
DB_NAME=breathe_esg
DB_USER=breathe_user
DB_PASSWORD=breathe123
DB_HOST=localhost
DB_PORT=5432

Now replace everything in breathe_backend/breathe_backend/settings.py with this:
pythonfrom pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    # Our apps
    'tenants',
    'ingestion',
    'emissions',
    'review',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'breathe_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'breathe_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS - allow React frontend to talk to Django
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

Now the most important part — The Data Models
This is 35% of your grade. Here's the thinking behind each model before we write it:
Tenant          → Who is the client company?
DataIngestion   → One upload event (a file came in at this time, from this source)
EmissionRecord  → One cleaned, normalized row of data
AuditLog        → Every change ever made to a record

tenants/models.py
pythonfrom django.db import models

class Tenant(models.Model):
    """A client company using the platform"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)  # e.g. 'acme-corp'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

ingestion/models.py
pythonfrom django.db import models
from tenants.models import Tenant

class DataIngestion(models.Model):
    """
    Represents one upload/ingestion event.
    e.g. 'SAP CSV uploaded on 2024-01-15 by facilities team'
    """

    SOURCE_TYPES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity Data'),
        ('TRAVEL', 'Corporate Travel Data'),
    ]

    STATUS_CHOICES = [
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ingestions')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')
    error_message = models.TextField(blank=True, null=True)  # if parsing failed, why?
    row_count = models.IntegerField(default=0)       # how many rows parsed
    error_count = models.IntegerField(default=0)     # how many rows failed
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.tenant.name} - {self.source_type} - {self.uploaded_at.date()}"

emissions/models.py
This is the core model — every single row of emission data ends up here:
pythonfrom django.db import models
from tenants.models import Tenant
from ingestion.models import DataIngestion

class EmissionRecord(models.Model):
    """
    One normalized row of emission data.
    No matter whether it came from SAP, utility bill, or travel —
    it ends up here in a common shape.
    """

    # --- Scope classification (GHG Protocol standard) ---
    SCOPE_CHOICES = [
        ('SCOPE_1', 'Scope 1 - Direct (fuel combustion)'),
        ('SCOPE_2', 'Scope 2 - Indirect (purchased electricity)'),
        ('SCOPE_3', 'Scope 3 - Value chain (travel, procurement)'),
    ]

    CATEGORY_CHOICES = [
        # Scope 1
        ('FUEL_STATIONARY', 'Stationary Combustion (generators, boilers)'),
        ('FUEL_MOBILE', 'Mobile Combustion (company vehicles)'),
        # Scope 2
        ('ELECTRICITY', 'Purchased Electricity'),
        # Scope 3
        ('BUSINESS_TRAVEL_AIR', 'Business Travel - Flights'),
        ('BUSINESS_TRAVEL_HOTEL', 'Business Travel - Hotels'),
        ('BUSINESS_TRAVEL_GROUND', 'Business Travel - Ground Transport'),
        ('PROCUREMENT', 'Procurement / Purchased Goods'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('FLAGGED', 'Flagged - Needs Attention'),
        ('APPROVED', 'Approved'),
        ('LOCKED', 'Locked for Audit'),
    ]

    # --- Traceability: where did this row come from? ---
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='emission_records')
    ingestion = models.ForeignKey(DataIngestion, on_delete=models.CASCADE, related_name='records')
    source_row_id = models.CharField(max_length=255, blank=True)  # original row ID from source

    # --- Classification ---
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)

    # --- Raw values exactly as they came in (never modified) ---
    raw_quantity = models.DecimalField(max_digits=15, decimal_places=4)
    raw_unit = models.CharField(max_length=50)   # e.g. 'litres', 'kWh', 'MWh', 'gallons'
    raw_data = models.JSONField()                # the entire original row as JSON

    # --- Normalized values (always kg CO2e) ---
    normalized_quantity = models.DecimalField(max_digits=15, decimal_places=4)
    normalized_unit = models.CharField(max_length=20, default='kg_co2e')
    emission_factor_used = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    emission_factor_source = models.CharField(max_length=255, blank=True)  # e.g. 'DEFRA 2023'

    # --- Time period ---
    period_start = models.DateField()
    period_end = models.DateField()

    # --- Location ---
    facility_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # --- Description ---
    description = models.TextField(blank=True)  # human-readable summary

    # --- Review workflow ---
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    flag_reason = models.TextField(blank=True)   # why was it flagged?
    reviewed_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_records'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tenant.name} | {self.scope} | {self.normalized_quantity} kg CO2e"

review/models.py
pythonfrom django.db import models
from emissions.models import EmissionRecord

class AuditLog(models.Model):
    """
    Immutable log of every change to an EmissionRecord.
    Required for auditor trust — nothing can be deleted, only appended.
    """

    ACTION_CHOICES = [
        ('CREATED', 'Record Created'),
        ('EDITED', 'Record Edited'),
        ('FLAGGED', 'Record Flagged'),
        ('APPROVED', 'Record Approved'),
        ('LOCKED', 'Record Locked'),
    ]

    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    note = models.TextField(blank=True)           # optional human note
    before_state = models.JSONField(null=True)    # snapshot before change
    after_state = models.JSONField(null=True)     # snapshot after change
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['performed_at']

    def __str__(self):
        return f"{self.action} on Record #{self.record.id} at {self.performed_at}"

Now run the migrations
bashcd breathe_backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

For superuser, enter any username/email/password you'll remember — you'll use this to log in.

Then test it works:
bashpython manage.py runserver
Visit http://127.0.0.1:8000/admin — you should see the Django admin panel.

Tell me when this is working and we'll move to Day 2 — building the parsers and REST API endpoints for all three data sources (SAP, Utility, Travel).You said: done, tell me nextdone, tell me nextMay 25Claude responded: Day 2: Parsers + REST APIDay 2: Parsers + REST API
First let's create the sample data files that will be uploaded. This is important because your sample data needs to look realistic — they'll ask you about it.
Step 1: Create Sample Data Files
Create a folder called sample_data inside breathe_backend:
breathe_backend/
└── sample_data/
    ├── sap_export.csv
    ├── utility_export.csv
    └── travel_export.csv
sample_data/sap_export.csv (SAP flat file format — IDoc-inspired):
csvMANDT,WERKS,BUKRS,BLDAT,BUDAT,MATNR,MAKTX,MENGE,MEINS,NETWR,WAERS,LIFNR,NAME1,KOSTL
100,1000,CORP,20240101,20240103,DIES001,Diesel Kraftstoff,5000.000,L,4250.00,INR,V-1001,Sharma Fuels Pvt Ltd,COST001
100,1000,CORP,20240115,20240117,DIES001,Diesel Kraftstoff,3200.000,L,2720.00,INR,V-1001,Sharma Fuels Pvt Ltd,COST001
100,2000,CORP,20240201,20240203,PETT001,Petrol,1800.000,L,1980.00,INR,V-1002,Rajesh Petroleum,COST002
100,1000,CORP,20240210,20240212,DIES001,Diesel Kraftstoff,4100.000,L,3485.00,INR,V-1001,Sharma Fuels Pvt Ltd,COST001
100,3000,CORP,20240301,20240303,LPGG001,LPG Gas,800.000,KG,2400.00,INR,V-1003,National Gas Supply,COST003
100,2000,CORP,20240315,20240317,PETT001,Petrol,2100.000,L,2310.00,INR,V-1002,Rajesh Petroleum,COST002

Why it looks like this: SAP uses German field names (MENGE=quantity, MEINS=unit, WERKS=plant, BLDAT=document date). Dates are YYYYMMDD. Units are SAP internal codes (L=litres, KG=kilograms).

sample_data/utility_export.csv (Green Button Data format — US/India utility standard):
csvmeter_id,account_number,facility_name,billing_period_start,billing_period_end,consumption_kwh,demand_kw,tariff_code,rate_per_unit,total_amount,currency,utility_provider,state
MTR-001,ACC-2024-001,Head Office Mumbai,2024-01-01,2024-01-31,45230.500,120.5,HT-I,8.50,384459.25,INR,MSEDCL,Maharashtra
MTR-002,ACC-2024-002,Factory Pune,2024-01-01,2024-01-31,128450.000,380.0,HT-II,7.80,1001910.00,INR,MSEDCL,Maharashtra
MTR-001,ACC-2024-001,Head Office Mumbai,2024-02-01,2024-02-29,41820.000,115.0,HT-I,8.50,355470.00,INR,MSEDCL,Maharashtra
MTR-003,ACC-2024-003,Warehouse Delhi,2024-01-01,2024-01-31,22100.000,65.0,LT-II,6.50,143650.00,INR,BSES,Delhi
MTR-002,ACC-2024-002,Factory Pune,2024-02-01,2024-02-29,134200.000,390.0,HT-II,7.80,1046760.00,INR,MSEDCL,Maharashtra

Why it looks like this: Indian utilities (MSEDCL, BSES) export meter-level data with tariff codes (HT-I = High Tension industrial). Billing periods don't align with calendar months sometimes.

sample_data/travel_export.csv (Navan/Concur export format):
csvtrip_id,traveler_name,traveler_email,department,trip_purpose,segment_type,origin,destination,travel_date,return_date,cabin_class,distance_km,hotel_name,hotel_city,nights,ground_type,vendor,amount,currency
TRP-001,Ankit Verma,ankit@corp.com,Sales,Client Meeting,FLIGHT,BOM,DEL,2024-01-10,2024-01-12,ECONOMY,,,,,,18500.00,INR
TRP-001,Ankit Verma,ankit@corp.com,Sales,Client Meeting,HOTEL,,,,2024-01-10,,,,The Leela Delhi,Delhi,2,,22000.00,INR
TRP-002,Priya Sharma,priya@corp.com,Engineering,Conference,FLIGHT,DEL,LHR,2024-01-20,2024-01-25,BUSINESS,,,,,,185000.00,INR
TRP-002,Priya Sharma,priya@corp.com,Engineering,Conference,FLIGHT,LHR,DEL,2024-01-25,,BUSINESS,,,,,,185000.00,INR
TRP-003,Rahul Singh,rahul@corp.com,Operations,Site Visit,GROUND,,,2024-02-05,,,,,,,,TAXI,1200.00,INR
TRP-004,Meera Patel,meera@corp.com,Finance,Audit,FLIGHT,BOM,BLR,2024-02-15,,ECONOMY,,,,,,6500.00,INR

Why it looks like this: Travel platforms export one row per segment (flight/hotel/taxi separately). Flights only have airport codes (BOM/DEL), not distances — your parser must calculate or estimate distances.


Step 2: Build the Parsers
Create this file: breathe_backend/ingestion/parsers.py
pythonimport csv
import io
from decimal import Decimal
from datetime import datetime, date


# ── Emission factors (kg CO2e per unit) ──────────────────────────────────────
# Source: DEFRA 2023 / India GHG Platform
EMISSION_FACTORS = {
    'diesel_litre':     Decimal('2.6391'),   # kg CO2e per litre
    'petrol_litre':     Decimal('2.3153'),
    'lpg_kg':           Decimal('2.9830'),
    'electricity_kwh':  Decimal('0.7160'),   # India grid average 2023 (CEA)
    'flight_economy_km':   Decimal('0.1553'),
    'flight_business_km':  Decimal('0.4285'),
    'hotel_night':      Decimal('31.0000'),  # kg CO2e per room-night (DEFRA)
    'taxi_inr':         Decimal('0.0850'),   # rough: kg CO2e per INR spent
}

# Airport coordinates for distance calculation (lat, lon)
AIRPORT_COORDS = {
    'BOM': (19.0896, 72.8656),  # Mumbai
    'DEL': (28.5562, 77.1000),  # Delhi
    'BLR': (13.1986, 77.7066),  # Bangalore
    'MAA': (12.9941, 80.1709),  # Chennai
    'HYD': (17.2403, 78.4294),  # Hyderabad
    'LHR': (51.4700, -0.4543),  # London Heathrow
    'JFK': (40.6413, -73.7781), # New York JFK
    'DXB': (25.2532, 55.3657),  # Dubai
}

# SAP plant code → facility name lookup
PLANT_LOOKUP = {
    '1000': 'Head Office Mumbai',
    '2000': 'Factory Pune',
    '3000': 'Warehouse Delhi',
}

# SAP material → fuel type lookup
MATERIAL_LOOKUP = {
    'DIES001': ('diesel', 'L'),
    'PETT001': ('petrol', 'L'),
    'LPGG001': ('lpg',    'KG'),
}


def haversine_km(coord1, coord2):
    """Calculate great-circle distance between two (lat, lon) pairs in km."""
    import math
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(a))


def parse_sap_date(date_str):
    """SAP dates come as YYYYMMDD strings."""
    try:
        return datetime.strptime(date_str.strip(), '%Y%m%d').date()
    except Exception:
        return None


# ── SAP Parser ────────────────────────────────────────────────────────────────

def parse_sap(file_content: str) -> list[dict]:
    """
    Parse SAP flat file CSV export.
    Returns list of normalized emission record dicts.
    """
    results = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader):
        try:
            matnr = row['MATNR'].strip()
            if matnr not in MATERIAL_LOOKUP:
                errors.append({'row': i+2, 'reason': f'Unknown material {matnr}'})
                continue

            fuel_type, sap_unit = MATERIAL_LOOKUP[matnr]
            raw_unit = row['MEINS'].strip()
            quantity = Decimal(row['MENGE'].strip())
            doc_date = parse_sap_date(row['BLDAT'])

            if not doc_date:
                errors.append({'row': i+2, 'reason': 'Invalid date'})
                continue

            # Unit normalization: SAP 'L' = litres, 'KG' = kg
            if raw_unit == 'L':
                norm_unit = 'litres'
                if fuel_type == 'diesel':
                    ef = EMISSION_FACTORS['diesel_litre']
                    ef_label = 'DEFRA 2023 - Diesel'
                else:
                    ef = EMISSION_FACTORS['petrol_litre']
                    ef_label = 'DEFRA 2023 - Petrol'
            elif raw_unit == 'KG':
                norm_unit = 'kg'
                ef = EMISSION_FACTORS['lpg_kg']
                ef_label = 'DEFRA 2023 - LPG'
            else:
                errors.append({'row': i+2, 'reason': f'Unknown unit {raw_unit}'})
                continue

            co2e = quantity * ef

            results.append({
                'source_row_id':        f"SAP-{row['MANDT']}-{i+2}",
                'scope':                'SCOPE_1',
                'category':             'FUEL_STATIONARY',
                'raw_quantity':         float(quantity),
                'raw_unit':             raw_unit,
                'raw_data':             dict(row),
                'normalized_quantity':  float(round(co2e, 4)),
                'normalized_unit':      'kg_co2e',
                'emission_factor_used': float(ef),
                'emission_factor_source': ef_label,
                'period_start':         doc_date.isoformat(),
                'period_end':           doc_date.isoformat(),
                'facility_name':        PLANT_LOOKUP.get(row['WERKS'].strip(), row['WERKS']),
                'country':              'India',
                'description':          f"{row['MAKTX'].strip()} - {quantity} {norm_unit} from {row['NAME1'].strip()}",
            })

        except Exception as e:
            errors.append({'row': i+2, 'reason': str(e)})

    return results, errors


# ── Utility Parser ─────────────────────────────────────────────────────────────

def parse_utility(file_content: str) -> tuple[list[dict], list[dict]]:
    """
    Parse utility portal CSV export (Green Button style).
    """
    results = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader):
        try:
            kwh = Decimal(row['consumption_kwh'].strip())
            ef = EMISSION_FACTORS['electricity_kwh']
            co2e = kwh * ef

            period_start = date.fromisoformat(row['billing_period_start'].strip())
            period_end   = date.fromisoformat(row['billing_period_end'].strip())

            results.append({
                'source_row_id':        f"UTIL-{row['meter_id'].strip()}-{i+2}",
                'scope':                'SCOPE_2',
                'category':             'ELECTRICITY',
                'raw_quantity':         float(kwh),
                'raw_unit':             'kWh',
                'raw_data':             dict(row),
                'normalized_quantity':  float(round(co2e, 4)),
                'normalized_unit':      'kg_co2e',
                'emission_factor_used': float(ef),
                'emission_factor_source': 'CEA India Grid Emission Factor 2023',
                'period_start':         period_start.isoformat(),
                'period_end':           period_end.isoformat(),
                'facility_name':        row['facility_name'].strip(),
                'country':              'India',
                'description':          f"Electricity - {row['facility_name'].strip()} - {kwh} kWh ({row['tariff_code'].strip()})",
            })

        except Exception as e:
            errors.append({'row': i+2, 'reason': str(e)})

    return results, errors


# ── Travel Parser ──────────────────────────────────────────────────────────────

def parse_travel(file_content: str) -> tuple[list[dict], list[dict]]:
    """
    Parse Navan/Concur style travel export.
    Handles flights (with distance calc), hotels, and ground transport.
    """
    results = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader):
        try:
            segment = row['segment_type'].strip().upper()
            travel_date = date.fromisoformat(row['travel_date'].strip())
            return_date_str = row.get('return_date', '').strip()
            return_date = date.fromisoformat(return_date_str) if return_date_str else travel_date

            if segment == 'FLIGHT':
                origin = row['origin'].strip().upper()
                dest   = row['destination'].strip().upper()

                # Calculate distance from airport codes
                if origin in AIRPORT_COORDS and dest in AIRPORT_COORDS:
                    dist_km = Decimal(str(round(haversine_km(
                        AIRPORT_COORDS[origin], AIRPORT_COORDS[dest]
                    ), 2)))
                else:
                    # Unknown airport — flag it but still record
                    dist_km = Decimal('0')

                cabin = row.get('cabin_class', 'ECONOMY').strip().upper()
                ef_key = 'flight_business_km' if cabin == 'BUSINESS' else 'flight_economy_km'
                ef = EMISSION_FACTORS[ef_key]
                co2e = dist_km * ef

                results.append({
                    'source_row_id':        f"TRV-{row['trip_id'].strip()}-FLT-{i+2}",
                    'scope':                'SCOPE_3',
                    'category':             'BUSINESS_TRAVEL_AIR',
                    'raw_quantity':         float(dist_km),
                    'raw_unit':             'km',
                    'raw_data':             dict(row),
                    'normalized_quantity':  float(round(co2e, 4)),
                    'normalized_unit':      'kg_co2e',
                    'emission_factor_used': float(ef),
                    'emission_factor_source': 'DEFRA 2023 - Aviation',
                    'period_start':         travel_date.isoformat(),
                    'period_end':           return_date.isoformat(),
                    'facility_name':        '',
                    'country':              'India',
                    'description':          f"Flight {origin}→{dest} ({cabin}) - {row['traveler_name'].strip()} - {dist_km} km",
                })

            elif segment == 'HOTEL':
                nights = int(row.get('nights', 1) or 1)
                ef = EMISSION_FACTORS['hotel_night']
                co2e = Decimal(str(nights)) * ef

                results.append({
                    'source_row_id':        f"TRV-{row['trip_id'].strip()}-HTL-{i+2}",
                    'scope':                'SCOPE_3',
                    'category':             'BUSINESS_TRAVEL_HOTEL',
                    'raw_quantity':         float(nights),
                    'raw_unit':             'nights',
                    'raw_data':             dict(row),
                    'normalized_quantity':  float(round(co2e, 4)),
                    'normalized_unit':      'kg_co2e',
                    'emission_factor_used': float(ef),
                    'emission_factor_source': 'DEFRA 2023 - Hotel Stay',
                    'period_start':         travel_date.isoformat(),
                    'period_end':           travel_date.isoformat(),
                    'facility_name':        row.get('hotel_name', '').strip(),
                    'country':              'India',
                    'description':          f"Hotel - {row.get('hotel_name','').strip()} - {nights} nights - {row['traveler_name'].strip()}",
                })

            elif segment == 'GROUND':
                amount = Decimal(row.get('amount', '0').strip() or '0')
                ef = EMISSION_FACTORS['taxi_inr']
                co2e = amount * ef

                results.append({
                    'source_row_id':        f"TRV-{row['trip_id'].strip()}-GRD-{i+2}",
                    'scope':                'SCOPE_3',
                    'category':             'BUSINESS_TRAVEL_GROUND',
                    'raw_quantity':         float(amount),
                    'raw_unit':             'INR',
                    'raw_data':             dict(row),
                    'normalized_quantity':  float(round(co2e, 4)),
                    'normalized_unit':      'kg_co2e',
                    'emission_factor_used': float(ef),
                    'emission_factor_source': 'Spend-based estimate - Ground Transport',
                    'period_start':         travel_date.isoformat(),
                    'period_end':           travel_date.isoformat(),
                    'facility_name':        '',
                    'country':              'India',
                    'description':          f"Ground transport ({row.get('vendor','Taxi').strip()}) - {row['traveler_name'].strip()}",
                })

        except Exception as e:
            errors.append({'row': i+2, 'reason': str(e)})

    return results, errors

Step 3: Build the API Views
ingestion/views.py:
pythonfrom rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.base import ContentFile

from tenants.models import Tenant
from .models import DataIngestion
from emissions.models import EmissionRecord
from .parsers import parse_sap, parse_utility, parse_travel


class UploadView(APIView):
    """
    POST /api/upload/
    Accepts a CSV file + source_type + tenant_id
    Parses it and creates EmissionRecords
    """

    def post(self, request):
        file        = request.FILES.get('file')
        source_type = request.data.get('source_type')
        tenant_id   = request.data.get('tenant_id', 1)

        if not file or not source_type:
            return Response(
                {'error': 'file and source_type are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant = Tenant.objects.get(id=tenant_id)
        content = file.read().decode('utf-8')

        # Create the ingestion event record
        ingestion = DataIngestion.objects.create(
            tenant=tenant,
            source_type=source_type,
            original_filename=file.name,
            status='PROCESSING',
        )
        ingestion.file.save(file.name, ContentFile(content.encode()))

        # Pick the right parser
        parsers = {
            'SAP':     parse_sap,
            'UTILITY': parse_utility,
            'TRAVEL':  parse_travel,
        }

        if source_type not in parsers:
            ingestion.status = 'FAILED'
            ingestion.error_message = f'Unknown source type: {source_type}'
            ingestion.save()
            return Response({'error': 'Invalid source_type'}, status=400)

        records, errors = parsers[source_type](content)

        # Save all parsed records to the database
        created = []
        for rec in records:
            er = EmissionRecord.objects.create(
                tenant=tenant,
                ingestion=ingestion,
                source_row_id=rec['source_row_id'],
                scope=rec['scope'],
                category=rec['category'],
                raw_quantity=rec['raw_quantity'],
                raw_unit=rec['raw_unit'],
                raw_data=rec['raw_data'],
                normalized_quantity=rec['normalized_quantity'],
                normalized_unit=rec['normalized_unit'],
                emission_factor_used=rec['emission_factor_used'],
                emission_factor_source=rec['emission_factor_source'],
                period_start=rec['period_start'],
                period_end=rec['period_end'],
                facility_name=rec['facility_name'],
                country=rec['country'],
                description=rec['description'],
                status='PENDING',
            )
            created.append(er.id)

        # Update ingestion status
        ingestion.status = 'COMPLETED'
        ingestion.row_count = len(records)
        ingestion.error_count = len(errors)
        ingestion.save()

        return Response({
            'ingestion_id':   ingestion.id,
            'records_created': len(created),
            'errors':          errors,
            'status':          'COMPLETED',
        })
review/views.py:
pythonfrom rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from emissions.models import EmissionRecord
from .models import AuditLog


class RecordListView(APIView):
    """GET /api/records/ — list all emission records with optional filters"""

    def get(self, request):
        qs = EmissionRecord.objects.all()

        # Filters
        status_filter = request.query_params.get('status')
        scope_filter  = request.query_params.get('scope')
        source_filter = request.query_params.get('source_type')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if scope_filter:
            qs = qs.filter(scope=scope_filter)
        if source_filter:
            qs = qs.filter(ingestion__source_type=source_filter)

        data = []
        for r in qs:
            data.append({
                'id':                   r.id,
                'scope':                r.scope,
                'category':             r.category,
                'description':          r.description,
                'raw_quantity':         float(r.raw_quantity),
                'raw_unit':             r.raw_unit,
                'normalized_quantity':  float(r.normalized_quantity),
                'normalized_unit':      r.normalized_unit,
                'emission_factor_source': r.emission_factor_source,
                'period_start':         r.period_start.isoformat(),
                'period_end':           r.period_end.isoformat(),
                'facility_name':        r.facility_name,
                'status':               r.status,
                'flag_reason':          r.flag_reason,
                'source_type':          r.ingestion.source_type,
                'ingestion_id':         r.ingestion.id,
                'created_at':           r.created_at.isoformat(),
            })

        return Response({'records': data, 'total': len(data)})


class RecordActionView(APIView):
    """PATCH /api/records/<id>/action/ — approve, flag, or lock a record"""

    def patch(self, request, pk):
        try:
            record = EmissionRecord.objects.get(id=pk)
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        action     = request.data.get('action')   # 'approve', 'flag', 'lock'
        flag_reason = request.data.get('flag_reason', '')

        before = {'status': record.status}

        if action == 'approve':
            record.status = 'APPROVED'
            record.reviewed_at = timezone.now()
            audit_action = 'APPROVED'
        elif action == 'flag':
            record.status = 'FLAGGED'
            record.flag_reason = flag_reason
            audit_action = 'FLAGGED'
        elif action == 'lock':
            if record.status != 'APPROVED':
                return Response({'error': 'Only approved records can be locked'}, status=400)
            record.status = 'LOCKED'
            record.locked_at = timezone.now()
            audit_action = 'LOCKED'
        else:
            return Response({'error': 'Invalid action'}, status=400)

        record.save()

        # Write to audit log — immutable
        AuditLog.objects.create(
            record=record,
            action=audit_action,
            note=flag_reason,
            before_state=before,
            after_state={'status': record.status},
        )

        return Response({'id': record.id, 'status': record.status})


class StatsView(APIView):
    """GET /api/stats/ — summary numbers for the dashboard"""

    def get(self, request):
        records = EmissionRecord.objects.all()

        total_co2e = sum(float(r.normalized_quantity) for r in records)

        by_scope = {}
        for r in records:
            by_scope[r.scope] = by_scope.get(r.scope, 0) + float(r.normalized_quantity)

        by_status = {}
        for r in records:
            by_status[r.status] = by_status.get(r.status, 0) + 1

        return Response({
            'total_records': records.count(),
            'total_co2e_kg': round(total_co2e, 2),
            'by_scope':      by_scope,
            'by_status':     by_status,
        })

Step 4: Wire up URLs
breathe_backend/breathe_backend/urls.py:
pythonfrom django.contrib import admin
from django.urls import path
from ingestion.views import UploadView
from review.views import RecordListView, RecordActionView, StatsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/upload/', UploadView.as_view()),
    path('api/records/', RecordListView.as_view()),
    path('api/records/<int:pk>/action/', RecordActionView.as_view()),
    path('api/stats/', StatsView.as_view()),
]

Step 5: Create a Tenant + Test the API
bashpython manage.py shell
pythonfrom tenants.models import Tenant
Tenant.objects.create(name='Acme Corporation', slug='acme-corp')
exit()
Then start the server:
bashpython manage.py runserver
Test it by uploading the SAP file:
bashcurl -X POST http://127.0.0.1:8000/api/upload/ \
  -F "file=@sample_data/sap_export.csv" \
  -F "source_type=SAP" \
  -F "tenant_id=1"
You should see a response like:
json{
  "ingestion_id": 1,
  "records_created": 6,
  "errors": [],
  "status": "COMPLETED"
}
Then check records:
http://127.0.0.1:8000/api/records/
http://127.0.0.1:8000/api/stats/

Tell me when the API is working and we'll move to Day 3 — building the React frontend dashboard.You said: done, move to next partdone, move to next partMay 25Claude responded: Day 3: React FrontendDay 3: React Frontend
Step 1: Install dependencies
bashcd breathe-frontend
npm install axios recharts lucide-react

Step 2: Clean up default files
Delete everything inside src/ and replace with our own files.
src/index.css — replace everything with:
css* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f0f4f8;
  color: #1a202c;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { background: #cbd5e0; border-radius: 3px; }

Step 3: Create the API helper
src/api.js:
javascriptimport axios from 'axios';

const BASE = 'http://127.0.0.1:8000/api';

export const uploadFile = (file, sourceType, tenantId = 1) => {
  const form = new FormData();
  form.append('file', file);
  form.append('source_type', sourceType);
  form.append('tenant_id', tenantId);
  return axios.post(`${BASE}/upload/`, form);
};

export const getRecords = (filters = {}) => {
  return axios.get(`${BASE}/records/`, { params: filters });
};

export const getStats = () => {
  return axios.get(`${BASE}/stats/`);
};

export const doAction = (id, action, flagReason = '') => {
  return axios.patch(`${BASE}/records/${id}/action/`, {
    action,
    flag_reason: flagReason,
  });
};

Step 4: Build the components
Create a src/components/ folder. We'll build 4 components.

src/components/StatCard.jsx:
jsxexport default function StatCard({ label, value, sub, color = '#3182ce' }) {
  return (
    <div style={{
      background: '#fff',
      borderRadius: 12,
      padding: '20px 24px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
      borderTop: `4px solid ${color}`,
      minWidth: 180,
    }}>
      <div style={{ fontSize: 13, color: '#718096', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: '#1a202c' }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: '#a0aec0', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

src/components/UploadPanel.jsx:
jsximport { useState } from 'react';
import { uploadFile } from '../api';

const SOURCE_TYPES = [
  { value: 'SAP',     label: 'SAP — Fuel & Procurement',   color: '#2b6cb0' },
  { value: 'UTILITY', label: 'Utility — Electricity Data', color: '#276749' },
  { value: 'TRAVEL',  label: 'Travel — Flights / Hotels',  color: '#744210' },
];

export default function UploadPanel({ onDone }) {
  const [sourceType, setSourceType] = useState('SAP');
  const [file, setFile]             = useState(null);
  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState(null);
  const [error, setError]           = useState(null);
  const [dragging, setDragging]     = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await uploadFile(file, sourceType);
      setResult(res.data);
      onDone();
    } catch (e) {
      setError(e.response?.data?.error || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 28, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20 }}>Upload Data</h2>

      {/* Source type selector */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: '#718096', marginBottom: 8 }}>Source Type</div>
        <div style={{ display: 'flex', gap: 10 }}>
          {SOURCE_TYPES.map(s => (
            <button key={s.value} onClick={() => setSourceType(s.value)} style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: '2px solid',
              borderColor: sourceType === s.value ? s.color : '#e2e8f0',
              background: sourceType === s.value ? s.color : '#fff',
              color: sourceType === s.value ? '#fff' : '#4a5568',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 600,
              transition: 'all 0.15s',
            }}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('fileInput').click()}
        style={{
          border: `2px dashed ${dragging ? '#3182ce' : '#cbd5e0'}`,
          borderRadius: 10,
          padding: '36px 20px',
          textAlign: 'center',
          cursor: 'pointer',
          background: dragging ? '#ebf8ff' : '#f7fafc',
          transition: 'all 0.2s',
          marginBottom: 16,
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
        <div style={{ fontWeight: 600, color: '#2d3748' }}>
          {file ? file.name : 'Drop CSV here or click to browse'}
        </div>
        <div style={{ fontSize: 12, color: '#a0aec0', marginTop: 4 }}>
          Accepts .csv files
        </div>
        <input
          id="fileInput"
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={e => setFile(e.target.files[0])}
        />
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || loading}
        style={{
          width: '100%',
          padding: '12px',
          background: (!file || loading) ? '#cbd5e0' : '#3182ce',
          color: '#fff',
          border: 'none',
          borderRadius: 8,
          fontWeight: 700,
          fontSize: 15,
          cursor: (!file || loading) ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Processing...' : 'Upload & Parse'}
      </button>

      {/* Result */}
      {result && (
        <div style={{ marginTop: 16, padding: 14, background: '#f0fff4', borderRadius: 8, border: '1px solid #9ae6b4' }}>
          <div style={{ fontWeight: 700, color: '#276749' }}>✅ Upload successful</div>
          <div style={{ fontSize: 13, color: '#2f855a', marginTop: 4 }}>
            {result.records_created} records created · {result.errors.length} errors
          </div>
          {result.errors.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {result.errors.map((e, i) => (
                <div key={i} style={{ fontSize: 12, color: '#c53030' }}>Row {e.row}: {e.reason}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={{ marginTop: 16, padding: 14, background: '#fff5f5', borderRadius: 8, border: '1px solid #feb2b2' }}>
          <div style={{ color: '#c53030', fontWeight: 600 }}>❌ {error}</div>
        </div>
      )}
    </div>
  );
}

src/components/RecordTable.jsx:
jsximport { useState } from 'react';
import { doAction } from '../api';

const STATUS_COLORS = {
  PENDING:  { bg: '#fffbeb', text: '#92400e', border: '#fcd34d' },
  FLAGGED:  { bg: '#fff5f5', text: '#c53030', border: '#fc8181' },
  APPROVED: { bg: '#f0fff4', text: '#276749', border: '#9ae6b4' },
  LOCKED:   { bg: '#ebf4ff', text: '#2b6cb0', border: '#90cdf4' },
};

const SCOPE_LABELS = {
  SCOPE_1: '🔴 Scope 1',
  SCOPE_2: '🟡 Scope 2',
  SCOPE_3: '🔵 Scope 3',
};

export default function RecordTable({ records, onRefresh }) {
  const [flagModal, setFlagModal] = useState(null);
  const [flagReason, setFlagReason] = useState('');
  const [loading, setLoading] = useState(null);

  const act = async (id, action, reason = '') => {
    setLoading(id);
    try {
      await doAction(id, action, reason);
      onRefresh();
    } finally {
      setLoading(null);
      setFlagModal(null);
      setFlagReason('');
    }
  };

  if (records.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 60, color: '#a0aec0' }}>
        <div style={{ fontSize: 40 }}>📭</div>
        <div style={{ marginTop: 12, fontSize: 15 }}>No records found. Upload a file to get started.</div>
      </div>
    );
  }

  return (
    <>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>
              {['ID', 'Source', 'Scope', 'Description', 'Raw Value', 'CO₂e (kg)', 'Period', 'Facility', 'Status', 'Actions'].map(h => (
                <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: '#4a5568', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((r, i) => {
              const s = STATUS_COLORS[r.status] || STATUS_COLORS.PENDING;
              return (
                <tr key={r.id} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb', borderBottom: '1px solid #e2e8f0' }}>
                  <td style={{ padding: '10px 12px', color: '#718096' }}>#{r.id}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                      background: r.source_type === 'SAP' ? '#ebf8ff' : r.source_type === 'UTILITY' ? '#f0fff4' : '#fffbeb',
                      color: r.source_type === 'SAP' ? '#2b6cb0' : r.source_type === 'UTILITY' ? '#276749' : '#744210',
                    }}>{r.source_type}</span>
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>{SCOPE_LABELS[r.scope]}</td>
                  <td style={{ padding: '10px 12px', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    title={r.description}>{r.description}</td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>{r.raw_quantity} {r.raw_unit}</td>
                  <td style={{ padding: '10px 12px', fontWeight: 700, color: '#2d3748' }}>
                    {r.normalized_quantity.toFixed(2)}
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: '#718096', fontSize: 12 }}>
                    {r.period_start}<br />{r.period_end !== r.period_start ? `→ ${r.period_end}` : ''}
                  </td>
                  <td style={{ padding: '10px 12px', color: '#718096' }}>{r.facility_name || '—'}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700,
                      background: s.bg, color: s.text, border: `1px solid ${s.border}` }}>
                      {r.status}
                    </span>
                    {r.flag_reason && (
                      <div style={{ fontSize: 11, color: '#c53030', marginTop: 3 }} title={r.flag_reason}>
                        ⚠ {r.flag_reason.slice(0, 30)}...
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                    {r.status === 'PENDING' && (
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button onClick={() => act(r.id, 'approve')} disabled={loading === r.id}
                          style={{ padding: '4px 10px', background: '#276749', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                          ✓ Approve
                        </button>
                        <button onClick={() => setFlagModal(r.id)}
                          style={{ padding: '4px 10px', background: '#c53030', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                          ⚑ Flag
                        </button>
                      </div>
                    )}
                    {r.status === 'FLAGGED' && (
                      <button onClick={() => act(r.id, 'approve')} disabled={loading === r.id}
                        style={{ padding: '4px 10px', background: '#276749', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                        ✓ Approve
                      </button>
                    )}
                    {r.status === 'APPROVED' && (
                      <button onClick={() => act(r.id, 'lock')} disabled={loading === r.id}
                        style={{ padding: '4px 10px', background: '#2b6cb0', color: '#fff', border: 'none', borderRadius: 5, cursor: 'pointer', fontSize: 12 }}>
                        🔒 Lock
                      </button>
                    )}
                    {r.status === 'LOCKED' && (
                      <span style={{ fontSize: 12, color: '#a0aec0' }}>🔒 Locked</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Flag Modal */}
      {flagModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 28, width: 420, boxShadow: '0 20px 60px rgba(0,0,0,0.2)' }}>
            <h3 style={{ marginBottom: 12 }}>Flag Record #{flagModal}</h3>
            <p style={{ color: '#718096', fontSize: 13, marginBottom: 16 }}>Describe why this record needs attention:</p>
            <textarea
              value={flagReason}
              onChange={e => setFlagReason(e.target.value)}
              placeholder="e.g. Unusually high consumption — verify meter reading"
              style={{ width: '100%', height: 90, padding: 10, borderRadius: 8, border: '1px solid #cbd5e0', fontSize: 13, resize: 'none' }}
            />
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <button onClick={() => act(flagModal, 'flag', flagReason)}
                style={{ flex: 1, padding: 10, background: '#c53030', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: 'pointer' }}>
                Submit Flag
              </button>
              <button onClick={() => setFlagModal(null)}
                style={{ flex: 1, padding: 10, background: '#e2e8f0', color: '#4a5568', border: 'none', borderRadius: 8, fontWeight: 700, cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

src/components/Charts.jsx:
jsximport { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const SCOPE_COLORS  = { SCOPE_1: '#fc8181', SCOPE_2: '#f6e05e', SCOPE_3: '#63b3ed' };
const STATUS_COLORS = { PENDING: '#f6ad55', FLAGGED: '#fc8181', APPROVED: '#68d391', LOCKED: '#63b3ed' };

export default function Charts({ stats }) {
  if (!stats) return null;

  const scopeData = Object.entries(stats.by_scope || {}).map(([k, v]) => ({
    name: k.replace('_', ' '), value: Math.round(v), fill: SCOPE_COLORS[k] || '#a0aec0',
  }));

  const statusData = Object.entries(stats.by_status || {}).map(([k, v]) => ({
    name: k, value: v, fill: STATUS_COLORS[k] || '#a0aec0',
  }));

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      {/* CO2e by Scope */}
      <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
        <div style={{ fontWeight: 700, marginBottom: 16, color: '#2d3748' }}>CO₂e by Scope (kg)</div>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie data={scopeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
              {scopeData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Records by Status */}
      <div style={{ background: '#fff', borderRadius: 12, padding: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
        <div style={{ fontWeight: 700, marginBottom: 16, color: '#2d3748' }}>Records by Status</div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={statusData}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {statusData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

Step 5: Main App
Replace src/App.js entirely:
jsximport { useState, useEffect, useCallback } from 'react';
import { getRecords, getStats } from './api';
import StatCard from './components/StatCard';
import UploadPanel from './components/UploadPanel';
import RecordTable from './components/RecordTable';
import Charts from './components/Charts';

const FILTERS = [
  { label: 'All',      value: '' },
  { label: 'Pending',  value: 'PENDING' },
  { label: 'Flagged',  value: 'FLAGGED' },
  { label: 'Approved', value: 'APPROVED' },
  { label: 'Locked',   value: 'LOCKED' },
];

const SOURCE_FILTERS = [
  { label: 'All Sources', value: '' },
  { label: 'SAP',         value: 'SAP' },
  { label: 'Utility',     value: 'UTILITY' },
  { label: 'Travel',      value: 'TRAVEL' },
];

export default function App() {
  const [tab, setTab]           = useState('dashboard'); // 'dashboard' | 'upload'
  const [records, setRecords]   = useState([]);
  const [stats, setStats]       = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [loading, setLoading]   = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [recRes, statRes] = await Promise.all([
        getRecords({ status: statusFilter, source_type: sourceFilter }),
        getStats(),
      ]);
      setRecords(recRes.data.records);
      setStats(statRes.data);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, sourceFilter]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const totalCO2e = stats ? (stats.total_co2e_kg / 1000).toFixed(2) : '—';

  return (
    <div style={{ minHeight: '100vh', background: '#f0f4f8' }}>

      {/* Header */}
      <div style={{ background: '#1a202c', padding: '0 32px', display: 'flex', alignItems: 'center', gap: 32 }}>
        <div style={{ color: '#fff', fontWeight: 800, fontSize: 20, padding: '18px 0' }}>
          🌿 Breathe ESG
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {[['dashboard', '📊 Dashboard'], ['upload', '📤 Upload']].map(([key, label]) => (
            <button key={key} onClick={() => setTab(key)} style={{
              padding: '18px 20px',
              background: 'none',
              border: 'none',
              borderBottom: tab === key ? '3px solid #68d391' : '3px solid transparent',
              color: tab === key ? '#fff' : '#a0aec0',
              fontWeight: 600,
              fontSize: 14,
              cursor: 'pointer',
            }}>{label}</button>
          ))}
        </div>
        <div style={{ marginLeft: 'auto', color: '#68d391', fontWeight: 600, fontSize: 13 }}>
          Acme Corporation
        </div>
      </div>

      <div style={{ padding: 32, maxWidth: 1400, margin: '0 auto' }}>

        {tab === 'upload' && (
          <UploadPanel onDone={() => { fetchAll(); setTab('dashboard'); }} />
        )}

        {tab === 'dashboard' && (
          <>
            {/* Stat cards */}
            <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
              <StatCard label="Total Records"    value={stats?.total_records ?? '—'}  color="#3182ce" />
              <StatCard label="Total CO₂e"       value={`${totalCO2e} t`}             color="#e53e3e" sub="tonnes CO2 equivalent" />
              <StatCard label="Pending Review"   value={stats?.by_status?.PENDING ?? 0}  color="#d69e2e" />
              <StatCard label="Flagged"          value={stats?.by_status?.FLAGGED ?? 0}  color="#c53030" />
              <StatCard label="Approved"         value={stats?.by_status?.APPROVED ?? 0} color="#276749" />
              <StatCard label="Locked"           value={stats?.by_status?.LOCKED ?? 0}   color="#2b6cb0" />
            </div>

            {/* Charts */}
            <div style={{ marginBottom: 24 }}>
              <Charts stats={stats} />
            </div>

            {/* Records table */}
            <div style={{ background: '#fff', borderRadius: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
              <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, marginRight: 8 }}>Emission Records</h2>

                {/* Status filter */}
                <div style={{ display: 'flex', gap: 6 }}>
                  {FILTERS.map(f => (
                    <button key={f.value} onClick={() => setStatusFilter(f.value)} style={{
                      padding: '5px 12px', borderRadius: 20, border: '1px solid',
                      borderColor: statusFilter === f.value ? '#3182ce' : '#e2e8f0',
                      background: statusFilter === f.value ? '#ebf8ff' : '#fff',
                      color: statusFilter === f.value ? '#2b6cb0' : '#4a5568',
                      fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    }}>{f.label}</button>
                  ))}
                </div>

                {/* Source filter */}
                <div style={{ display: 'flex', gap: 6, marginLeft: 8 }}>
                  {SOURCE_FILTERS.map(f => (
                    <button key={f.value} onClick={() => setSourceFilter(f.value)} style={{
                      padding: '5px 12px', borderRadius: 20, border: '1px solid',
                      borderColor: sourceFilter === f.value ? '#805ad5' : '#e2e8f0',
                      background: sourceFilter === f.value ? '#faf5ff' : '#fff',
                      color: sourceFilter === f.value ? '#553c9a' : '#4a5568',
                      fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    }}>{f.label}</button>
                  ))}
                </div>

                {loading && <span style={{ fontSize: 12, color: '#a0aec0', marginLeft: 'auto' }}>Refreshing...</span>}
              </div>

              <RecordTable records={records} onRefresh={fetchAll} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

Step 6: Run the frontend
bashnpm start
Visit http://localhost:3000 — you should see the full dashboard.
Test the full flow:

Click Upload tab
Select SAP, drop in sap_export.csv → click Upload
Repeat for UTILITY and TRAVEL
Go to Dashboard — see all records, charts, stats
Approve a few records, flag one with a reason, lock an approved one


Tell me when it's working and we'll do Day 4 — the four markdown docs + deployment to Railway + Vercel.You said: nextnext1:57 PMClaude responded: Day 4: Documentation + DeploymentDay 4: Documentation + Deployment
Part 1: Write the 4 Required Docs
Create these files in your root breathe-esg/ folder:

MODEL.md:
markdown# Data Model — Breathe ESG Prototype

## Overview

The data model is built around one central question: **how do you take messy,
inconsistent data from three completely different sources and produce a single,
auditable, trustworthy emissions record?**

The answer is a clean separation between:
- What came in (raw, never touched)
- What we computed (normalized, explainable)
- What an analyst decided (review workflow)
- What happened over time (immutable audit trail)

---

## Tables

### `Tenant`
Represents a client company. Every record in the system belongs to a tenant.
This is the foundation of multi-tenancy — no data ever crosses tenant boundaries
because every query filters by tenant foreign key.

| Field | Type | Why |
|-------|------|-----|
| name | CharField | Human-readable company name |
| slug | SlugField (unique) | URL-safe identifier e.g. `acme-corp` |
| created_at | DateTimeField | Onboarding timestamp |

---

### `DataIngestion`
One upload event. If a facilities manager uploads a utility CSV on Jan 15,
that is one DataIngestion row. It tracks the file, who uploaded it, when,
and whether parsing succeeded or failed.

| Field | Type | Why |
|-------|------|-----|
| tenant | FK → Tenant | Ownership |
| source_type | CharField | SAP / UTILITY / TRAVEL |
| file | FileField | Original file stored for re-processing |
| original_filename | CharField | Audit trail — what the user actually uploaded |
| status | CharField | PROCESSING / COMPLETED / FAILED |
| error_message | TextField | Why it failed, if it did |
| row_count | IntegerField | How many rows were successfully parsed |
| error_count | IntegerField | How many rows were skipped |
| uploaded_at | DateTimeField | When the upload happened |
| uploaded_by | FK → User | Who uploaded it |

**Why store the original file?**
Because parsers can have bugs. If we discover our SAP parser miscalculated
units in February, we need to be able to re-parse from the original source
without asking the client to re-upload.

---

### `EmissionRecord`
The core of the system. One normalized row of emission data, regardless of
whether it came from SAP, a utility bill, or a travel platform.

#### Traceability fields
| Field | Type | Why |
|-------|------|-----|
| tenant | FK → Tenant | Multi-tenancy |
| ingestion | FK → DataIngestion | Which upload produced this row |
| source_row_id | CharField | Original row identifier from source system |

#### Classification (GHG Protocol)
| Field | Type | Why |
|-------|------|-----|
| scope | CharField | SCOPE_1 / SCOPE_2 / SCOPE_3 |
| category | CharField | e.g. FUEL_STATIONARY, ELECTRICITY, BUSINESS_TRAVEL_AIR |

Scope follows the GHG Protocol Corporate Standard — the global framework
all carbon auditors use. Scope 1 = direct emissions (fuel burned on-site),
Scope 2 = indirect from purchased electricity, Scope 3 = value chain
(travel, supply chain).

#### Raw values — never modified
| Field | Type | Why |
|-------|------|-----|
| raw_quantity | DecimalField | Exactly as it came in — 5000.000 |
| raw_unit | CharField | Exactly as it came in — L, KG, kWh |
| raw_data | JSONField | The entire original row as JSON |

Raw values are sacred. We never overwrite them. If an analyst edits a record,
we write a new version and log the change — we do not mutate raw_quantity.

#### Normalized values
| Field | Type | Why |
|-------|------|-----|
| normalized_quantity | DecimalField | Always in kg CO2e |
| normalized_unit | CharField | Always kg_co2e |
| emission_factor_used | DecimalField | The factor applied e.g. 2.6391 |
| emission_factor_source | CharField | e.g. DEFRA 2023 — Diesel |

Every emission record stores the exact factor used and its source. This is
non-negotiable for auditors — they need to verify the calculation themselves.

#### Review workflow
| Field | Type | Why |
|-------|------|-----|
| status | CharField | PENDING → APPROVED → LOCKED (or FLAGGED) |
| flag_reason | TextField | Why an analyst flagged it |
| reviewed_by | FK → User | Who approved it |
| reviewed_at | DateTimeField | When they approved it |
| locked_at | DateTimeField | When it was locked for audit |

Status transitions are one-directional: you cannot un-lock a locked record.
This protects audit integrity.

---

### `AuditLog`
An append-only log of every state change on every EmissionRecord. Rows are
never deleted or edited. This is what makes the system auditable.

| Field | Type | Why |
|-------|------|-----|
| record | FK → EmissionRecord | Which record changed |
| action | CharField | CREATED / EDITED / FLAGGED / APPROVED / LOCKED |
| performed_by | FK → User | Who did it |
| note | TextField | Optional human explanation |
| before_state | JSONField | Snapshot of record before change |
| after_state | JSONField | Snapshot of record after change |
| performed_at | DateTimeField | auto_now_add — immutable timestamp |

---

## Scope 1 / 2 / 3 Mapping

| Source | Scope | Category |
|--------|-------|----------|
| SAP — Diesel | Scope 1 | FUEL_STATIONARY |
| SAP — Petrol | Scope 1 | FUEL_MOBILE |
| SAP — LPG | Scope 1 | FUEL_STATIONARY |
| Utility — kWh | Scope 2 | ELECTRICITY |
| Travel — Flight | Scope 3 | BUSINESS_TRAVEL_AIR |
| Travel — Hotel | Scope 3 | BUSINESS_TRAVEL_HOTEL |
| Travel — Ground | Scope 3 | BUSINESS_TRAVEL_GROUND |

---

## Unit Normalization

All quantities are normalized to **kg CO2e** (kilograms of CO2 equivalent).
This is the standard unit used in GHG reporting.

Conversion pipeline:
raw_quantity (any unit) × emission_factor (kg CO2e per unit) = normalized_quantity (kg CO2e)

Example:
5000 litres diesel × 2.6391 kg CO2e/litre = 13,195.5 kg CO2e 


Emission factors sourced from:
- DEFRA 2023 (UK government, internationally used)
- CEA India Grid Emission Factor 2023 (for electricity)