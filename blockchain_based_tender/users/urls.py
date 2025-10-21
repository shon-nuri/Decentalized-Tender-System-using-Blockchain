# users/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter 
from .views import BidderViewSet, profile, profile_update, change_password

router = DefaultRouter()
router.register(r'bidders', BidderViewSet, basename='bidder')

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('profile/update/', profile_update, name='profile_update'),
    path('profile/change-password/', change_password, name='change_password'),
] + router.urls
