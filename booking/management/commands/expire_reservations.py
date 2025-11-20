from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from scheduler.models import DailySlot
from booking.models import RESERVATION_MINUTES


class Command(BaseCommand):
    help = "Expire reserved slots not confirmed within RESERVATION_MINUTES"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=RESERVATION_MINUTES)
        # Make sure your DailySlot has reserved_at and STATUS_RESERVED constants; adjust if necessary.
        expired = DailySlot.objects.filter(status=getattr(DailySlot, "STATUS_RESERVED", "reserved"))
        # if reserved_at present:
        if hasattr(DailySlot, "reserved_at"):
            expired = expired.filter(reserved_at__lt=cutoff)
        count = expired.count()
        # free them
        for s in expired:
            s.status = getattr(DailySlot, "STATUS_AVAILABLE", "available")
            if hasattr(s, "reserved_by"):
                s.reserved_by = None
            if hasattr(s, "reserved_at"):
                s.reserved_at = None
            s.save()
        self.stdout.write(self.style.SUCCESS(f"Expired {count} slots"))
