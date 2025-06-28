from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import random

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'address', 'avatar', 'initials']
        extra_kwargs = {
            'email': {'required': False},  # Make email optional for updates
            'phone': {'required': False, 'allow_blank': True},
            'address': {'required': False, 'allow_blank': True},
        }
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_avatar(self, obj):
        if obj.avatar:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
        return None
    
    def get_initials(self, obj):
        if not obj.avatar:
            initials = ''
            if obj.first_name:
                initials += obj.first_name[0].upper()
            if obj.last_name:
                initials += obj.last_name[0].upper()
            return initials or obj.username[0].upper()
        return ''
    
    def update(self, instance, validated_data):
        # Handle email separately to avoid overwriting with None
        if 'email' in validated_data and validated_data['email'] is None:
            del validated_data['email']
        
        return super().update(instance, validated_data)
    
    def to_internal_value(self, data):
        internal_data = super().to_internal_value(data)
        if 'name' in data:
            name_parts = data['name'].split(' ', 1)
            internal_data['first_name'] = name_parts[0]
            internal_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        return internal_data