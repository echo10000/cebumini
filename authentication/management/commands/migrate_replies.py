"""
Management command to migrate MessageReply records to staff_response field.
This fixes the issue where guests couldn't see staff replies.
"""

from django.core.management.base import BaseCommand
from authentication.models import ContactMessage, MessageReply
from django.utils import timezone


class Command(BaseCommand):
    help = 'Migrate MessageReply records to staff_response field for guest visibility'

    def handle(self, *args, **options):
        # Find all messages with MessageReply records
        messages_with_replies = ContactMessage.objects.filter(
            replies__isnull=False
        ).distinct()

        migrated_count = 0
        skipped_count = 0

        for message in messages_with_replies:
            replies = MessageReply.objects.filter(
                contact_message=message
            ).order_by('created_at')

            if not replies.exists():
                continue

            # Skip if staff_response already has content
            if message.staff_response and '[Staff Reply' in message.staff_response:
                skipped_count += 1
                continue

            # Build response from all replies
            response_parts = []
            for reply in replies:
                staff_name = reply.staff_member.get_full_name() or reply.staff_member.username if reply.staff_member else 'System'
                timestamp = reply.created_at.strftime('%B %d, %Y at %I:%M %p')
                response_text = f"[Staff Reply - {staff_name} on {timestamp}]\n\n{reply.reply_text}"
                response_parts.append(response_text)

            combined_response = "\n\n---\n\n".join(response_parts)

            # Update the message
            if message.staff_response:
                message.staff_response += f"\n\n---\n\n{combined_response}"
            else:
                message.staff_response = combined_response

            message.save()
            migrated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully migrated {migrated_count} messages. '
                f'Skipped {skipped_count} (already migrated).'
            )
        )
