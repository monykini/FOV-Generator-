# Generated by Django 3.1.4 on 2021-03-11 13:21

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('generator', '0008_auto_20210307_2141'),
    ]

    operations = [
        migrations.CreateModel(
            name='maxElevation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tile', django.contrib.gis.db.models.fields.RasterField(srid=4326)),
            ],
        ),
    ]