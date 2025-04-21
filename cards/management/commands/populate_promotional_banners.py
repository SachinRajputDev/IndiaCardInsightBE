from django.core.management.base import BaseCommand
from cards.models import PromotionalBanner, CreditCard
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = 'Populates the database with initial promotional banners for cards.'

    def handle(self, *args, **options):
        banners_to_create = [
    {
        "title": "High Approval Rate",
        "color": "bg-gradient-to-r from-green-50 to-emerald-100",
        "icon": "thumbs_up",
        "order": 0,
        "link_url": "/cards?category=high-approval",
        "description": "Discover cards with the highest approval rates. Get approved faster!"
    },
    {
        "title": "New Launch",
        "color": "bg-gradient-to-r from-amber-50 to-yellow-100",
        "icon": "star",
        "order": 1,
        "link_url": "/cards?category=new-launch",
        "description": "Check out the latest credit cards just launched. Don’t miss out!"
    },
    {
        "title": "Limited Time Offer",
        "color": "bg-gradient-to-r from-blue-50 to-indigo-100",
        "icon": "clock",
        "order": 2,
        "link_url": "/cards?category=high-approval",
        "description": "Grab these exclusive limited time offers before they’re gone!"
    },
]

        for banner in banners_to_create:
            obj, created = PromotionalBanner.objects.get_or_create(
                title=banner["title"],
                defaults={
                    "color": banner["color"],
                    "icon": banner["icon"],
                    "order": banner["order"],
                    "card": None,
                    "link_url": banner["link_url"],
                    "description": banner["description"],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"[OK] Created banner: {banner['title']}"))
            else:
                # Update all fields if the banner already exists
                obj.color = banner["color"]
                obj.icon = banner["icon"]
                obj.order = banner["order"]
                obj.card = None
                obj.link_url = banner["link_url"]
                obj.description = banner["description"]
                obj.save()
                self.stdout.write(self.style.SUCCESS(f"[UPDATED] Banner updated: {banner['title']}"))
