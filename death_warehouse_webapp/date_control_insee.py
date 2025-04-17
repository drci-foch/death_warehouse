import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "death_warehouse_webapp.settings")
django.setup()

from death_warehouse_app.models import INSEEPatient
from django.db import models


def delete_invalid_records():
    # Filter out records where death_date is less than birth_date
    invalid_records = INSEEPatient.objects.filter(date_deces__lt=models.F("date_naiss"))

    print(f"Deleting {invalid_records.count()} invalid records")

    # Delete the filtered records
    invalid_records.delete()


delete_invalid_records()
