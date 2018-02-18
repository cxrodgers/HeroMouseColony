# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2018-02-18 00:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colony', '0017_auto_20180123_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cage',
            name='location',
            field=models.IntegerField(choices=[(0, '1710'), (1, '1702'), (2, 'Behavior'), (3, '1736'), (4, 'SC2-011'), (5, 'L7-007'), (6, 'SC2-056')], default=4),
        ),
        migrations.AlterField(
            model_name='historicalcage',
            name='location',
            field=models.IntegerField(choices=[(0, '1710'), (1, '1702'), (2, 'Behavior'), (3, '1736'), (4, 'SC2-011'), (5, 'L7-007'), (6, 'SC2-056')], default=4),
        ),
    ]