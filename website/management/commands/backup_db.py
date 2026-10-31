import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

BACKUP_PREFIX = 'db-'
BACKUP_SUFFIX = '.sqlite3'


class Command(BaseCommand):
    help = (
        'Copy the SQLite database to a dated file in the backup directory using the '
        'SQLite online backup API, then delete all but the newest --keep backups.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--dest', required=True, help='Directory to write backups into')
        parser.add_argument('--keep', type=int, default=14, help='Number of backups to keep (default 14)')

    def handle(self, *args, **options):
        if connection.vendor != 'sqlite':
            raise CommandError('backup_db only supports SQLite databases')
        if options['keep'] < 1:
            raise CommandError('--keep must be at least 1')

        dest_dir = Path(options['dest'])
        dest_dir.mkdir(parents=True, exist_ok=True)
        stamp = timezone.localtime().strftime('%Y-%m-%d-%H%M%S')
        target = dest_dir / f'{BACKUP_PREFIX}{stamp}{BACKUP_SUFFIX}'

        # The backup API copies a consistent snapshot even while the site is writing
        connection.ensure_connection()
        backup = sqlite3.connect(str(target))
        try:
            connection.connection.backup(backup)
        finally:
            backup.close()

        backups = sorted(dest_dir.glob(f'{BACKUP_PREFIX}*{BACKUP_SUFFIX}'))
        for old in backups[:-options['keep']]:
            old.unlink()

        kept = min(len(backups), options['keep'])
        self.stdout.write(f'Backed up to {target} ({target.stat().st_size} bytes); {kept} backup(s) kept')
