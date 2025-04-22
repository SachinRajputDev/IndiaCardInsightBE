from django.contrib import admin

from .models import (
    Bank, CardFilter, CreditCard, FeeWaiver, RewardPointConversion, DefaultCashback,
    CashbackRule, RewardMultiplier, WelcomeBenefit, MilestoneBonus,
    CardBenefit, FeesAndCharges, EligibilityCriteria, Tag, CardTag,
    PromotionalBanner, Highlight
)

admin.site.register(CreditCard)
admin.site.register(FeeWaiver)
admin.site.register(RewardPointConversion)
admin.site.register(DefaultCashback)
admin.site.register(CashbackRule)
admin.site.register(RewardMultiplier)
admin.site.register(WelcomeBenefit)
admin.site.register(MilestoneBonus)
admin.site.register(CardBenefit)
admin.site.register(FeesAndCharges)
admin.site.register(EligibilityCriteria)
admin.site.register(Tag)
admin.site.register(CardTag)
admin.site.register(PromotionalBanner)
admin.site.register(Bank)
admin.site.register(CardFilter)
admin.site.register(Highlight)
