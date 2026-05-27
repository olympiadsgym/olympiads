from django.db import migrations


def seed_plans(apps, schema_editor):
    MembershipPlan = apps.get_model('core', 'MembershipPlan')
    MembershipPlan.objects.all().delete()
    plans = [
        {'plan_name': 'Monthly',         'duration_days': 30, 'price': '500.00'},
        {'plan_name': 'Student Monthly', 'duration_days': 30, 'price': '350.00'},
    ]
    for p in plans:
        MembershipPlan.objects.create(**p)


def reverse_plans(apps, schema_editor):
    MembershipPlan = apps.get_model('core', 'MembershipPlan')
    MembershipPlan.objects.filter(
        plan_name__in=['Monthly', 'Student Monthly']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(seed_plans, reverse_plans),
    ]