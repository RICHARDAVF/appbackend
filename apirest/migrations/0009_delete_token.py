# Generated by Django 4.2.1 on 2023-09-27 14:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apirest', '0008_token_delete_tokenlog'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Token',
        ),
    ]