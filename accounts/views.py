from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import UserProfile, UserCreditCard, UserPreferences, UserActivity
from .serializers import (
    UserSerializer, UserProfileSerializer, UserCreditCardSerializer,
    UserPreferencesSerializer, UserActivitySerializer, UserRegistrationSerializer,
    ChangePasswordSerializer
)


class UserCreditCardFilter(filters.FilterSet):
    card_name = filters.CharFilter(field_name='credit_card__card_name', lookup_expr='icontains')
    bank = filters.CharFilter(field_name='credit_card__bank__name', lookup_expr='icontains')
    status = filters.CharFilter(lookup_expr='exact')
    joining_date_after = filters.DateFilter(field_name='joining_date', lookup_expr='gte')
    joining_date_before = filters.DateFilter(field_name='joining_date', lookup_expr='lte')

    class Meta:
        model = UserCreditCard
        fields = ['status', 'annual_fee_waived']


class UserActivityFilter(filters.FilterSet):
    activity_type = filters.CharFilter(lookup_expr='exact')
    date_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = UserActivity
        fields = ['activity_type']


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user accounts."""
    
    swagger_tags = ['User Management']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.none()
    
    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=UserRegistrationSerializer,
        responses={201: UserSerializer}
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'status': 'success',
                'message': 'User registered successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.data['old_password']):
                return Response({'error': 'Invalid old password'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.data['new_password'])
            user.save()
            return Response({'status': 'success'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user profiles."""
    
    swagger_tags = ['User Profile']
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # Log the activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='profile_updated',
            description='Profile information updated'
        )


class UserCreditCardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user's credit cards."""
    
    swagger_tags = ['User Credit Cards']
    filterset_class = UserCreditCardFilter
    search_fields = ['credit_card__card_name', 'credit_card__bank__name', 'notes']
    ordering_fields = ['joining_date', 'created_at', 'credit_limit']
    ordering = ['-created_at']
    queryset = UserCreditCard.objects.all()
    serializer_class = UserCreditCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserCreditCard.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='card_added',
            credit_card=serializer.instance.credit_card,
            description=f'Added {serializer.instance.credit_card.card_name} to portfolio'
        )
    
    def perform_update(self, serializer):
        instance = serializer.save()
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='card_updated',
            credit_card=instance.credit_card,
            description=f'Updated {instance.credit_card.card_name} details'
        )
    
    def perform_destroy(self, instance):
        card_name = instance.credit_card.card_name
        instance.delete()
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='card_removed',
            description=f'Removed {card_name} from portfolio'
        )


class UserPreferencesViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user preferences."""
    
    swagger_tags = ['User Preferences']
    queryset = UserPreferences.objects.all()
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserPreferences.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='preferences_updated',
            description='Card preferences updated'
        )


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing user activity history."""
    
    swagger_tags = ['User Activity']
    filterset_class = UserActivityFilter
    search_fields = ['description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)
