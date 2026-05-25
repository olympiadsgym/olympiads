# Generated migration for session_end_time field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancelog',
            name='session_end_time',
            field=models.TimeField(blank=True, help_text='Time when this session expires (default: 2 hours after check-in)', null=True),
        ),
    ]
