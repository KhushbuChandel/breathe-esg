from django.db import models

class Tenant(models.Model):
    """A client company using the platform"""
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)  # e.g. 'acme-corp'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name