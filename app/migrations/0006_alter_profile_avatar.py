# Generated by Django 4.2.11 on 2024-04-22 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_rename_question_id_answer_question'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(blank=True, default='Cat03.jpg', null=True, upload_to='avatar/%Y/%m/%d'),
        ),
    ]
