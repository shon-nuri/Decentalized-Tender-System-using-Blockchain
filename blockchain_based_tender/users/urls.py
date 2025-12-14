# users/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter 
from .views import (
    BidderViewSet, profile, profile_update, change_password,
    mfa_setup, mfa_verify, mfa_disable
)

router = DefaultRouter()
router.register(r'bidders', BidderViewSet, basename='bidder')

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('profile/update/', profile_update, name='profile_update'),
    path('profile/change-password/', change_password, name='change_password'),
    path('mfa/setup/', mfa_setup, name='mfa_setup'),
    path('mfa/verify/', mfa_verify, name='mfa_verify'),
    path('mfa/disable/', mfa_disable, name='mfa_disable'),
] + router.urls
