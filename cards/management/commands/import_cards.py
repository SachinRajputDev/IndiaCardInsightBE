import json
from django.core.management.base import BaseCommand
from cards.models import (
    CreditCard, FeeWaiver, RewardPointConversion, DefaultCashback,
    CashbackRule, RewardMultiplier, WelcomeBenefit, MilestoneBonus,
    CardBenefit, FeesAndCharges, EligibilityCriteria
)

class Command(BaseCommand):
    help = 'Import credit cards data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        json_file = options['json_file']

        try:
            with open(json_file, 'r') as file:
                data = json.load(file)

            for card_data in data:
                # Create credit card
                # Handle required fields with defaults
                card_name = card_data.get('card_name', 'Unnamed Card')
                bank = card_data.get('bank', 'HDFC Bank')
                card_type = card_data.get('card_type', 'Credit Card')
                
                # Handle network field which can be string or list
                network = card_data.get('network')
                if network:
                    if isinstance(network, list):
                        network = network[0]  # Take the first network if multiple
                    elif '/' in network:
                        network = network.split('/')[0].strip()  # Take first network before slash
                else:
                    network = 'Unknown'  # Default value for null networks
                
                # Handle annual fee and effective annual fee
                annual_fee = card_data.get('annual_fee')
                if annual_fee is None:
                    annual_fee = 0  # Default to 0 if not present
                
                effective_annual_fee = card_data.get('effective_annual_fee')
                if effective_annual_fee is None:
                    # If effective annual fee is not specified, use annual fee
                    effective_annual_fee = annual_fee
                
                card = CreditCard.objects.create(
                    card_name=card_name,
                    bank=bank,
                    card_type=card_type,
                    network=network,
                    annual_fee=annual_fee,
                    waiver_on_spend=card_data.get('waiver_on_spend'),
                    effective_annual_fee=effective_annual_fee,
                    image_url=card_data.get('image_url'),
                    apply_url=card_data.get('apply_url'),
                    status=card_data.get('status', 'active')
                )

                # Create fee waiver
                if 'fee_waiver' in card_data:
                    waiver_data = card_data['fee_waiver']
                    FeeWaiver.objects.create(
                        card=card,
                        annual_fee=waiver_data['annual_fee'],
                        waiver_on_annual_spend=waiver_data['waiver_on_annual_spend'],
                        waiver_description=waiver_data.get('waiver_description', '')
                    )

                # Create reward point conversion
                if 'reward_point_conversion' in card_data:
                    conversion_data = card_data['reward_point_conversion']
                    # Handle conversion rate which can be a number or a dict
                    conversion_rate = conversion_data.get('conversion_rate')
                    if isinstance(conversion_rate, dict):
                        # If it's a dict, convert string values to float and use the highest value
                        try:
                            conversion_rate = max(float(v) for v in conversion_rate.values())
                        except (ValueError, TypeError):
                            # Skip if conversion fails
                            conversion_rate = None
                    elif conversion_rate is None:
                        # Skip if no conversion rate
                        pass
                    else:
                        try:
                            conversion_rate = float(conversion_rate)
                            RewardPointConversion.objects.create(
                                card=card,
                                conversion_rate=conversion_rate,
                                min_points_required=conversion_data.get('min_points_required'),
                                conversion_description=conversion_data.get('conversion_description')
                            )
                        except (ValueError, TypeError):
                            # Skip if conversion fails
                            pass

                # Create default cashback
                if 'default_cashback' in card_data:
                    cashback_data = card_data['default_cashback']
                    # Skip if any required field is null
                    if all(key in cashback_data and cashback_data[key] is not None 
                           for key in ['cashback_percent', 'monthly_cap', 'min_transaction_amount']):
                        DefaultCashback.objects.create(
                            card=card,
                            cashback_percent=cashback_data['cashback_percent'],
                            monthly_cap=cashback_data['monthly_cap'],
                            min_transaction_amount=cashback_data['min_transaction_amount']
                        )

                # Create cashback rules
                for rule_data in card_data.get('cashback_rules', []):
                    # Skip rules with missing required fields
                    if rule_data.get('category') is not None and rule_data.get('cashback_percent') is not None:
                        CashbackRule.objects.create(
                            card=card,
                            category=rule_data['category'],
                            cashback_percent=rule_data['cashback_percent'],
                            monthly_cap=rule_data.get('monthly_cap'),
                            min_transaction_amount=rule_data.get('min_transaction_amount'),
                            conditions=rule_data.get('conditions')
                        )

                # Create reward multipliers
                for multiplier_data in card_data.get('reward_multipliers', []):
                    RewardMultiplier.objects.create(
                        card=card,
                        category=multiplier_data['category'],
                        multiplier=multiplier_data['multiplier'],
                        monthly_cap=multiplier_data.get('monthly_cap'),
                        min_transaction_amount=multiplier_data.get('min_transaction_amount'),
                        conditions=multiplier_data.get('conditions')
                    )

                # Create welcome benefits
                for benefit_data in card_data.get('welcome_benefits', []):
                    WelcomeBenefit.objects.create(
                        card=card,
                        benefit_type=benefit_data['benefit_type'],
                        description=benefit_data['description'],
                        value=benefit_data['value'],
                        spend_requirement=benefit_data.get('spend_requirement'),
                        validity_days=benefit_data.get('validity_days'),
                        conditions=benefit_data.get('conditions')
                    )

                # Create milestone bonuses
                for milestone_data in card_data.get('milestone_bonuses', []):
                    MilestoneBonus.objects.create(
                        card=card,
                        spend_threshold=milestone_data['spend_threshold'],
                        bonus_type=milestone_data['bonus_type'],
                        bonus_value=milestone_data['bonus_value'],
                        validity_period=milestone_data.get('validity_period'),
                        conditions=milestone_data.get('conditions')
                    )

                # Create card benefits
                for benefit_data in card_data.get('card_benefits', []):
                    CardBenefit.objects.create(
                        card=card,
                        benefit_type=benefit_data['benefit_type'],
                        description=benefit_data['description'],
                        value=benefit_data.get('value'),
                        frequency=benefit_data.get('frequency'),
                        conditions=benefit_data.get('conditions')
                    )

                # Create fees and charges
                if 'fees_and_charges' in card_data:
                    fees_data = card_data['fees_and_charges']
                    FeesAndCharges.objects.create(
                        card=card,
                        joining_fee=fees_data.get('joining_fee'),
                        joining_fee_waiver=fees_data.get('joining_fee_waiver'),
                        interest_rate=fees_data.get('interest_rate'),
                        cash_advance_fee=fees_data.get('cash_advance_fee'),
                        late_payment_fee=fees_data.get('late_payment_fee'),
                        overlimit_fee=fees_data.get('overlimit_fee'),
                        foreign_transaction_fee=fees_data.get('foreign_transaction_fee')
                    )

                # Create eligibility criteria
                if 'eligibility_criteria' in card_data:
                    criteria_data = card_data['eligibility_criteria']
                    EligibilityCriteria.objects.create(
                        card=card,
                        min_income=criteria_data.get('min_income'),
                        min_age=criteria_data.get('min_age'),
                        max_age=criteria_data.get('max_age'),
                        employment_type=criteria_data.get('employment_type'),
                        credit_score=criteria_data.get('credit_score'),
                        additional_requirements=criteria_data.get('additional_requirements')
                    )

            self.stdout.write(self.style.SUCCESS('Successfully imported credit cards data'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('Invalid JSON format'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
