# Generated by Django 5.2.3 on 2025-06-29 14:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminuser',
            name='has_dashboard_access',
        ),
    ]
