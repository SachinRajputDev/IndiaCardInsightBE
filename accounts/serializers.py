from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, UserCreditCard, UserPreferences, UserActivity


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class UserCreditCardSerializer(serializers.ModelSerializer):
    credit_card_details = serializers.SerializerMethodField()
    
    class Meta:
        model = UserCreditCard
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def get_credit_card_details(self, obj):
        from cards.serializers import CreditCardSerializer
        return CreditCardSerializer(obj.credit_card).data


class UserPreferencesSerializer(serializers.ModelSerializer):
    preferred_banks_details = serializers.SerializerMethodField()
    
    class Meta:
        model = UserPreferences
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def get_preferred_banks_details(self, obj):
        from cards.serializers import BankSerializer
        return BankSerializer(obj.preferred_banks.all(), many=True).data


class UserActivitySerializer(serializers.ModelSerializer):
    credit_card_details = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at')
    
    def get_credit_card_details(self, obj):
        if obj.credit_card:
            from cards.serializers import CreditCardSerializer
            return CreditCardSerializer(obj.credit_card).data
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'first_name', 'last_name')
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match")
        return data
