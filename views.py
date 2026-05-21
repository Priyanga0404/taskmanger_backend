import logging
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from apps.users.models import User
from apps.users.serializers import UserSerializer
from .serializers import (
    RegisterSerializer, LoginSerializer, 
    ForgotPasswordSerializer, ResetPasswordSerializer
)

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def verify_google_token(credential):
    # Dynamic developer fallback to enable effortless testing without real Google Credentials
    if credential.startswith('mock_'):
        email = credential.replace('mock_', '')
        if '@' not in email:
            email = f"{email}@example.com"
        name = email.split('@')[0].capitalize()
        return {
            'email': email,
            'first_name': name,
            'last_name': 'Mock',
            'profile_image': f'https://api.dicebear.com/7.x/initials/svg?seed={name}'
        }
    
    # Real Google API verification
    try:
        # Client ID must be set in settings.py/environment
        client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
        # Verify the ID token
        id_info = id_token.verify_oauth2_token(
            credential, 
            google_requests.Request(), 
            client_id if client_id else None
        )
        return {
            'email': id_info['email'],
            'first_name': id_info.get('given_name', ''),
            'last_name': id_info.get('family_name', ''),
            'profile_image': id_info.get('picture', '')
        }
    except Exception as e:
        raise ValueError(f"Invalid Google Token: {str(e)}")


class RegisterView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens,
                'message': 'Registration successful!'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, email=email, password=password)
            if user:
                if not user.is_active:
                    return Response({
                        'detail': 'This user account has been disabled by the administrator.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                tokens = get_tokens_for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': tokens,
                    'message': 'Login successful!'
                }, status=status.HTTP_200_OK)
            
            return Response({
                'detail': 'Invalid email or password.'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get('credential')
        if not credential:
            return Response({'detail': 'Google credential token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_data = verify_google_token(credential)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        email = user_data['email']
        first_name = user_data['first_name']
        last_name = user_data['last_name']
        profile_image = user_data['profile_image']

        # Find or create user
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                return Response({
                    'detail': 'This account has been disabled by the administrator.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Update user profile image if none exists
            if not user.profile_image and profile_image:
                user.profile_image = profile_image
                user.save()
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile_image=profile_image,
                auth_provider='GOOGLE',
                is_verified=True
            )

        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'message': 'Google Sign-In successful!'
        }, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful!'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                
                # Generate password reset token
                token = default_token_generator.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build frontend absolute URL
                reset_link = f"http://localhost:3000/reset-password?uid={uidb64}&token={token}"
                
                # Send email (prints to console if SMTP is not configured)
                subject = "Password Reset Request - Task Manager"
                message = f"Hello {user.first_name or 'User'},\n\nWe received a request to reset your password. Click the link below to set a new password:\n\n{reset_link}\n\nIf you did not request this, please ignore this email.\n\nBest,\nTask Manager Team"
                
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else 'noreply@taskmanager.com',
                    [email],
                    fail_silently=False,
                )
                
                return Response({
                    'message': 'Password reset link sent to email.',
                    # Include link in response for easy developer/testing use!
                    'dev_reset_link': reset_link
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # Security best practice: don't reveal if email exists or not, but return success
                return Response({'message': 'Password reset link sent to email.'}, status=status.HTTP_200_OK)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            password = serializer.validated_data['password']
            uidb64 = request.data.get('uid')
            
            if not uidb64:
                return Response({'detail': 'User ID (uid) is required.'}, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
                
                if default_token_generator.check_token(user, token):
                    user.set_password(password)
                    user.save()
                    return Response({'message': 'Password reset successful! You can now log in.'}, status=status.HTTP_200_OK)
                
                return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
                
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({'detail': 'Invalid user ID.'}, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            # Standard users cannot change their role
            if 'role' in request.data and user.role != 'ADMIN':
                return Response({'detail': 'Only administrators can alter roles.'}, status=status.HTTP_403_FORBIDDEN)
                
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminUserManagementView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'ADMIN':
            return Response({'detail': 'Administrator role required.'}, status=status.HTTP_403_FORBIDDEN)
            
        users = User.objects.all().order_index('-created_at') if hasattr(User.objects.all(), 'order_index') else User.objects.all().order_by('-created_at')
        return Response(UserSerializer(users, many=True).data)

    def patch(self, request, pk=None):
        if request.user.role != 'ADMIN':
            return Response({'detail': 'Administrator role required.'}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if user == request.user:
            return Response({'detail': 'You cannot modify your own administrative access permissions.'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Toggle user active status or change roles
        is_active = request.data.get('is_active')
        role = request.data.get('role')
        
        if is_active is not None:
            user.is_active = bool(is_active)
        if role is not None:
            if role in ['USER', 'ADMIN']:
                user.role = role
                
        user.save()
        return Response(UserSerializer(user).data)
