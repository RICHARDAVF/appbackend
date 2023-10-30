# Generated by Django 4.2.1 on 2023-10-26 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0009_delete_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='VersionApp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, verbose_name='Nombre de la version')),
                ('version', models.CharField(max_length=50, verbose_name='Version de la applicacion')),
                ('fecha', models.DateField(verbose_name='Fecha de la ultima actualizacion')),
            ],
            options={
                'verbose_name': 'version',
                'verbose_name_plural': 'Versiones',
                'db_table': 'versiones',
            },
        ),
    ]
