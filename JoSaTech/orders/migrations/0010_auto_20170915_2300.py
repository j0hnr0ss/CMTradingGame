# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-15 21:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_auto_20170915_2255'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trade',
            name='quantity',
            field=models.IntegerField(max_length=8),
        ),
    ]
