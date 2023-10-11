from django.db import models

class RecherchePatient(models.Model):
    nom = models.TextField(max_length=100)
    prenom = models.TextField(max_length=100)
    date_naiss = models.DateField(validators=[], null=True)
    pays_naiss = models.CharField(max_length=100, blank=True)
    lieu_naiss = models.CharField(max_length=100, blank=True)
    code_naiss = models.CharField(max_length=10, blank=True)
    date_deces = models.DateField(validators=[], null=True, blank=True)
    code_deces = models.CharField(max_length=10, blank=True)

