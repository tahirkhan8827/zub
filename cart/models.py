from django.db import models
from django.conf import settings
from products.models import Products,Size  # Your Products model

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return self.items.count()
    
  

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)  # Add size field
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    


    def __str__(self):
        return self.product.name

    @property
    def subtotal(self):
        return self.price * self.quantity
    
    def username(self):
        return self.cart.user.username  # Assuming your Cart model has a user field
    
    username.short_description = 'Username'  # Sets the column header in admin

    class Meta:
        unique_together = ('cart', 'product', 'size')