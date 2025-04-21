from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'credit-cards', views.UserCreditCardViewSet)
router.register(r'preferences', views.UserPreferencesViewSet)
router.register(r'activities', views.UserActivityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
