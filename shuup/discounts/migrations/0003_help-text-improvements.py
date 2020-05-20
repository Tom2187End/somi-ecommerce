# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-01-29 09:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discounts', '0002_add_supplier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='active',
            field=models.BooleanField(default=True, help_text='Enable this if the discount is currently active. Please also set a start and an end date.', verbose_name='active'),
        ),
        migrations.AlterField(
            model_name='happyhour',
            name='name',
            field=models.CharField(help_text='The name for this HappyHour. Used internally with exception lists for filtering.', max_length=120, verbose_name='name'),
        ),
    ]
