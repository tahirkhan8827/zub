from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json
from .models import Cart, CartItem
from products.models import Products,Size

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
        items = CartItem.objects.filter(cart=cart).select_related('product', 'size')
        
        cart_items = []
        for item in items:
            # Get the first available image for the product
            first_image = None
            try:
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
                'image': request.build_absolute_uri(first_image.image.url) if first_image and first_image.image else None,
                'color': product_color.color.name if product_color else None
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
        quantity = int(data.get('quantity', 1))
        
        if not size_id:
            return JsonResponse({'status': 'error', 'message': 'Size is required'}, status=400)
            
        try:
            # Get product and size first
            product = Products.objects.get(id=product_id)
            size = Size.objects.get(id=size_id)
            
            # Check stock availability if needed
            # product_size = product.sizes.filter(size=size).first()
            # if product_size and product_size.stock < quantity:
            #     return JsonResponse({'status': 'error', 'message': 'Not enough stock'}, status=400)
            
            # Get or create cart item
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                size=size,
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
        product = Products.objects.get(id=product_id)
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            CartItem.objects.filter(cart=cart, product=product).delete()
        else:
            item = CartItem.objects.get(cart=cart, product=product)
            item.quantity = quantity
            item.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Cart updated',
            'items': [{
                'id': item.id,
                'product_id': item.product.id,
                'quantity': item.quantity,
                'price': float(item.price)
            } for item in cart.items.all()],
            'total': float(cart.total),
            'item_count': cart.item_count
        })
        
    except Products.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
    except CartItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not in cart'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@require_POST
def remove_cart_item(request, product_id):
    """Remove item from cart"""
    try:
        cart = get_or_create_cart(request)
        product = Products.objects.get(id=product_id)
        CartItem.objects.filter(cart=cart, product=product).delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed',
            'total': float(cart.total),
            'item_count': cart.item_count
        })
        
    except Products.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)