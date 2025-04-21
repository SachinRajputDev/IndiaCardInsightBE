import json
from django.core.management.base import BaseCommand
from cards.models import (
    Bank, CreditCard, FeeWaiver, RewardPointConversion, DefaultCashback,
    CashbackRule, RewardMultiplier, WelcomeBenefit, MilestoneBonus,
    CardBenefit, FeesAndCharges, EligibilityCriteria, Tag, CardTag
)

class Command(BaseCommand):
    help = 'Import credit card data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        with open(options['json_file'], 'r') as f:
            data = json.load(f)

        # Create or get HDFC Bank
        bank, _ = Bank.objects.get_or_create(
            name='HDFC Bank',
            defaults={
                'website': 'https://www.hdfcbank.com',
                'logo_url': None
            }
        )

        for card_data in data:
            try:
                # Create credit card
                # Handle waiver_on_spend which can be a dictionary
                waiver_on_spend = card_data.get('waiver_on_spend')
                if isinstance(waiver_on_spend, dict):
                    # Use renewal amount if available, otherwise first_year
                    waiver_on_spend = waiver_on_spend.get('renewal') or waiver_on_spend.get('first_year', 0)
                
                # Handle required fields
                annual_fee = card_data.get('annual_fee')
                if annual_fee is None:
                    annual_fee = 0
                
                effective_annual_fee = card_data.get('effective_annual_fee')
                if effective_annual_fee is None:
                    effective_annual_fee = annual_fee
                
                card = CreditCard.objects.create(
                    card_name=card_data['card_name'],
                    bank=bank,
                    card_type=card_data['card_type'],
                    variant=card_data.get('variant'),
                    network=card_data.get('network', []),
                    status=card_data.get('status', 1),
                    annual_fee=annual_fee,
                    waiver_on_spend=waiver_on_spend,
                    effective_annual_fee=effective_annual_fee,
                    image_url=card_data.get('image_url'),
                    apply_url=card_data.get('apply_url'),
                    summary=card_data.get('summary')
                )

                # Create reward point conversion if present
                rpc_data = card_data.get('reward_point_conversion')
                if rpc_data:
                    conversion_rate = rpc_data.get('conversion_rate')
                    # Handle both number and dictionary conversion rates
                    if not isinstance(conversion_rate, dict):
                        conversion_rate = {'Cashback': conversion_rate or 0}
                    
                    min_points_required = rpc_data.get('min_points_required')
                    if min_points_required is None:
                        min_points_required = 0
                    
                    conversion_description = rpc_data.get('conversion_description')
                    if conversion_description is None:
                        # Generate a default description based on conversion rate
                        if isinstance(conversion_rate, dict):
                            descriptions = []
                            for key, value in conversion_rate.items():
                                descriptions.append(f'1 Point = ₹{value} for {key}')
                            conversion_description = '; '.join(descriptions)
                        else:
                            conversion_description = f'1 Point = ₹{conversion_rate}'
                    
                    RewardPointConversion.objects.create(
                        card=card,
                        conversion_rate=conversion_rate,
                        min_points_required=min_points_required,
                        conversion_description=conversion_description
                    )

                # Create default cashback if present
                dc_data = card_data.get('default_cashback')
                if dc_data:
                    # Only create if cashback_percent has a value
                    cashback_percent = dc_data.get('cashback_percent')
                    if cashback_percent is not None:
                        DefaultCashback.objects.create(
                            card=card,
                            cashback_percent=cashback_percent,
                            monthly_cap=dc_data.get('monthly_cap'),
                            min_transaction_amount=dc_data.get('min_transaction_amount', 0)
                        )

                # Create cashback rules if present
                for rule_data in card_data.get('cashback_rules', []):
                    # Handle EazyDiner case where cashback is in additional_conditions
                    if rule_data.get('additional_conditions') and ('discount' in rule_data.get('additional_conditions', '').lower() or 'cashback' in rule_data.get('additional_conditions', '').lower()):
                        # Extract cashback percent from additional conditions
                        import re
                        match = re.search(r'(\d+)%', rule_data.get('additional_conditions', ''))
                        if match:
                            cashback_percent = float(match.group(1))
                        else:
                            continue
                    else:
                        # Skip rule if it has no cashback_percent or is 0
                        cashback_percent = rule_data.get('cashback_percent')
                        if cashback_percent is None or cashback_percent == 0:
                            continue
                    
                    # Handle platform field which can be list or string
                    platform = rule_data.get('platform')
                    if isinstance(platform, list):
                        platform = platform[0] if platform else None
                    
                    # Handle payment_app field which can be list or string
                    payment_app = rule_data.get('payment_app')
                    if isinstance(payment_app, list):
                        payment_app = payment_app[0] if payment_app else None
                    
                    # Handle platform_type field which can be list or string
                    platform_type = rule_data.get('platform_type')
                    if isinstance(platform_type, list):
                        platform_type = platform_type[0] if platform_type else None
                    
                    # Handle min_transaction_amount
                    min_transaction_amount = rule_data.get('min_transaction_amount')
                    if min_transaction_amount is None:
                        # If not specified, use default from default_cashback if available
                        dc_data = card_data.get('default_cashback', {})
                        min_transaction_amount = dc_data.get('min_transaction_amount', 0)
                    
                    # Handle monthly_cap
                    monthly_cap = rule_data.get('monthly_cap')
                    if monthly_cap is None:
                        monthly_cap = 0
                    
                    # Handle max_cashback_per_transaction
                    max_cashback_per_transaction = rule_data.get('max_cashback_per_transaction')
                    if max_cashback_per_transaction is None:
                        max_cashback_per_transaction = monthly_cap
                    
                    # Skip if no valid cashback percent
                    if not cashback_percent or cashback_percent <= 0:
                        continue
                        
                    CashbackRule.objects.create(
                        card=card,
                        category=rule_data.get('category'),
                        subcategory=rule_data.get('subcategory'),
                        platform=platform,
                        brand=rule_data.get('brand'),
                        spending_type=rule_data.get('spending_type'),
                        platform_type=platform_type,
                        payment_app=payment_app,
                        cashback_percent=cashback_percent,
                        monthly_cap=monthly_cap,
                        min_transaction_amount=min_transaction_amount,
                        max_cashback_per_transaction=max_cashback_per_transaction,
                        additional_conditions=rule_data.get('additional_conditions')
                    )

                # Create tags if present
                for tag_name in card_data.get('tags', []):
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    CardTag.objects.create(card=card, tag=tag)

                self.stdout.write(self.style.SUCCESS(f'Successfully imported {card.card_name}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing card {card_data["card_name"]}: {str(e)}'))
