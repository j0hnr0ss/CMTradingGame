# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-19 19:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_closingprice'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ClosingPrice',
            new_name='Price',
        ),
    ]
