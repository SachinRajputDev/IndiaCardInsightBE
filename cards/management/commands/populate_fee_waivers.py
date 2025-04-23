from django.core.management.base import BaseCommand
from cards.models import CreditCard, FeeWaiver

FEE_WAIVER_DATA = {
  "HDFC Millennia": {"joining_fee": 1000, "annual_fee": 1000, "waiver_on_spend": 100000},
  "HDFC PIXEL Go": {"joining_fee": 0, "annual_fee": 0, "waiver_on_spend": None},
  "HDFC PIXEL Play": {"joining_fee": 0, "annual_fee": 0, "waiver_on_spend": None},
  "HDFC Tata Neu Plus": {"joining_fee": 499, "annual_fee": 499, "waiver_on_spend": None},
  "HDFC Freedom": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 60000},
  "HDFC Swiggy Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 200000},
  "IndianOil HDFC Bank Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 50000},
  "HDFC Bank MoneyBack+ Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 50000},
  "HDFC Regalia Gold": {"joining_fee": 2500, "annual_fee": 2500, "waiver_on_spend": 100000},
  "HDFC Infinia Credit Card (Metal Edition)": {"joining_fee": 12500, "annual_fee": 12500, "waiver_on_spend": 1000000},
  "HDFC Diners Club Black Metal Edition": {"joining_fee": 10000, "annual_fee": 10000, "waiver_on_spend": 800000},
  "HDFC Bank Marriott Bonvoy Credit Card": {"joining_fee": 3000, "annual_fee": 3000, "waiver_on_spend": None},
  "HDFC Bank Harley-Davidson Diners Club Credit Card": {"joining_fee": 2500, "annual_fee": 2500, "waiver_on_spend": 300000},
  "HDFC Bank Diners Club Privilege Credit Card": {"joining_fee": 1000, "annual_fee": 1000, "waiver_on_spend": None},
  "Tata Neu Infinity HDFC Bank Credit Card": {"joining_fee": 1499, "annual_fee": 1499, "waiver_on_spend": 300000},
  "Shoppers Stop HDFC Bank Credit Card": {"joining_fee": 299, "annual_fee": 299, "waiver_on_spend": None},
  "Shoppers Stop Black HDFC Bank Credit Card": {"joining_fee": 4500, "annual_fee": 4500, "waiver_on_spend": None},
  "Paytm HDFC Bank Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 30000},
  "Paytm HDFC Bank Select Credit Card": {"joining_fee": 1000, "annual_fee": 1000, "waiver_on_spend": 150000},
  "Paytm HDFC Bank Mobile Credit Card": {"joining_fee": 149, "annual_fee": 149, "waiver_on_spend": 25000},
  "HDFC Bank UPI RuPay Credit Card": {"joining_fee": 99, "annual_fee": 99, "waiver_on_spend": 25000},
  "Paytm HDFC Bank Digital Credit Card": {"joining_fee": 0, "annual_fee": 0, "waiver_on_spend": None},
  "HDFC Bank Millennia EasyEMI Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 20000},
  "HDFC Bank Platinum Times Credit Card": {"joining_fee": 1000, "annual_fee": 1000, "waiver_on_spend": 250000},
  "HDFC Bank Titanium Times Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 100000},
  "HDFC Bank All Miles Credit Card": {"joining_fee": 1000, "annual_fee": 1000, "waiver_on_spend": 100000},
  "HDFC Bank Bharat Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": None},
  "HDFC Bank Diners Club Premium Credit Card": {"joining_fee": 2500, "annual_fee": 2500, "waiver_on_spend": 300000},
  "HDFC Bank Diners Club Rewardz Credit Card": {"joining_fee": 1000, "annual_fee": 1000, "waiver_on_spend": 100000},
  "HDFC Bank Doctor's Regalia Credit Card": {"joining_fee": None, "annual_fee": None, "waiver_on_spend": None},
  "HDFC Bank Doctor's Superia Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 100000},
  "JetPrivilege HDFC Bank Titanium Credit Card": {"joining_fee": 499, "annual_fee": 499, "waiver_on_spend": 150000},
  "HDFC Bank Platinum Edge Credit Card": {"joining_fee": None, "annual_fee": None, "waiver_on_spend": None},
  "HDFC Bank Platinum Plus Credit Card": {"joining_fee": None, "annual_fee": None, "waiver_on_spend": None},
  "HDFC Bank Solitaire Credit Card": {"joining_fee": 999, "annual_fee": 999, "waiver_on_spend": None},
  "HDFC Bank Superia Credit Card": {"joining_fee": None, "annual_fee": None, "waiver_on_spend": {"first_year": 15000, "renewal": 75000}},
  "HDFC Bank Teachers Platinum Credit Card": {"joining_fee": None, "annual_fee": None, "waiver_on_spend": None},
  "HDFC Bank Titanium Edge Credit Card": {"joining_fee": 500, "annual_fee": 500, "waiver_on_spend": 50000},
  "HDFC Bank Visa Signature Credit Card": {"joining_fee": None, "annual_fee": None, "waiver_on_spend": {"first_year": 15000, "renewal": 75000}},
  "HDFC Bank World MasterCard Credit Card": {"joining_fee": None, "annual_fee": None, "waiver_on_spend": {"first_year": 15000, "renewal": 75000}},
  "HDFC Bank Regalia First Credit Card": {"joining_fee": 1000, "annual_fee": 1000, "waiver_on_spend": 100000}
}

class Command(BaseCommand):
    help = "Populates FeeWaiver data for HDFC cards from a predefined JSON."

    def handle(self, *args, **options):
        for card_name, waiver_data in FEE_WAIVER_DATA.items():
            try:
                card = CreditCard.objects.get(card_name=card_name)
            except CreditCard.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Card not found: {card_name}"))
                continue

            joining_fee = waiver_data.get("joining_fee", 0) or 0
            annual_fee = waiver_data.get("annual_fee", 0) or 0
            waiver_on_annual_spend = waiver_data.get("waiver_on_spend")
            if isinstance(waiver_on_annual_spend, dict) or waiver_on_annual_spend is None:
                waiver_on_annual_spend = 0

            fw, created = FeeWaiver.objects.update_or_create(
                card=card,
                defaults={
                    "joining_fee": joining_fee,
                    "annual_fee": annual_fee,
                    "waiver_on_annual_spends": waiver_on_annual_spend,
                }
            )
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} FeeWaiver for {card_name}"))
