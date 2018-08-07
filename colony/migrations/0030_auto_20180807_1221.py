# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-07 16:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colony', '0029_auto_20180806_1941'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalperson',
            name='login_name',
            field=models.CharField(db_index=True, help_text='this must be manually set to be the same as their login name in order to make their personalized census view work', max_length=15),
        ),
        migrations.AlterField(
            model_name='person',
            name='login_name',
            field=models.CharField(help_text='this must be manually set to be the same as their login name in order to make their personalized census view work', max_length=15, unique=True),
        ),
    ]
