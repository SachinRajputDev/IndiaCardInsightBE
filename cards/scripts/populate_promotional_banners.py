# This script will create the three initial promotional banners for your app.
# Usage: python manage.py shell < backend/cards/scripts/populate_promotional_banners.py

from cards.models import PromotionalBanner, CreditCard
from django.core.exceptions import ObjectDoesNotExist

banners_to_create = [
    {
        "title": "New Launch: Premium Rewards Gold",
        "color": "bg-gradient-to-r from-amber-50 to-yellow-100",
        "icon": "star",
        "order": 0,
        "card_name": "Premium Rewards Gold",
        "link_url": "/cards?category=new"
    },
    {
        "title": "High Approval Rate: Everyday Rewards",
        "color": "bg-gradient-to-r from-green-50 to-emerald-100",
        "icon": "thumbs_up",
        "order": 1,
        "card_name": "Everyday Rewards",
        "link_url": "/cards?category=high-approval"
    },
    {
        "title": "Limited Time Offer: ShopMore Platinum",
        "color": "bg-gradient-to-r from-blue-50 to-indigo-100",
        "icon": "clock",
        "order": 2,
        "card_name": "ShopMore Platinum",
        "link_url": "/cards?category=limited-offer"
    },
]

for banner in banners_to_create:
    try:
        card = CreditCard.objects.get(card_name=banner["card_name"])
    except ObjectDoesNotExist:
        print(f"[ERROR] Card not found: {banner['card_name']}. Skipping banner '{banner['title']}'.")
        continue
    obj, created = PromotionalBanner.objects.get_or_create(
        title=banner["title"],
        defaults={
            "color": banner["color"],
            "icon": banner["icon"],
            "order": banner["order"],
            "card": card,
            "link_url": banner["link_url"],
        }
    )
    if created:
        print(f"[OK] Created banner: {banner['title']}")
    else:
        print(f"[SKIP] Banner already exists: {banner['title']}")
