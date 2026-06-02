from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_encrypt_member_pii'),
    ]

    operations = [
        migrations.RemoveField(model_name='member', name='contact'),
        migrations.RemoveField(model_name='member', name='contact_hash'),
    ]