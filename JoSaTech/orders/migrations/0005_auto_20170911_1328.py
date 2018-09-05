# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-11 11:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_auto_20170911_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='buysell',
            field=models.CharField(max_length=4),
        ),
        migrations.AlterField(
            model_name='order',
            name='filled',
            field=models.FloatField(default=0, max_length=8),
        ),
        migrations.AlterField(
            model_name='order',
            name='fund_name',
            field=models.CharField(default='Test', max_length=250),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_order',
            field=models.FloatField(default=0, max_length=8),
        ),
    ]
