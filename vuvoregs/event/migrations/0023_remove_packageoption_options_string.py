# Generated by Django 5.1.7 on 2025-04-04 19:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0022_alter_event_max_participants_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='packageoption',
            name='options_string',
        ),
    ]
