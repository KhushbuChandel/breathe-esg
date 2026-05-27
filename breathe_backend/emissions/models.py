from django.db import models
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