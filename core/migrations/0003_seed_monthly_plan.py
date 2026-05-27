from django.db import migrations


def seed_plans(apps, schema_editor):
    MembershipPlan = apps.get_model('core', 'MembershipPlan')
    MembershipPlan.objects.update_or_create(
        plan_name='Monthly',
        defaults={'duration_days': 30, 'price': '600.00'},
    )
    MembershipPlan.objects.exclude(plan_name='Monthly').delete()


def reverse_plans(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(seed_plans, reverse_plans),
    ]