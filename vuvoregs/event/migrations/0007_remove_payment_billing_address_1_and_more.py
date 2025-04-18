# Generated by Django 5.1.7 on 2025-03-18 22:50

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0006_alter_registration_payment_status_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='billing_address_1',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_address_2',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_city',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_country_area',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_country_code',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_email',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_first_name',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_last_name',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_phone',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='billing_postcode',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='captured_amount',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='created',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='customer_ip_address',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='delivery',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='description',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='extra_data',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='fraud_message',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='fraud_status',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='message',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='modified',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='tax',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='token',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='total',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='transaction_id',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='variant',
        ),
        migrations.AddField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='payment',
            name='order_code',
            field=models.CharField(default=uuid.uuid4, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='currency',
            field=models.CharField(default='EUR', max_length=3),
        ),
        migrations.AlterField(
            model_name='payment',
            name='registration',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='event.registration'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='registration',
            name='payment_status',
            field=models.CharField(choices=[('not_paid', 'Not Paid'), ('paid', 'Paid'), ('failed', 'Payment Failed')], default='not_paid', max_length=20),
        ),
    ]
