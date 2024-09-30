# Generated by Django 5.1.1 on 2024-09-19 23:10

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0002_patient"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="timestamp",
            field=models.DateTimeField(
                auto_now_add=True,
                default=datetime.datetime(
                    2024, 9, 19, 23, 10, 16, 43867, tzinfo=datetime.timezone.utc
                ),
            ),
            preserve_default=False,
        ),
    ]