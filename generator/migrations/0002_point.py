# Generated by Django 3.1.4 on 2021-03-05 00:46

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('generator', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Point',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wsg48Point', django.contrib.gis.db.models.fields.PointField(srid=4326, unique=True)),
                ('macPoint', django.contrib.gis.db.models.fields.PointField(srid=4326, unique=True)),
                ('color', models.TextField()),
                ('pixal_xy', models.TextField()),
                ('height', models.FloatField()),
                ('world_pixal_xy', models.TextField()),
            ],
        ),
    ]