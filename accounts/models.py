from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from cards.models import CreditCard, Bank


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    credit_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class UserCreditCard(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('applied', 'Applied'),
        ('rejected', 'Rejected')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_cards')
    credit_card = models.ForeignKey(CreditCard, on_delete=models.CASCADE)
    card_number_last4 = models.CharField(max_length=4, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    joining_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    annual_fee_waived = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.credit_card.card_name}"

    class Meta:
        unique_together = ['user', 'credit_card', 'card_number_last4']


class UserPreferences(models.Model):
    SPEND_CATEGORY_CHOICES = [
        ('travel', 'Travel'),
        ('shopping', 'Shopping'),
        ('dining', 'Dining'),
        ('entertainment', 'Entertainment'),
        ('fuel', 'Fuel'),
        ('utilities', 'Utilities'),
        ('groceries', 'Groceries'),
        ('others', 'Others')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    preferred_banks = models.ManyToManyField(Bank, blank=True)
    preferred_card_types = models.JSONField(default=list, blank=True)
    monthly_spend = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    primary_spend_categories = models.JSONField(default=list, blank=True)
    max_annual_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Preferences"


class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('card_added', 'Credit Card Added'),
        ('card_updated', 'Credit Card Updated'),
        ('card_removed', 'Credit Card Removed'),
        ('profile_updated', 'Profile Updated'),
        ('preferences_updated', 'Preferences Updated'),
        ('card_application', 'Card Application'),
        ('reward_redeemed', 'Reward Redeemed')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    credit_card = models.ForeignKey(CreditCard, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.activity_type} on {self.created_at}"

    class Meta:
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']


@receiver(post_save, sender=User)
def create_user_profile_and_preferences(sender, instance, created, **kwargs):
    """Create UserProfile and UserPreferences when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)
        UserPreferences.objects.create(user=instance)

