# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-08-15 07:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Payment',
            new_name='AliPayment',
        ),
    ]
