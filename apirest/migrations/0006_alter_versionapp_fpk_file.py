# Generated by Django 5.0.4 on 2024-05-02 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0005_versionapp_fpk_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='versionapp',
            name='fpk_file',
            field=models.FileField(blank=True, null=True, upload_to='apk/', verbose_name='Archivo de al aplicacion'),
        ),
    ]
