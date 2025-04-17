import os
import django
from django.db.models import Count
from django.db.models.functions import ExtractYear, ExtractMonth
import logging

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "death_warehouse_webapp.settings")
django.setup()
logger = logging.getLogger(__name__)

from death_warehouse_app.models import INSEEPatient


def count_deaths_by_year_month():
    try:
        # Annotate each record with its year and month of death
        queryset = (
            INSEEPatient.objects.annotate(
                year=ExtractYear("date_deces"), month=ExtractMonth("date_deces")
            )
            .values("year", "month")
            .annotate(
                count=Count("id")  # Count the number of records in each group
            )
            .order_by("year", "month")
        )

        # Display the results
        for entry in queryset:
            year = entry["year"]
            month = entry["month"]
            count = entry["count"]
            print(f"Year: {year}, Month: {month}, Deaths: {count}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    count_deaths_by_year_month()
