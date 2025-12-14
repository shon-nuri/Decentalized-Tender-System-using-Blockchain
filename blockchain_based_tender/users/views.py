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

# MFA imports
import pyotp
import qrcode
import io
import base64
from .forms import TOTPVerifyForm

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


@login_required
def mfa_setup(request):
    """Set up TOTP MFA: show QR and verify initial code."""
    user = request.user
    # Generate secret if not present
    if not user.otp_secret:
        user.generate_totp_secret()

    provisioning_uri = user.get_totp_uri()

    # Generate QR code image
    qr_b64 = None
    if provisioning_uri:
        qr = qrcode.make(provisioning_uri)
        buffered = io.BytesIO()
        qr.save(buffered, format='PNG')
        qr_b64 = base64.b64encode(buffered.getvalue()).decode()

    if request.method == 'POST':
        form = TOTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(code):
                user.mfa_enabled = True
                user.save(update_fields=['mfa_enabled'])
                request.session['mfa_verified'] = True
                messages.success(request, 'MFA enabled successfully.')
                return redirect('profile')
            else:
                messages.error(request, 'Invalid code. Please try again.')
    else:
        form = TOTPVerifyForm()

    return render(request, 'users/mfa_setup.html', {'form': form, 'qr_b64': qr_b64, 'secret': user.otp_secret})


@login_required
def mfa_verify(request):
    """Verify TOTP during login flow when MFA is required."""
    user = request.user
    if request.method == 'POST':
        form = TOTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            totp = pyotp.TOTP(user.otp_secret)
            if totp.verify(code):
                request.session['mfa_verified'] = True
                messages.success(request, 'MFA verification successful.')
                return redirect('tender_list')
            else:
                messages.error(request, 'Invalid code. Try again.')
    else:
        form = TOTPVerifyForm()

    return render(request, 'users/mfa_verify.html', {'form': form})


@login_required
def mfa_disable(request):
    user = request.user
    if request.method == 'POST':
        user.mfa_enabled = False
        user.otp_secret = ''
        user.save(update_fields=['mfa_enabled', 'otp_secret'])
        request.session.pop('mfa_verified', None)
        messages.success(request, 'MFA disabled for your account.')
        return redirect('profile')
    return render(request, 'users/mfa_disable.html')

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
