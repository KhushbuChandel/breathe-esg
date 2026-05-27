from django.db import models
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