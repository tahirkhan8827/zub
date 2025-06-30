from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json
from .models import Cart, CartItem
from products.models import *

def get_or_create_cart(request):
    """Helper to get or create cart for user/session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart

# views.py
@csrf_exempt
@require_GET
def cart_api(request):
    """Get current cart contents with size info"""
    try:
        cart = get_or_create_cart(request)
        items = CartItem.objects.filter(cart=cart).select_related('product', 'size', 'color')
        
        cart_items = []
        for item in items:
            # Get the correct image based on selected color
            first_image = None
            try:
                if item.color:
                    # Find the ProductColor for this item's product and color
                    product_color = ProductColor.objects.filter(
                        product=item.product,
                        color=item.color
                    ).first()
                    
                    if product_color:
                        first_image = product_color.images.first()
                else:
                    # Fallback to first color's image if no color selected
                    product_color = item.product.colors.first()
                    if product_color:
                        first_image = product_color.images.first()
                        
            except Exception as e:
                print(f"Error getting product image: {e}")
            
            cart_items.append({
                'id': item.id,
                'product_id': item.product.id,
                'name': item.product.name,
                'price': float(item.price),
                'quantity': item.quantity,
                'size_id': item.size.id,
                'size_name': item.size.name,
                'color_id': item.color.id if item.color else None,
                'color_name': item.color.name if item.color else None,
                'image': request.build_absolute_uri(first_image.image.url) if first_image and first_image.image else None,
            })
        
        return JsonResponse({
            'status': 'success',
            'items': cart_items,
            'total': float(cart.total),
            'item_count': cart.item_count,
            'csrf_token': get_token(request)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# views.py
@csrf_exempt
@require_POST
def add_to_cart(request, product_id):
    try:
        cart = get_or_create_cart(request)
        data = json.loads(request.body)
        size_id = data.get('size_id')
        color_id = data.get('color_id')  # Add color_id parameter
        quantity = int(data.get('quantity', 1))
        
        if not size_id:
            return JsonResponse({'status': 'error', 'message': 'Size is required'}, status=400)
            
        try:
            product = Products.objects.get(id=product_id)
            size = Size.objects.get(id=size_id)
            
            # Get color if provided
            color = None
            if color_id:
                color = Color.objects.get(id=color_id)
                # Verify this color exists for this product
                if not ProductColor.objects.filter(product=product, color=color).exists():
                    return JsonResponse({'status': 'error', 'message': 'Invalid color for this product'}, status=400)
            
            # Get or create cart item with both size and color
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                size=size,
                color=color,  # Add color to the unique together
                defaults={
                    'quantity': quantity,
                    'price': product.currentprice
                }
            )
            
            if not created:
                item.quantity += quantity
                item.save()
                
            return JsonResponse({
                'status': 'success',
                'message': 'Item added to cart',
                'item_count': cart.item_count,
                'total': float(cart.total)
            })
            
        except Products.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
        except Size.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Size not found'}, status=404)
        except Color.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Color not found'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
@csrf_exempt
@require_POST
def update_cart_item(request, product_id):
    """Update cart item quantity"""
    try:
        cart = get_or_create_cart(request)
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        size_id = data.get('size_id')
        color_id = data.get('color_id', None)  # Optional color_id
        
        # Find the specific cart item with product_id, size_id, and color_id
        try:
            item = CartItem.objects.get(
                cart=cart,
                product_id=product_id,
                size_id=size_id,
                color_id=color_id
            )
            
            if quantity < 1:
                item.delete()
            else:
                item.quantity = quantity
                item.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Cart updated',
                'total': float(cart.total),
                'item_count': cart.item_count
            })
            
        except CartItem.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Item not found in cart'
            }, status=404)
        except CartItem.MultipleObjectsReturned:
            # Handle case where multiple items exist (shouldn't happen with proper constraints)
            items = CartItem.objects.filter(
                cart=cart,
                product_id=product_id,
                size_id=size_id,
                color_id=color_id
            )
            # Delete all and create a new one with summed quantities
            total_quantity = sum(item.quantity for item in items)
            items.delete()
            
            if quantity > 0:
                CartItem.objects.create(
                    cart=cart,
                    product_id=product_id,
                    size_id=size_id,
                    color_id=color_id,
                    quantity=total_quantity,
                    price=items[0].price  # Assuming same price for all
                )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Consolidated duplicate items',
                'total': float(cart.total),
                'item_count': cart.item_count
            })
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
@csrf_exempt
@require_POST
def remove_cart_item(request, product_id):
    """Remove item from cart"""
    try:
        cart = get_or_create_cart(request)
        data = json.loads(request.body)
        size_id = data.get('size_id')
        color_id = data.get('color_id', None)  # Optional color_id
        
        # Delete all matching items (should be just one due to unique constraint)
        deleted_count, _ = CartItem.objects.filter(
            cart=cart,
            product_id=product_id,
            size_id=size_id,
            color_id=color_id
        ).delete()
        
        if deleted_count == 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Item not found in cart'
            }, status=404)
            
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed',
            'total': float(cart.total),
            'item_count': cart.item_count
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)