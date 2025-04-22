from django.db import models
from django.core.validators import MinValueValidator


class Bank(models.Model):
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(null=True, blank=True)
    logo_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class CardFilter(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CreditCard(models.Model):
    STATUS_CHOICES = [
        (0, 'Discontinued'),
        (1, 'Active'),
        (2, 'Coming Soon'),
    ]

    card_name = models.CharField(max_length=255)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=50, default='Credit Card')
    variant = models.CharField(max_length=50, null=True, blank=True)  # Platinum, Signature etc.
    network = models.JSONField(default=list)  # Visa, Mastercard, RuPay, etc.
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    filters = models.ManyToManyField(CardFilter, related_name='cards')
    
    annual_fee = models.PositiveIntegerField(default=0)
    waiver_on_spend = models.PositiveIntegerField(null=True, blank=True)
    effective_annual_fee = models.PositiveIntegerField(default=0)

    image_url = models.URLField(null=True, blank=True)

    promotional_card = models.BooleanField(default=False, help_text="Show this card in the homepage banner")
    promotional_order = models.PositiveIntegerField(default=0, help_text="Order of appearance in the banner (lower = first)")
    apply_url = models.URLField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.bank.name} {self.card_name}"


class FeeWaiver(models.Model):
    card = models.OneToOneField(CreditCard, on_delete=models.CASCADE, related_name='fee_waiver')
    annual_fee = models.PositiveIntegerField()
    waiver_on_annual_spend = models.PositiveIntegerField()
    waiver_description = models.TextField(null=True, blank=True)


class RewardPointConversion(models.Model):
    card = models.OneToOneField(CreditCard, on_delete=models.CASCADE, related_name='reward_point_conversion')
    conversion_rate = models.JSONField()  # {"Cashback": 0.15, "SmartBuy": 0.3, ...}
    min_points_required = models.PositiveIntegerField()
    conversion_description = models.TextField()


class DefaultCashback(models.Model):
    card = models.OneToOneField(CreditCard, on_delete=models.CASCADE, related_name='default_cashback')
    cashback_percent = models.FloatField()
    monthly_cap = models.PositiveIntegerField(null=True, blank=True)
    min_transaction_amount = models.PositiveIntegerField()


class CashbackRule(models.Model):
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='cashback_rules')
    category = models.CharField(max_length=255, null=True, blank=True)
    subcategory = models.CharField(max_length=255, null=True, blank=True)
    platform = models.CharField(max_length=255, null=True, blank=True)
    brand = models.JSONField(null=True, blank=True)
    spending_type = models.CharField(max_length=50, null=True, blank=True)  # Online, Offline
    platform_type = models.JSONField(null=True, blank=True)  # App, Website, Store
    payment_app = models.JSONField(null=True, blank=True)
    cashback_percent = models.FloatField(null=True, blank=True)
    monthly_cap = models.PositiveIntegerField(null=True, blank=True)
    min_transaction_amount = models.PositiveIntegerField(null=True, blank=True, default=0)
    max_cashback_per_transaction = models.PositiveIntegerField(null=True, blank=True)
    additional_conditions = models.TextField(null=True, blank=True)


class RewardMultiplier(models.Model):
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='reward_multipliers')
    category = models.CharField(max_length=255)
    multiplier = models.FloatField()
    monthly_cap = models.PositiveIntegerField(null=True, blank=True)
    min_transaction_amount = models.PositiveIntegerField(null=True, blank=True)
    conditions = models.JSONField(null=True, blank=True)


class WelcomeBenefit(models.Model):
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='welcome_benefits')
    benefit_type = models.CharField(max_length=50)
    description = models.TextField()
    value = models.CharField(max_length=255)
    spend_requirement = models.PositiveIntegerField(null=True, blank=True)
    validity_days = models.PositiveIntegerField(null=True, blank=True)
    conditions = models.JSONField(null=True, blank=True)


class MilestoneBonus(models.Model):
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='milestone_bonuses')
    spend_threshold = models.PositiveIntegerField()
    bonus_type = models.CharField(max_length=50)
    bonus_value = models.IntegerField()
    validity_period = models.CharField(max_length=50, null=True, blank=True)
    conditions = models.JSONField(null=True, blank=True)


class CardBenefit(models.Model):
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='card_benefits')
    benefit_type = models.CharField(max_length=50)
    description = models.TextField()
    value = models.CharField(max_length=255, null=True, blank=True)
    frequency = models.CharField(max_length=50, null=True, blank=True)
    conditions = models.JSONField(null=True, blank=True)


class FeesAndCharges(models.Model):
    card = models.OneToOneField(CreditCard, on_delete=models.CASCADE, related_name='fees_and_charges')
    joining_fee = models.PositiveIntegerField(null=True, blank=True)
    joining_fee_waiver = models.TextField(null=True, blank=True)
    interest_rate = models.FloatField(null=True, blank=True)
    cash_advance_fee = models.CharField(max_length=255, null=True, blank=True)
    late_payment_fee = models.JSONField(null=True, blank=True)
    overlimit_fee = models.PositiveIntegerField(null=True, blank=True)
    foreign_transaction_fee = models.FloatField(null=True, blank=True)


class EligibilityCriteria(models.Model):
    card = models.OneToOneField(CreditCard, on_delete=models.CASCADE, related_name='eligibility_criteria')
    min_income = models.PositiveIntegerField(null=True, blank=True)
    min_age = models.PositiveIntegerField(null=True, blank=True)
    max_age = models.PositiveIntegerField(null=True, blank=True)
    employment_type = models.JSONField(null=True, blank=True)  # ["Salaried", "Self-Employed"]
    credit_score = models.PositiveIntegerField(null=True, blank=True)
    additional_requirements = models.JSONField(null=True, blank=True)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)


class CardTag(models.Model):
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class PromotionalBanner(models.Model):
    title = models.CharField(max_length=100)
    color = models.CharField(max_length=50, help_text="Tailwind or CSS class for color")
    icon = models.CharField(max_length=50, null=True, blank=True, help_text="Icon name for frontend")
    order = models.PositiveIntegerField(default=0)
    card = models.ForeignKey('CreditCard', on_delete=models.CASCADE, related_name='banners', null=True, blank=True)
    link_url = models.CharField(max_length=255, null=True, blank=True, help_text="URL to navigate when clicking the banner")
    description = models.TextField(null=True, blank=True, help_text="Short description for the banner")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Highlight(models.Model):
    # One-to-one highlight data for a credit card
    card = models.OneToOneField(CreditCard, on_delete=models.CASCADE, related_name='highlight')
    highlight = models.JSONField(help_text="Structured highlight data for the card")

    def __str__(self):
        return f"Highlight for {self.card}"