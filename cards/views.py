from rest_framework import viewsets, filters
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from .models import CreditCard, PromotionalBanner
from .serializers import CreditCardSerializer, PromotionalBannerSerializer, CardRecommendationInputSerializer
from .utils import get_top_card_groups
from rest_framework.decorators import api_view
from rest_framework import status
from .formschema import get_form_schema

@api_view(['POST'])
def recommend_cards(request):
    """
    Recommend credit cards based on spending form input.
    """
    serializer = CardRecommendationInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    spending = serializer.validated_data['spending']
    preferences = serializer.validated_data.get('preferences', {})
    # Determine group size: use desiredCardCount from frontend, fallback to num_new_cards
    num_new_cards = preferences.get('desiredCardCount', preferences.get('num_new_cards', 1))
    cards = list(CreditCard.objects.all())

    # Generate top groups of num_new_cards
    group_results = get_top_card_groups(cards, spending, group_size=num_new_cards, max_groups=10)
    groups = []
    filtered_groups = []
    seen_groups = set()
    for group_result in group_results:
        # Only include groups with strictly positive netBenefit
        if group_result.get('netBenefit', 0) <= 0:
            continue
        group_cards = group_result['cards']
        # ensure uniqueness: skip if same card ID set seen
        card_ids = tuple(sorted(card.id for card in group_cards))
        if card_ids in seen_groups:
            continue
        seen_groups.add(card_ids)
        group_cards_serialized = []
        for card in group_cards:
            savings_breakdown = [
                {
                    'spendEntry': b['spendEntry'],
                    'savings': b['savings'],
                    'cashbackPercent': b['cashbackPercent']
                }
                for b in group_result.get('breakdown', []) if b.get('bestCardId') == card.id
            ]
            total_spend = sum(b['spendEntry'].get('amount', 0) for b in group_result.get('breakdown', []))
            covered_spend = sum(b['spendEntry'].get('amount', 0) for b in savings_breakdown)
            if total_spend > 0:
                coverage_percentage = round(covered_spend / total_spend * 100, 2)
            else:
                coverage_percentage = 0.0
            group_cards_serialized.append({
                'card': CreditCardSerializer(card).data,
                'cardName': card.card_name,
                'savingsBreakdown': [
                    {
                        **b,
                        'category': b['spendEntry'].get('category', ''),
                        'amount': b['spendEntry'].get('amount', 0)
                    }
                    for b in savings_breakdown
                ],
                'spendCoverage': coverage_percentage,
                'netBenefit': group_result['cardNetBenefits'].get(card.id, {}).get('net_benefit', 0),
                'totalMonthlySavings': sum((b['savings'] or 0) for b in savings_breakdown)
            })
        # Only include groups with at least one valuable card
        if not group_cards_serialized:
            continue
        filtered_groups.append({
            'cards': group_cards_serialized,
            'totalGroupSavings': group_result.get('totalSavings', 0),
            'spendCoverage': group_result.get('spendCoverage', 0),
            'breakdown': group_result.get('breakdown', []),
            'netBenefit': group_result.get('netBenefit', 0),
            'cardNetBenefits': group_result.get('cardNetBenefits', {})
        })
    # Order by totalGroupSavings descending
    groups = sorted(filtered_groups, key=lambda g: g['totalGroupSavings'], reverse=True)
    # Do NOT pad the groups list to 10; just return as many as make sense (up to 10)
    groups = groups[:10]

    # Prepare spendToCardSavings as before
    spend_to_card_savings = []
    for idx, spend in enumerate(spending):
        spend_entry = {
            'spendEntryIndex': idx,
            'category': spend.get('category', ''),
            'amount': spend.get('amount', 0),
            'cardSavings': []
        }
        for card in cards:
            matched_rule = None
            for rule in card.cashback_rules.all():
                if rule.category and spend.get('category') and rule.category.lower() == spend.get('category').lower():
                    matched_rule = rule
                    break
            if matched_rule and matched_rule.cashback_percent:
                cashback_percent = matched_rule.cashback_percent
            elif hasattr(card, 'default_cashback') and card.default_cashback and card.default_cashback.cashback_percent:
                cashback_percent = card.default_cashback.cashback_percent
            else:
                cashback_percent = 0
            savings = round(spend.get('amount', 0) * cashback_percent / 100, 2)
            spend_entry['cardSavings'].append({
                'cardId': card.id,
                'cardName': card.card_name,
                'savings': savings,
                'cashbackPercent': cashback_percent
            })
        spend_to_card_savings.append(spend_entry)
    return Response({
        "recommendations": groups,
        "spendToCardSavings": spend_to_card_savings
    }, status=status.HTTP_200_OK)



@api_view(['GET'])
def form_schema(request):
    form_name = request.query_params.get('name')
    schema = get_form_schema(form_name)
    if not schema:
        return Response({'detail': 'Form schema not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(schema)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_categories(request):
    from .models import CashbackRule
    categories = CashbackRule.objects.exclude(category__isnull=True).exclude(category__exact='').values_list('category', flat=True).distinct()
    return Response(sorted(categories))

@api_view(['GET'])
@permission_classes([AllowAny])
def subcategories(request):
    from .models import CashbackRule
    category = request.query_params.get('category')
    if not category:
        return Response([], status=400)
    subcategories = CashbackRule.objects.filter(category=category).exclude(subcategory__isnull=True).exclude(subcategory__exact='').values_list('subcategory', flat=True).distinct()
    return Response(sorted(subcategories))

@api_view(['GET'])
@permission_classes([AllowAny])
def brands(request):
    from .models import CashbackRule
    category = request.query_params.get('category')
    subcategory = request.query_params.get('subcategory')
    queryset = CashbackRule.objects.all()
    if category:
        queryset = queryset.filter(category=category)
    if subcategory:
        queryset = queryset.filter(subcategory=subcategory)
    brands = set()
    for rule in queryset:
        if rule.brand:
            if isinstance(rule.brand, list):
                brands.update(rule.brand)
            else:
                brands.add(rule.brand)
    return Response(sorted(brands))

class CreditCardViewSet(viewsets.ModelViewSet):
    queryset = CreditCard.objects.all()
    serializer_class = CreditCardSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['card_name', 'bank', 'card_type', 'network']
    ordering_fields = ['annual_fee', 'effective_annual_fee', 'promotional_order']

    @action(detail=False, methods=['get'])
    def promotional_cards(self, request):
        """
        Returns all cards marked as promotional (for homepage/banner), ordered by promotional_order.
        """
        queryset = CreditCard.objects.filter(promotional_card=True).order_by('promotional_order')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def promotional_banners(self, request):
        """
        Returns all promotional banners with card details, ordered by 'order'.
        """
        queryset = PromotionalBanner.objects.select_related('card').all().order_by('order')
        serializer = PromotionalBannerSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def filter_cards(self, request):
        queryset = self.get_queryset()
        
        # Filter by card type
        card_type = request.query_params.get('card_type', None)
        if card_type:
            queryset = queryset.filter(card_type=card_type)

        # Filter by network
        network = request.query_params.get('network', None)
        if network:
            queryset = queryset.filter(network=network)

        # Filter by bank
        bank = request.query_params.get('bank', None)
        if bank:
            queryset = queryset.filter(bank=bank)

        # Filter by annual fee range
        min_fee = request.query_params.get('min_fee', None)
        max_fee = request.query_params.get('max_fee', None)
        if min_fee is not None:
            queryset = queryset.filter(annual_fee__gte=min_fee)
        if max_fee is not None:
            queryset = queryset.filter(annual_fee__lte=max_fee)

        # Filter by effective annual fee range
        min_effective_fee = request.query_params.get('min_effective_fee', None)
        max_effective_fee = request.query_params.get('max_effective_fee', None)
        if min_effective_fee is not None:
            queryset = queryset.filter(effective_annual_fee__gte=min_effective_fee)
        if max_effective_fee is not None:
            queryset = queryset.filter(effective_annual_fee__lte=max_effective_fee)

        # Filter by minimum income
        min_income = request.query_params.get('min_income', None)
        if min_income is not None:
            queryset = queryset.filter(eligibility_criteria__min_income__lte=min_income)

        # Filter by credit score
        credit_score = request.query_params.get('credit_score', None)
        if credit_score is not None:
            queryset = queryset.filter(eligibility_criteria__credit_score__lte=credit_score)

        # Filter by cashback percentage
        min_cashback = request.query_params.get('min_cashback', None)
        if min_cashback is not None:
            queryset = queryset.filter(
                Q(default_cashback__cashback_percent__gte=min_cashback) |
                Q(cashback_rules__cashback_percent__gte=min_cashback)
            ).distinct()

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def compare_cards(self, request):
        card_names = request.query_params.getlist('cards')
        queryset = self.get_queryset().filter(card_name__in=card_names)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_cards(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])

        queryset = self.get_queryset().filter(
            Q(card_name__icontains=query) |
            Q(bank__icontains=query) |
            Q(card_type__icontains=query) |
            Q(network__icontains=query)
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
