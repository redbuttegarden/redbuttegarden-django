from rest_framework import serializers

from custom_user.models import User


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
