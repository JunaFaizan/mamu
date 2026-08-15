from django.db import migrations

ROOMS = [
    ('101', 'Standard', 6000),
    ('102', 'Standard', 6000),
    ('103', 'Standard', 6500),
    ('104', 'Standard', 6500),
    ('201', 'Deluxe', 9500),
    ('202', 'Deluxe', 9500),
    ('203', 'Deluxe', 10000),
    ('204', 'Deluxe', 10000),
    ('301', 'Suite', 16000),
    ('302', 'Suite', 18000),
]


def seed_rooms(apps, schema_editor):
    Room = apps.get_model('main_app', 'Room')
    for number, room_type, rate in ROOMS:
        Room.objects.get_or_create(
            number=number,
            defaults={'type': room_type, 'rate': rate, 'status': 'available'},
        )


def unseed_rooms(apps, schema_editor):
    Room = apps.get_model('main_app', 'Room')
    Room.objects.filter(number__in=[number for number, _, _ in ROOMS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0002_room_booking'),
    ]

    operations = [
        migrations.RunPython(seed_rooms, unseed_rooms),
    ]
