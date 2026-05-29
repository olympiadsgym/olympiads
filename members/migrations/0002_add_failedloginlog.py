from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0003_add_session_end_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]