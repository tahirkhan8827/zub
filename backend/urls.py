
from django.contrib import admin
from django.urls import path,include
from .views import hello_world
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('', include('cart.urls')),
    path('api/', include('users.urls')),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
