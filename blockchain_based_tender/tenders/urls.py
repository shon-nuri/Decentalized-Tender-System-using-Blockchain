from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .utils import download_contract

# Router for the Tender API ViewSet 
router = DefaultRouter()
router.register(r'tenders', views.TenderViewSet, basename='tender')

# Template URL patterns
template_urlpatterns = [
    # List all tenders
    path('', views.tender_list, name='tender_list'), 
    
    # Detail/Edit view for a specific tender
    path('<int:pk>/', views.tender_detail, name='tender_detail'),
    
    # Placeholder for creating a new tender
    path('create/', views.tender_create, name='tender_create'), 

    path('<int:pk>/delete/', views.tender_delete, name='tender_delete'),

    path('blockchain/', views.blockchain_view, name='blockchain_view'),

    path('<int:tender_id>/contract/', download_contract, name='download_contract'),
]

# Combine template URLs and API URLs
urlpatterns = template_urlpatterns + router.urls
