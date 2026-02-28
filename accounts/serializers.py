from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (admin-only action)."""

    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'role', 'email', 'first_name', 'last_name')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role', 'cashier'),
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for user info."""

    class Meta:
        model = User
        fields = ('id', 'username', 'role', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    """Serializer for login request."""

    username = serializers.CharField()
    password = serializers.CharField()
