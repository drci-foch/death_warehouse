from django.contrib import admin
from .models import INSEEPatient, WarehousePatient
from .models import UserActionLog


@admin.register(INSEEPatient)
class INSEEPatientAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "prenom",
        "date_naiss",
        "pays_naiss",
        "lieu_naiss",
        "code_naiss",
        "date_deces",
    )


@admin.register(WarehousePatient)
class WarehousePatientAdmin(admin.ModelAdmin):
    list_display = (
        "PATIENT_NUM",
        "LASTNAME",
        "FIRSTNAME",
        "BIRTH_DATE",
        "SEX",
        "MAIL",
        "MAIDEN_NAME",
        "DEATH_DATE",
        "BIRTH_COUNTRY",
        "HOSPITAL_PATIENT_ID",
    )


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ("action", "timestamp", "user_ip")
    list_filter = ("action", "timestamp")
    search_fields = ("action", "user_ip", "details")
    readonly_fields = ("action", "timestamp", "user_ip", "details")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
