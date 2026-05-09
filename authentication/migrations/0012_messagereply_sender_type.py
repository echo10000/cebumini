from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_alter_booking_status_alter_payment_status_emailotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagereply',
            name='sender_type',
            field=models.CharField(
                choices=[
                    ('guest', 'Guest'),
                    ('staff', 'Staff'),
                    ('system', 'System'),
                ],
                db_index=True,
                default='staff',
                max_length=10,
            ),
        ),
    ]
