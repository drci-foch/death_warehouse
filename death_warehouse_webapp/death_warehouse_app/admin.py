from django.contrib import admin
from .models import INSEEPatient, WarehousePatient

@admin.register(INSEEPatient)
class INSEEPatientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'date_naiss', 'pays_naiss', 'lieu_naiss', 'code_naiss', 'date_deces')

@admin.register(WarehousePatient)
class WarehousePatientAdmin(admin.ModelAdmin):
    list_display = ('PATIENT_NUM', 'LASTNAME', 'FIRSTNAME', 'BIRTH_DATE', 'SEX', 'MAIL', 'MAIDEN_NAME', 'DEATH_DATE', 'BIRTH_COUNTRY', 'HOSPITAL_PATIENT_ID')
