import json
from django.core.management.base import BaseCommand
from cards.models import CreditCard, Highlight

class Command(BaseCommand):
    help = 'Import highlights from JSON file containing card_name and key_highlights'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to JSON file with highlights')

    def handle(self, *args, **options):
        file_path = options['file_path']
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error reading file: {e}'))
            return
        for entry in data:
            card_name = entry.get('card_name')
            bank_name = entry.get('bank')
            if not card_name:
                self.stdout.write(self.style.WARNING('Skipping entry without card_name'))
                continue
            # Filter by card_name and optional bank name to disambiguate
            qs = CreditCard.objects.filter(card_name=card_name)
            if bank_name:
                qs = qs.filter(bank__name=bank_name)
            count = qs.count()
            if count == 1:
                card = qs.first()
            elif count == 0:
                self.stdout.write(self.style.WARNING(f'Card not found: {card_name} ({bank_name})'))
                continue
            else:
                self.stdout.write(self.style.WARNING(f'Multiple cards found for {card_name} ({bank_name}), skipping'))
                continue
            highlights = entry.get('key_highlights', [])
            obj, created = Highlight.objects.update_or_create(
                card=card,
                defaults={'highlight': highlights}
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(f'{action} highlight for {card_name}')
        self.stdout.write(self.style.SUCCESS('Import complete.'))
