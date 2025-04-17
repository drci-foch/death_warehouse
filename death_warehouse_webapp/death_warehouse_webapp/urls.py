"""
URL configuration for death_warehouse_webapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from death_warehouse_app.views import home, import_file, export_results_csv, export_results_xlsx, patient_data_view, run_scripts, latestdate, get_recent_death_date_from_database

urlpatterns = [
    path('', home, name='home'),
    path('import/', import_file, name='import_file'),
    path('export_results_csv/', export_results_csv, name='export_results_csv'),
    path('export_results_xlsx/', export_results_xlsx, name='export_results_xlsx'),
    path('test/', patient_data_view, name='test'),
    path('admin/', admin.site.urls),
    path('run-scripts/', run_scripts, name='run_scripts'),
    path('import/', latestdate, name='latestdate'),
    path('get_recent_death_date_from_database/', get_recent_death_date_from_database, name='get_recent_death_date_from_database'),
]
