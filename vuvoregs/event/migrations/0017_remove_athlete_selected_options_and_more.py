# Generated by Django 5.1.7 on 2025-03-31 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0016_remove_athlete_selected_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='athlete',
            name='selected_options',
        ),
        migrations.AddField(
            model_name='athlete',
            name='selected_options',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
