from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, GoogleLoginView, LogoutView,
    ForgotPasswordView, ResetPasswordView, UserProfileView,
    AdminUserManagementView
)

urlpatterns = [
    # Auth flow
    path('register', RegisterView.as_view(), name='auth-register'),
    path('login', LoginView.as_view(), name='auth-login'),
    path('google-login', GoogleLoginView.as_view(), name='auth-google-login'),
    path('logout', LogoutView.as_view(), name='auth-logout'),
    path('forgot-password', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='auth-reset-password'),
    path('token/refresh', TokenRefreshView.as_view(), name='auth-token-refresh'),
    
    # Profile & Admin User Management
    path('profile', UserProfileView.as_view(), name='user-profile'),
    path('admin/users', AdminUserManagementView.as_view(), name='admin-users-list'),
    path('admin/users/<int:pk>', AdminUserManagementView.as_view(), name='admin-users-detail'),
]
