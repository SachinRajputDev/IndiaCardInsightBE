from rest_framework import serializers
from .models import (
    CreditCard, FeeWaiver, RewardPointConversion, DefaultCashback,
    CashbackRule, RewardMultiplier, WelcomeBenefit, MilestoneBonus,
    CardBenefit, FeesAndCharges, EligibilityCriteria, PromotionalBanner,
    Bank, Highlight
)

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['id', 'name', 'website', 'logo_url']

class FeeWaiverSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeWaiver
        exclude = ('card',)

class RewardPointConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardPointConversion
        exclude = ('card',)

class DefaultCashbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefaultCashback
        exclude = ('card',)

class CashbackRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashbackRule
        exclude = ('card',)

class RewardMultiplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardMultiplier
        exclude = ('card',)

class WelcomeBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = WelcomeBenefit
        exclude = ('card',)

class MilestoneBonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilestoneBonus
        exclude = ('card',)

class CardBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardBenefit
        exclude = ('card',)

class FeesAndChargesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeesAndCharges
        exclude = ('card',)

class EligibilityCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EligibilityCriteria
        exclude = ('card',)

class HighlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highlight
        fields = ['highlight']

class CreditCardSerializer(serializers.ModelSerializer):
    bank = BankSerializer(read_only=True)
    bank_id = serializers.PrimaryKeyRelatedField(queryset=Bank.objects.all(), source='bank', write_only=True)
    # Expose flat list of highlights instead of nested dict
    highlight = serializers.JSONField(source='highlight.highlight', read_only=True)
    # CamelCase mapping for frontend
    annualFee = serializers.IntegerField(source='annual_fee', read_only=True)
    # Expose frontend-friendly fields
    name = serializers.CharField(source='card_name', read_only=True)
    issuer = serializers.CharField(source='bank.name', read_only=True)
    fee_waiver = FeeWaiverSerializer(read_only=True)
    reward_point_conversion = RewardPointConversionSerializer(read_only=True)
    default_cashback = DefaultCashbackSerializer(read_only=True)
    cashback_rules = CashbackRuleSerializer(many=True, read_only=True)
    reward_multipliers = RewardMultiplierSerializer(many=True, read_only=True)
    welcome_benefits = WelcomeBenefitSerializer(many=True, read_only=True)
    milestone_bonuses = MilestoneBonusSerializer(many=True, read_only=True)
    card_benefits = CardBenefitSerializer(many=True, read_only=True)
    fees_and_charges = FeesAndChargesSerializer(read_only=True)
    eligibility_criteria = EligibilityCriteriaSerializer(read_only=True)

    class Meta:
        model = CreditCard
        fields = '__all__'

class PromotionalBannerSerializer(serializers.ModelSerializer):
    card = CreditCardSerializer(read_only=True)
    class Meta:
        model = PromotionalBanner
        fields = ['id', 'title', 'color', 'icon', 'order', 'card', 'link_url', 'description']

class CardRecommendationSerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
    card_name = serializers.CharField()
    bank = serializers.CharField()
    cashback = serializers.FloatField()
    annual_fee = serializers.FloatField()
    net_benefit = serializers.FloatField()

class SpendingSerializer(serializers.Serializer):
    type_of_spending = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=False, allow_blank=True)
    app_name = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False, allow_blank=True)
    subcategory = serializers.CharField(required=False, allow_blank=True)
    brand = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.FloatField(required=True)
    frequency = serializers.CharField(required=False, allow_blank=True)
    payment_app = serializers.CharField(required=False, allow_blank=True)
    purpose = serializers.CharField(required=False, allow_blank=True)

class PreferencesSerializer(serializers.Serializer):
    cards_to_compare = serializers.ListField(child=serializers.CharField(), required=False)
    cards_to_exclude = serializers.ListField(child=serializers.CharField(), required=False)
    cards_you_own = serializers.ListField(child=serializers.CharField(), required=False)
    num_new_cards = serializers.IntegerField(required=False)
    # Desired number of cards per group from frontend
    desiredCardCount = serializers.IntegerField(required=False)

class CardRecommendationInputSerializer(serializers.Serializer):
    spending = serializers.ListField(child=SpendingSerializer(), required=True)
    preferences = PreferencesSerializer(required=False)

class PurchaseAdvisorInputSerializer(serializers.Serializer):
    amount = serializers.FloatField(required=True)
    category = serializers.CharField(required=True)
    platform = serializers.CharField(required=False, allow_blank=True)
    platform_name = serializers.CharField(required=False, allow_blank=True)
    specific_category = serializers.CharField(required=False, allow_blank=True)
    brand = serializers.CharField(required=False, allow_blank=True)
    owned_cards = serializers.ListField(child=serializers.IntegerField(), required=True)