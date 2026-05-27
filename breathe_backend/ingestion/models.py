from django.db import models
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