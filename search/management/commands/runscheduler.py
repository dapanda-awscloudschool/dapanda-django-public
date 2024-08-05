""" from django.core.management.base import BaseCommand
from search.tasks import scheduler

class Command(BaseCommand):
    help = 'Starts the scheduler'

    def handle(self, *args, **kwargs):
        scheduler.start()
        self.stdout.write(self.style.SUCCESS('Scheduler started successfully'))
 """