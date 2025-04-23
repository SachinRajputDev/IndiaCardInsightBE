from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreditCardViewSet

router = DefaultRouter()
router.register(r'cards', CreditCardViewSet)

from .views import form_schema, recommend_cards, all_categories, subcategories, brands, purchase_advisor

urlpatterns = [
    path('', include(router.urls)),
    path('form-schema/', form_schema, name='form-schema'),
    path('recommend/', recommend_cards, name='recommend-cards'),
    path('categories/', all_categories, name='all-categories'),
    path('subcategories/', subcategories, name='subcategories'),
    path('brands/', brands, name='brands'),
    path('purchase-advisor/', purchase_advisor, name='purchase-advisor'),
]
