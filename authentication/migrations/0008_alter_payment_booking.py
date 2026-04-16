# Generated migration for Payment model - OneToOneField to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_alter_customuser_role_roomhousekeepinglog_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='booking',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='authentication.booking'),
        ),
    ]
