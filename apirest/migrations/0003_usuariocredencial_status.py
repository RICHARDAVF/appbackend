# Generated by Django 4.2.1 on 2023-05-15 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0002_remove_usuariocredencial_empresa_razon_social_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuariocredencial',
            name='status',
            field=models.BooleanField(default=False, verbose_name='Estado'),
        ),
    ]
