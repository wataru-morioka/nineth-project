# Generated by Django 2.2.3 on 2019-09-29 09:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('serviceApp', '0008_article_comment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='article_id',
            new_name='article',
        ),
    ]