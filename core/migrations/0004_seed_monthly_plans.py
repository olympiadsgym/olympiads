from django.db import migrations


def seed_plans(apps, schema_editor):
    MembershipPlan = apps.get_model('core', 'MembershipPlan')
    # Remove all old plans that are not monthly
    MembershipPlan.objects.exclude(
        plan_name__in=['Monthly', 'Student Monthly']
    ).delete()
    # Upsert monthly plans
    MembershipPlan.objects.update_or_create(
        plan_name='Monthly',
        defaults={'duration_days': 30, 'price': '600.00'},
    )
    MembershipPlan.objects.update_or_create(
        plan_name='Student Monthly',
        defaults={'duration_days': 30, 'price': '350.00'},
    )


def reverse_plans(apps, schema_editor):
    pass  # Non-destructive reverse


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_seed_monthly_plans'),
    ]

    operations = [
        migrations.RunPython(seed_plans, reverse_plans),
    ]