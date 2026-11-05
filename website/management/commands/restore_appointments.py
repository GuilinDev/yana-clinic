import sqlite3
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ..commands.backup_db import BACKUP_SUFFIX
from ...models import Appointment


class Command(BaseCommand):
    help = (
        'Re-insert appointments that exist in a SQLite backup but are missing from the live '
        'database (matched by id), e.g. after an accidental delete. Existing rows are never changed. '
        'Output names only ids and dates, never patient details.'
    )

    def add_arguments(self, parser):
        parser.add_argument('backup', help='Path to a backup .sqlite3 file')
        parser.add_argument('--ids', help='Comma-separated appointment ids to restore (default: every missing row)')
        parser.add_argument('--dry-run', action='store_true', help='Only list what would be restored')

    def handle(self, *args, **options):
        path = Path(options['backup'])
        if not path.is_file() or path.suffix != BACKUP_SUFFIX:
            raise CommandError(f'{path} is not a backup file')
        wanted = None
        if options['ids']:
            try:
                wanted = {int(part) for part in options['ids'].split(',') if part.strip()}
            except ValueError:
                raise CommandError('--ids must be a comma-separated list of numbers')

        source = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        source.row_factory = sqlite3.Row
        try:
            columns = {row[1] for row in source.execute('pragma table_info(website_appointment)')}
            if not columns:
                raise CommandError('The backup has no appointment table')
            rows = source.execute('select * from website_appointment order by id').fetchall()
        finally:
            source.close()

        existing = set(Appointment.objects.values_list('id', flat=True))
        missing = [row for row in rows if row['id'] not in existing and (wanted is None or row['id'] in wanted)]
        self.stdout.write(f'Backup holds {len(rows)} appointment(s); live database holds {len(existing)}; '
                          f'{len(missing)} missing from live' + (' (filtered by --ids)' if wanted else ''))

        restored = []
        for row in missing:
            appointment = self._build(row, columns)
            self.stdout.write(f'  id {appointment.id}: {appointment.date} {appointment.time:%H:%M} '
                              f'{appointment.get_location_display()} [{appointment.status}]')
            restored.append(appointment)

        if options['dry_run'] or not restored:
            self.stdout.write('Dry run, nothing written' if options['dry_run'] else 'Nothing to restore')
            return

        with transaction.atomic():
            for appointment in restored:
                original_created = appointment.created_at
                appointment.save(force_insert=True)  # auto_now_add stamps created_at...
                if original_created:                  # ...so put the original back
                    Appointment.objects.filter(pk=appointment.pk).update(created_at=original_created)
        self.stdout.write(f'Restored {len(restored)} appointment(s)')

    @staticmethod
    def _build(row, columns):
        def get(column, default=''):
            value = row[column] if column in columns else None
            return default if value is None else value

        created = get('created_at', None)
        if created:
            created = datetime.fromisoformat(created)
            if created.tzinfo is None:  # Django stores UTC without an offset in SQLite
                created = created.replace(tzinfo=dt_timezone.utc)
        return Appointment(
            id=row['id'],
            name=get('name'),
            phone=get('phone'),
            email=get('email'),
            service=get('service', 'Not specified'),
            date=datetime.fromisoformat(row['date']).date(),
            time=datetime.strptime(row['time'][:8], '%H:%M:%S').time(),
            location=get('location', 'wilmington'),
            message=get('message'),
            status=get('status', Appointment.STATUS_PENDING),
            notes=get('notes'),
            created_at=created,
        )
