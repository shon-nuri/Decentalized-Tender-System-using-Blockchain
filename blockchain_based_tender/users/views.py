# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .forms import BidderCreationForm, BidderChangeForm, ProfileUpdateForm, PasswordChangeForm
from .models import Bidder
from .serializers import BidderSerializer, BidderProfileUpdateSerializer, ChangePasswordSerializer

# === TEMPLATE VIEWS ===

def register(request):
    """Handles Bidder registration using the custom form (template-based)."""
    if request.method == 'POST':
        form = BidderCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('tender_list')
    else:
        form = BidderCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    """User profile page"""
    return render(request, 'users/profile.html', {
        'user': request.user
    })

@login_required
def profile_update(request):
    """Update user profile information"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'users/profile_update.html', {'form': form})

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})

# === API VIEWS (DRF) ===

class BidderViewSet(viewsets.ModelViewSet):
    queryset = Bidder.objects.all()
    serializer_class = BidderSerializer
    
    def get_permissions(self):
        if self.action == 'list':
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Bidder.objects.all()
        return Bidder.objects.filter(pk=user.pk)
    
    @action(detail=False, methods=['put', 'patch'], serializer_class=BidderProfileUpdateSerializer)
    def update_profile(self, request):
        """Update user profile via API"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], serializer_class=ChangePasswordSerializer)
    def change_password(self, request):
        """Change user password via API"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['Wrong password.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, user)
        
        return Response({'message': 'Password updated successfully.'})
