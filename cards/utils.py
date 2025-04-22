from itertools import combinations

def parse_benefit_value(value):
    # Try to extract a numeric value from benefit (e.g., "₹500 Amazon voucher")
    import re
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[₹Rs. ]*(\d+[\.,]?\d*)", value)
        if match:
            return float(match.group(1).replace(",", ""))
    return 0.0

def get_card_net_benefit(card, total_cashback):
    # Get effective annual fee
    fee = getattr(card, 'effective_annual_fee', None)
    if fee is None or fee == 0:
        fee = getattr(card, 'annual_fee', 0)
    # Welcome benefits
    welcome_benefits = sum(parse_benefit_value(b.value) for b in getattr(card, 'welcome_benefits', []).all())
    # Milestone bonuses (assume all are achievable for now)
    milestone_bonuses = sum(getattr(b, 'bonus_value', 0) for b in getattr(card, 'milestone_bonuses', []).all())
    # Other card benefits
    other_benefits = sum(parse_benefit_value(b.value) for b in getattr(card, 'card_benefits', []).all())
    # Net benefit
    net_benefit = total_cashback + welcome_benefits + milestone_bonuses + other_benefits - (fee or 0)
    return {
        'annual_fee': fee or 0,
        'welcome_benefits': welcome_benefits,
        'milestone_bonuses': milestone_bonuses,
        'other_benefits': other_benefits,
        'net_benefit': net_benefit
    }

def get_top_card_groups(cards, spending, group_size=1, max_groups=10):
    """
    Recommend a group of cards only if the group provides higher total savings than any of its members individually.
    If two or more cards are redundant (identical benefits for all spends), recommend them individually, not as a group.
    For each group or individual card, include a 'reasoning' string explaining why it is recommended as a group or individually.
    Output is a list of dicts with keys: type ('group' or 'individual'), cards, breakdown, netBenefit, reasoning, etc.
    """
    card_list = list(cards)
    group_candidates = list(combinations(card_list, group_size))
    group_results = []
    individual_results = []
    for card in card_list:
        total_savings = 0
        breakdown = []
        total_spend = 0
        covered_spend = 0
        is_best_for_any = False
        for spend in spending:
            spend_amount = spend.get('amount', 0)
            spend_category = spend.get('category', '').lower() if spend.get('category') else None
            total_spend += spend_amount
            matched_rule = None
            for rule in card.cashback_rules.all():
                if rule.category and spend_category and rule.category.lower() == spend_category:
                    matched_rule = rule
                    break
            if matched_rule and matched_rule.cashback_percent:
                cashback_percent = matched_rule.cashback_percent
            elif hasattr(card, 'default_cashback') and card.default_cashback and card.default_cashback.cashback_percent:
                cashback_percent = card.default_cashback.cashback_percent
            else:
                cashback_percent = 0
            saving = round(spend_amount * cashback_percent / 100, 2)
            total_savings += saving
            if saving > 0:
                covered_spend += spend_amount
            breakdown.append({
                'spendEntry': spend,
                'bestCardId': card.id if saving > 0 else None,
                'savings': saving,
                'cashbackPercent': cashback_percent
            })
        # Determine if this card is 'best' for at least one spend (even if tied)
        for spend_idx, spend in enumerate(spending):
            spend_amount = spend.get('amount', 0)
            spend_category = spend.get('category', '').lower() if spend.get('category') else None
            # Find the max saving for this spend among all cards
            max_saving = 0
            for other_card in card_list:
                matched_rule = None
                for rule in other_card.cashback_rules.all():
                    if rule.category and spend_category and rule.category.lower() == spend_category:
                        matched_rule = rule
                        break
                if matched_rule and matched_rule.cashback_percent:
                    cashback_percent = matched_rule.cashback_percent
                elif hasattr(other_card, 'default_cashback') and other_card.default_cashback and other_card.default_cashback.cashback_percent:
                    cashback_percent = other_card.default_cashback.cashback_percent
                else:
                    cashback_percent = 0
                saving = round(spend_amount * cashback_percent / 100, 2)
                if saving > max_saving:
                    max_saving = saving
            if breakdown[spend_idx]['savings'] == max_saving and max_saving > 0:
                is_best_for_any = True
                break
        spend_coverage = round((covered_spend / total_spend) * 100, 2) if total_spend > 0 else 0.0
        net_benefit_info = get_card_net_benefit(card, total_savings)
        if is_best_for_any and total_savings > 0:
            reasoning = "This card is among the best for at least one of your spends."
            individual_results.append({
                'type': 'individual',
                'cards': [card],
                'totalSavings': total_savings,
                'breakdown': breakdown,
                'spendCoverage': spend_coverage,
                'netBenefit': net_benefit_info['net_benefit'],
                'cardNetBenefits': {card.id: net_benefit_info},
                'reasoning': reasoning
            })
    # Now, compute groups
    for group in group_candidates:
        if len(group) < 2:
            continue
        if len(group) > group_size:
            continue
        total_savings = 0
        breakdown = []
        total_spend = 0
        covered_spend = 0
        per_card_cashback = {card.id: 0 for card in group}
        spend_to_best_card = {}
        for spend in spending:
            spend_amount = spend.get('amount', 0)
            spend_category = spend.get('category', '').lower() if spend.get('category') else None
            total_spend += spend_amount
            best_saving = 0
            best_card = None
            best_cashback_percent = 0
            for card in group:
                matched_rule = None
                for rule in card.cashback_rules.all():
                    if rule.category and spend_category and rule.category.lower() == spend_category:
                        matched_rule = rule
                        break
                if matched_rule and matched_rule.cashback_percent:
                    cashback_percent = matched_rule.cashback_percent
                elif hasattr(card, 'default_cashback') and card.default_cashback and card.default_cashback.cashback_percent:
                    cashback_percent = card.default_cashback.cashback_percent
                else:
                    cashback_percent = 0
                saving = round(spend_amount * cashback_percent / 100, 2)
                if saving > best_saving:
                    best_saving = saving
                    best_card = card
                    best_cashback_percent = cashback_percent
            total_savings += best_saving
            if best_card:
                per_card_cashback[best_card.id] += best_saving
                spend_to_best_card.setdefault(best_card.id, []).append(spend)
            if best_saving > 0:
                covered_spend += spend_amount
            breakdown.append({
                'spendEntry': spend,
                'bestCardId': best_card.id if best_card else None,
                'bestCardName': best_card.card_name if best_card else None,
                'savings': best_saving,
                'cashbackPercent': best_cashback_percent
            })
        group_cards = list(group)
        # Only keep cards in group that actually contribute savings
        cards_with_savings = [card for card in group_cards if per_card_cashback[card.id] > 0]
        if len(cards_with_savings) == 0:
            continue
        if len(cards_with_savings) > group_size:
            continue
        group_net_benefit = 0
        card_net_benefits = {}
        for card in cards_with_savings:
            net_benefit_info = get_card_net_benefit(card, per_card_cashback[card.id])
            card_net_benefits[card.id] = net_benefit_info
            group_net_benefit += net_benefit_info['net_benefit']
        max_individual = max([
            r['netBenefit'] for r in individual_results if r['cards'][0] in cards_with_savings
        ], default=0)
        if group_net_benefit <= max_individual:
            continue
        reasoning = "Group these cards: together they cover different categories for better total savings than any card alone."
        group_results.append({
            'type': 'group',
            'cards': list(cards_with_savings),
            'totalSavings': total_savings,
            'breakdown': breakdown,
            'spendCoverage': round((covered_spend / total_spend) * 100, 2) if total_spend > 0 else 0.0,
            'netBenefit': group_net_benefit,
            'cardNetBenefits': card_net_benefits,
            'reasoning': reasoning
        })
    # Combine, deduplicate, and always include best individual(s) in top 5
    all_results = group_results + individual_results
    all_results = [r for r in all_results if r['netBenefit'] > 0]
    all_results.sort(key=lambda g: g['netBenefit'], reverse=True)
    best_individuals = sorted(
        [r for r in individual_results if r['netBenefit'] > 0],
        key=lambda g: g['netBenefit'],
        reverse=True
    )
    final_results = []
    seen_cards = set()
    for r in all_results:
        ids = tuple(sorted(card.id for card in r['cards']))
        if ids not in seen_cards:
            final_results.append(r)
            seen_cards.add(ids)
        if len(final_results) >= 5:
            break
    for r in best_individuals:
        ids = tuple(sorted(card.id for card in r['cards']))
        if ids not in seen_cards:
            final_results.append(r)
            seen_cards.add(ids)
        if len(final_results) >= 5:
            break
    return final_results
    """
    Recommend a group of cards only if the group provides higher total savings than any of its members individually.
    If two or more cards are redundant (identical benefits for all spends), recommend them individually, not as a group.
    For each group or individual card, include a 'reasoning' string explaining why it is recommended as a group or individually.
    Output is a list of dicts with keys: type ('group' or 'individual'), cards, breakdown, netBenefit, reasoning, etc.
    """
    card_list = list(cards)
    group_candidates = list(combinations(card_list, group_size))
    group_results = []
    # Recommend all cards that are 'best' for at least one spend (even if multiple tie for best), but only if their total savings > 0.
    individual_results = []
    for card in card_list:
        total_savings = 0
        breakdown = []
        total_spend = 0
        covered_spend = 0
        is_best_for_any = False
        for spend in spending:
            spend_amount = spend.get('amount', 0)
            spend_category = spend.get('category', '').lower() if spend.get('category') else None
            total_spend += spend_amount
            matched_rule = None
            for rule in card.cashback_rules.all():
                if rule.category and spend_category and rule.category.lower() == spend_category:
                    matched_rule = rule
                    break
            if matched_rule and matched_rule.cashback_percent:
                cashback_percent = matched_rule.cashback_percent
            elif hasattr(card, 'default_cashback') and card.default_cashback and card.default_cashback.cashback_percent:
                cashback_percent = card.default_cashback.cashback_percent
            else:
                cashback_percent = 0
            saving = round(spend_amount * cashback_percent / 100, 2)
            total_savings += saving
            if saving > 0:
                covered_spend += spend_amount
            breakdown.append({
                'spendEntry': spend,
                'bestCardId': card.id if saving > 0 else None,
                'savings': saving,
                'cashbackPercent': cashback_percent
            })
        # Determine if this card is 'best' for at least one spend (even if tied)
        for spend_idx, spend in enumerate(spending):
            spend_amount = spend.get('amount', 0)
            spend_category = spend.get('category', '').lower() if spend.get('category') else None
            # Find the max saving for this spend among all cards
            max_saving = 0
            for other_card in card_list:
                matched_rule = None
                for rule in other_card.cashback_rules.all():
                    if rule.category and spend_category and rule.category.lower() == spend_category:
                        matched_rule = rule
                        break
                if matched_rule and matched_rule.cashback_percent:
                    cashback_percent = matched_rule.cashback_percent
                elif hasattr(other_card, 'default_cashback') and other_card.default_cashback and other_card.default_cashback.cashback_percent:
                    cashback_percent = other_card.default_cashback.cashback_percent
                else:
                    cashback_percent = 0
                saving = round(spend_amount * cashback_percent / 100, 2)
                if saving > max_saving:
                    max_saving = saving
            # Now check if this card matches the max saving for this spend and saving > 0
            if breakdown[spend_idx]['savings'] == max_saving and max_saving > 0:
                is_best_for_any = True
                break
        spend_coverage = round((covered_spend / total_spend) * 100, 2) if total_spend > 0 else 0.0
        net_benefit_info = get_card_net_benefit(card, total_savings)
        if is_best_for_any and total_savings > 0:
            reasoning = "This card is among the best for at least one of your spends."
            individual_results.append({
                'type': 'individual',
                'cards': [card],
                'totalSavings': total_savings,
                'breakdown': breakdown,
                'spendCoverage': spend_coverage,
                'netBenefit': net_benefit_info['net_benefit'],
                'cardNetBenefits': {card.id: net_benefit_info},
                'reasoning': reasoning
            })
    # Now, compute groups
    for group in group_candidates:
        if len(group) < 2:
            continue
        # Enforce group size constraint
        if len(group) > group_size:
            continue
        total_savings = 0
        breakdown = []
        total_spend = 0
        covered_spend = 0
        per_card_cashback = {card.id: 0 for card in group}
        spend_to_best_card = {}
        for spend in spending:
            spend_amount = spend.get('amount', 0)
            spend_category = spend.get('category', '').lower() if spend.get('category') else None
            total_spend += spend_amount
            best_saving = 0
            best_card = None
            best_cashback_percent = 0
            for card in group:
                matched_rule = None
                for rule in card.cashback_rules.all():
                    if rule.category and spend_category and rule.category.lower() == spend_category:
                        matched_rule = rule
                        break
                if matched_rule and matched_rule.cashback_percent:
                    cashback_percent = matched_rule.cashback_percent
                elif hasattr(card, 'default_cashback') and card.default_cashback and card.default_cashback.cashback_percent:
                    cashback_percent = card.default_cashback.cashback_percent
                else:
                    cashback_percent = 0
                saving = round(spend_amount * cashback_percent / 100, 2)
                if saving > best_saving:
                    best_saving = saving
                    best_card = card
                    best_cashback_percent = cashback_percent
            total_savings += best_saving
            if best_card:
                per_card_cashback[best_card.id] += best_saving
                spend_to_best_card.setdefault(best_card.id, []).append(spend)
            if best_saving > 0:
                covered_spend += spend_amount
            breakdown.append({
                'spendEntry': spend,
                'bestCardId': best_card.id if best_card else None,
                'bestCardName': best_card.card_name if best_card else None,
                'savings': best_saving,
                'cashbackPercent': best_cashback_percent
            })
        group_cards = list(group)
        # Only keep cards in group that actually contribute savings
        cards_with_savings = [card for card in group_cards if per_card_cashback[card.id] > 0]
        if len(cards_with_savings) == 0:
            continue  # No card contributes, skip
        if len(cards_with_savings) > group_size:
            continue  # More than allowed contributing cards
        # Check if group provides higher net benefit than any member alone
        group_net_benefit = 0
        card_net_benefits = {}
        for card in cards_with_savings:
            net_benefit_info = get_card_net_benefit(card, per_card_cashback[card.id])
            card_net_benefits[card.id] = net_benefit_info
            group_net_benefit += net_benefit_info['net_benefit']
        max_individual = max([
            r['netBenefit'] for r in individual_results if r['cards'][0] in cards_with_savings
        ], default=0)
        if group_net_benefit <= max_individual:
            continue  # Only recommend group if it's strictly better
        # Reasoning
        reasoning = "Group these cards: together they cover different categories for better total savings than any card alone."
        group_results.append({
            'type': 'group',
            'cards': list(cards_with_savings),
            'totalSavings': total_savings,
            'breakdown': breakdown,
            'spendCoverage': round((covered_spend / total_spend) * 100, 2) if total_spend > 0 else 0.0,
            'netBenefit': group_net_benefit,
            'cardNetBenefits': card_net_benefits,
            'reasoning': reasoning
        })
    # Return both group and individual recommendations, sorted by netBenefit
    all_results = group_results + individual_results
    # Only skip cards/groups with netBenefit <= 0
    all_results = [r for r in all_results if r['netBenefit'] > 0]
    all_results.sort(key=lambda g: g['netBenefit'], reverse=True)
    # Always limit to top 5 results
    return all_results[:5]