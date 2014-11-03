from batch.start import batch_start
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):

    def handle(self, *args, **options):
        batch_start()
