# Generated by Django 5.0.4 on 2024-05-02 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0004_configcliente_guid_lote_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='versionapp',
            name='fpk_file',
            field=models.FileField(blank=True, null=True, upload_to='', verbose_name='Archivo de al aplicacion'),
        ),
    ]
