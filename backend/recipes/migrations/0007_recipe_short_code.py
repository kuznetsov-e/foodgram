# Generated by Django 3.2.3 on 2024-11-05 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_auto_20241103_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='short_code',
            field=models.CharField(blank=True, max_length=10, unique=True),
        ),
    ]
