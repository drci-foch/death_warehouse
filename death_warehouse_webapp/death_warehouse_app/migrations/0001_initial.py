# Generated by Django 4.2.6 on 2023-10-11 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RecherchePatient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.TextField(max_length=100)),
                ('prenom', models.TextField(max_length=100)),
                ('date_naiss', models.DateField()),
                ('pays_naiss', models.CharField(max_length=100)),
                ('lieu_naiss', models.CharField(max_length=100)),
                ('code_naiss', models.CharField(max_length=10)),
            ],
        ),
    ]
