# Generated by Django 5.2.1 on 2025-05-13 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_alter_studentprofile_date_of_birth'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentprofile',
            name='date_of_birth',
            field=models.DateField(default='2025-05-05'),
        ),
    ]
