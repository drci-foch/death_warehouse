from datetime import datetime

from dateutil.parser import parse as parse_date
from django.core import exceptions
from django.db import models
from django.utils import timezone


class CustomDateField(models.DateField):
    def to_python(self, value):
        if value is None:
            return value
        if isinstance(value, str):
            try:
                parsed = parse_date(value)
                if parsed is not None:
                    return parsed.date()
            except ValueError:
                pass

        raise exceptions.ValidationError(
            self.error_messages["invalid"],
            code="invalid",
            params={"value": value},
        )

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, datetime):
            return value.date()
        return value

    def formfield(self, **kwargs):
        defaults = {"input_formats": ["%Y/%m/%d"]}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class INSEEPatient(models.Model):
    nom = models.TextField(max_length=100, db_index=True)
    # TO DO :indexer avec le bon index (type pour icontains)
    prenom = models.TextField(max_length=100)
    date_naiss = CustomDateField(db_index=True)
    pays_naiss = models.CharField(max_length=100, blank=True)
    lieu_naiss = models.CharField(max_length=100, blank=True)
    code_naiss = models.CharField(max_length=10, blank=True)
    date_deces = CustomDateField(validators=[], blank=True, null=True, default="1970-01-01")


class WarehousePatient(models.Model):
    PATIENT_NUM = models.CharField(max_length=50, null=True)
    LASTNAME = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    # TO DO :indexer avec le bon index (type pour icontains)
    FIRSTNAME = models.CharField(max_length=100, blank=True, null=True)
    BIRTH_DATE = models.DateField(null=True, db_index=True)
    SEX = models.CharField(max_length=10, blank=True, null=True)
    MAIL = models.CharField(max_length=100, blank=True, null=True)
    MAIDEN_NAME = models.CharField(max_length=100, null=True, blank=True)
    DEATH_DATE = models.DateField(null=True, blank=True)
    BIRTH_COUNTRY = models.CharField(max_length=50, blank=True, null=True)
    HOSPITAL_PATIENT_ID = models.IntegerField(null=True)


class UserActionLog(models.Model):
    """Model to log user actions in the application"""

    ACTION_CHOICES = (
        ("search", "Patient Search"),
        ("export_csv", "Export to CSV"),
        ("export_xlsx", "Export to Excel"),
        ("import_file", "Import File"),
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(blank=True, null=True)  # For storing additional information

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} at {self.timestamp}"
