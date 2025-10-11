from django.db import migrations

def fix_points_distribution(apps, schema_editor):
    Activity = apps.get_model('leaderboard', 'Activity')
    
    for activity in Activity.objects.all():
        needs_save = False
        
        # Ensure points_distribution exists
        if not activity.points_distribution:
            activity.points_distribution = {}
            needs_save = True
        
        # Ensure all placements 1-5 exist
        default_distribution = {
            1: activity.max_points,
            2: int(activity.max_points * 0.8),
            3: int(activity.max_points * 0.6),
            4: int(activity.max_points * 0.4),
            5: int(activity.max_points * 0.2)
        }
        
        for placement in range(1, 6):
            if placement not in activity.points_distribution:
                activity.points_distribution[placement] = default_distribution[placement]
                needs_save = True
        
        if needs_save:
            activity.save()

def reverse_fix(apps, schema_editor):
    pass  # No need to reverse

class Migration(migrations.Migration):

    dependencies = [
        ('leaderboard', '0005_auto_20251011_1028'),
    ]

    operations = [
        migrations.RunPython(fix_points_distribution, reverse_fix),
    ]
