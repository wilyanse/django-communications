# Generated by Django 5.0 on 2024-09-19 18:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ChitChat', '0006_remove_callpreference_user_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='callpreference',
            name='phone_number',
        ),
    ]
