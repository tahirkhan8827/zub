from django.contrib import admin
from .models import Cart, CartItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'created_at', 'updated_at', 'item_count', 'total']
    

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('username', 'product', 'quantity', 'price', 'subtotal', 'created_at')
    list_select_related = ('cart__user', 'product')  # Optimizes database queries
    
    def username(self, obj):
        return obj.cart.user.username
    username.short_description = 'Username'
    username.admin_order_field = 'cart__user__username'  # Allows sorting by username