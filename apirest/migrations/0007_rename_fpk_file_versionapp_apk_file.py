# Generated by Django 4.2.1 on 2024-05-03 14:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0006_alter_versionapp_fpk_file'),
    ]

    operations = [
        migrations.RenameField(
            model_name='versionapp',
            old_name='fpk_file',
            new_name='apk_file',
        ),
    ]
