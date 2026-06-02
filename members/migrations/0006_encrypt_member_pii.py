"""
Encrypt Member email and contact fields.
IMPORTANT: Set FIELD_ENCRYPTION_KEY in .env before running this migration.
"""

from django.db import migrations, models


def encrypt_existing_rows(apps, schema_editor):
    from members.encryption import encrypt, make_lookup_hash
    Member = apps.get_model('members', 'Member')
    for m in Member.objects.all():
        plaintext_email = m.email_plain or ''
        plaintext_contact = m.contact_plain or ''
        m.email = encrypt(plaintext_email) if plaintext_email else ''
        m.contact = encrypt(plaintext_contact) if plaintext_contact else ''
        m.email_hash = make_lookup_hash(plaintext_email)
        m.contact_hash = make_lookup_hash(plaintext_contact)
        m.save(update_fields=['email', 'contact', 'email_hash', 'contact_hash'])


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_merge_20260529_1513'),
    ]

    operations = [
        # 1. Rename old plaintext columns to temp names for data migration
        migrations.RenameField(model_name='member', old_name='email', new_name='email_plain'),
        migrations.RenameField(model_name='member', old_name='contact', new_name='contact_plain'),

        # 2. Add new encrypted ciphertext columns
        migrations.AddField(
            model_name='member',
            name='email',
            field=models.TextField(db_column='email_enc', null=True, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='member',
            name='contact',
            field=models.TextField(db_column='contact_enc', null=True, blank=True, default=''),
        ),

        # 3. Add hash lookup columns
        migrations.AddField(
            model_name='member',
            name='email_hash',
            field=models.CharField(max_length=64, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='member',
            name='contact_hash',
            field=models.CharField(max_length=64, blank=True, default=''),
        ),

        # 4. Encrypt all existing rows
        migrations.RunPython(encrypt_existing_rows, migrations.RunPython.noop),

        # 5. Drop the old plaintext columns
        migrations.RemoveField(model_name='member', name='email_plain'),
        migrations.RemoveField(model_name='member', name='contact_plain'),

        # 6. Make email_hash unique (replaces the old unique constraint on email)
        migrations.AlterField(
            model_name='member',
            name='email_hash',
            field=models.CharField(max_length=64, unique=True, blank=True, default=''),
        ),
    ]