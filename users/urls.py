from django.urls import path
from .views import register_view, login_view,ProfileView,LogoutView,reset_password_confirm,reset_password_request
from . import views
urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('check-auth/', views.check_auth, name='check_auth'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', reset_password_request, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', reset_password_confirm, name='password_reset_confirm'),
]