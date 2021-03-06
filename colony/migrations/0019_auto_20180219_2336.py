# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2018-02-20 04:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colony', '0018_auto_20180217_1914'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalcage',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalgenotype',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicallitter',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalmouse',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalperson',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalspecialrequest',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
