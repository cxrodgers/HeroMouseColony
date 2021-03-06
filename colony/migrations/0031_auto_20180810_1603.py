# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-10 20:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colony', '0030_auto_20180807_1221'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalmouse',
            name='pure_breeder',
            field=models.BooleanField(default=False, help_text='Check this box if this mouse was acquired as a pure breeder or wild type (e.g., anything from JAX). Its progeny with a wild type will automatically inherit this status.'),
        ),
        migrations.AlterField(
            model_name='historicalmouse',
            name='wild_type',
            field=models.BooleanField(default=False, help_text='Check this box if this mouse was acquired as a pure wild type (e.g., from JAX). If it is a wild type, it is also a pure breeder.'),
        ),
        migrations.AlterField(
            model_name='mouse',
            name='pure_breeder',
            field=models.BooleanField(default=False, help_text='Check this box if this mouse was acquired as a pure breeder or wild type (e.g., anything from JAX). Its progeny with a wild type will automatically inherit this status.'),
        ),
        migrations.AlterField(
            model_name='mouse',
            name='wild_type',
            field=models.BooleanField(default=False, help_text='Check this box if this mouse was acquired as a pure wild type (e.g., from JAX). If it is a wild type, it is also a pure breeder.'),
        ),
    ]
