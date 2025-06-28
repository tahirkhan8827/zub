
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
import json




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import logging
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from django.contrib.auth import logout
from django.http import JsonResponse

from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.conf import settings

@csrf_exempt
def reset_password_request(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return JsonResponse({'error': 'No user with that email address'}, status=400)
                
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
            
            # Plain text email
            subject = "Password Reset Request"
            message = f"""Hello {user.first_name or 'User'},

You requested a password reset for your account.

Please click this link to reset your password:
{reset_url}

If you didn't request this, please ignore this email.

Thanks,
The Team"""
            
            # Send email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return JsonResponse({'message': 'Password reset email sent'}, status=200)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def reset_password_confirm(request, uidb64, token):
    if request.method == 'POST':
        try:
            # Clean the token in case it has slashes
            clean_token = token.replace('/', '')
            
            try:
                data = json.loads(request.body)
                new_password = data.get('new_password')
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)

            if not new_password:
                return JsonResponse({'error': 'New password is required'}, status=400)

            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return JsonResponse({'error': 'Invalid reset link'}, status=400)

            if not default_token_generator.check_token(user, clean_token):
                return JsonResponse({'error': 'Invalid or expired token'}, status=400)

            if len(new_password) < 8:
                return JsonResponse({'error': 'Password must be at least 8 characters'}, status=400)

            user.set_password(new_password)
            user.save()
            return JsonResponse({'message': 'Password reset successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

class LogoutView(APIView):
    def post(self, request):
        try:
            logout(request)
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def check_auth(request):
    return JsonResponse({
        'isAuthenticated': request.user.is_authenticated
    })

User = get_user_model()
logger = logging.getLogger(__name__)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            serializer = UserSerializer(request.user, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Profile fetch error: {str(e)}")
            return Response(
                {'error': 'Failed to fetch profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        try:
            user = request.user
            data = request.data.copy()
            
            # Handle name splitting
            if 'name' in data:
                name_parts = data['name'].split(' ', 1)
                data['first_name'] = name_parts[0]
                data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
            
            # Remove avatar from data if it's not in request.FILES
            if 'avatar' not in request.FILES and 'avatar' in data:
                del data['avatar']
            
            serializer = UserSerializer(
                user, 
                data=data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                # Handle avatar separately if provided
                if 'avatar' in request.FILES:
                    user.avatar.delete(save=False)  # Delete old avatar first
                    user.avatar = request.FILES['avatar']
                    user.save()
                
                serializer.save()
                return Response(serializer.data)
            
            return Response(
                {'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

@csrf_exempt
def register_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('email')  # Using email as username
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name')
            last_name = data.get('last_name')

            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            return JsonResponse({'message': 'Registration successful'}, status=201)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('email')
            password = data.get('password')

            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return JsonResponse({'message': 'Login successful'}, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)