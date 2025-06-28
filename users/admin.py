from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'get_full_name', 'phone', 'is_staff')
    
    # Fields to display in the user edit form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Make the full name searchable - FIXED VERSION
    def get_search_fields(self, request):
        search_fields = super().get_search_fields(request)
        return search_fields + ('first_name', 'last_name')  # Note the tuple instead of list