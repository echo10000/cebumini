# Generated migration for MessageReply model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_contactmessage_testimonial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageReply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reply_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contact_message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='authentication.contactmessage')),
                ('staff_member', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_replies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Message Reply',
                'verbose_name_plural': 'Message Replies',
                'db_table': 'message_replies',
                'ordering': ['created_at'],
            },
        ),
    ]
