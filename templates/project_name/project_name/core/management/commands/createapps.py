import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Create multiple Django apps'

    def add_arguments(self, parser):
        parser.add_argument('app_names', nargs='+', type=str, help='List of app names to create')

    def handle(self, *args, **options):
        apps_root = settings.APPS_DIR
        os.makedirs(apps_root, exist_ok=True)

        for app_name in options['app_names']:
            app_path = os.path.join(apps_root, app_name)

            if os.path.exists(app_path):
                self.stdout.write(self.style.WARNING(f"App '{app_name}' already exists"))
            else:
                os.makedirs(app_path, exist_ok=True)
                call_command('startapp', app_name, app_path)
                self.stdout.write(self.style.SUCCESS(f"App '{app_name}' created at {app_path}"))
