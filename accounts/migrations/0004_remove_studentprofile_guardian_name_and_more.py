# Generated by Django 5.2.1 on 2025-05-13 05:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_remove_parentprofile_children_studentprofile_parent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentprofile',
            name='guardian_name',
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='nationality',
            field=models.CharField(default='Nigeria', max_length=50),
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='preferred_contact_method',
            field=models.CharField(choices=[('phone', 'phone'), ('email', 'Email'), ('sms', 'SMS')], default='phone', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='relationship_to_student',
            field=models.CharField(default='Father', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='parentprofile',
            name='state',
            field=models.CharField(default='Lagos', max_length=50),
        ),
        migrations.AlterField(
            model_name='studentprofile',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='accounts.parentprofile'),
        ),
    ]
