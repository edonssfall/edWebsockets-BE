# Generated by Django 5.0.4 on 2024-05-10 12:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_remove_user_is_anonymous_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='name',
        ),
    ]