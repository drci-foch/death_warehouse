from django.db.models import Count
from django.db.models.functions import ExtractMonth, ExtractYear

# Setup Django environment
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'death_warehouse_webapp.settings')
django.setup()

# Import your INSEEPatient model
from death_warehouse_app.models import INSEEPatient

# Annotate each INSEEPatient object with both month and year extracted from date_deces
observations_per_month_year = (
    INSEEPatient.objects
    .annotate(month=ExtractMonth('date_deces'), year=ExtractYear('date_deces'))
    .values('month', 'year')  # Group by the extracted month and year
    .annotate(count=Count('id'))  # Count the number of occurrences for each group
    .order_by('year', 'month')  # Order the results by year and then by month
)

# Display the results iteratively
for observation in observations_per_month_year:
    print(f"Year: {observation['year']}, Month: {observation['month']}, Observations: {observation['count']}")
