# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

class Bidder(AbstractUser):
    company_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Company name')
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    bidder_role = models.CharField(max_length=50, default='bidder')  # Fixed typo
    email = models.EmailField(unique=True)
    
    # New fields for profile
    address = models.TextField(blank=True, null=True, verbose_name='Company Address')
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name='Tax ID')
    website = models.URLField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, verbose_name='Company Description')
    
    # Digital signature fields (for future implementation)
    digital_signature = models.FileField(
        upload_to='signatures/',
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(['p12', 'pfx'])]
    )
    signature_certificate = models.TextField(blank=True, null=True)  # Store certificate info

    USERNAME_FIELD = 'email'  # Fixed typo
    REQUIRED_FIELDS = ['username']

    # --- MFA (TOTP) fields ---
    otp_secret = models.CharField(max_length=64, blank=True, null=True, help_text='Base32 secret for TOTP')
    mfa_enabled = models.BooleanField(default=False, help_text='Whether user has MFA enabled')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='bidder_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='bidder_permission_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username
    
    def get_won_tenders(self):
        """Get all tenders won by this user"""
        from tenders.models import Tender
        return Tender.objects.filter(
            awarded_bid__bidder=self,
            status='awarded'
        )
    
    def get_active_bids(self):
        """Get all active bids by this user"""
        from tenders.models import Bid
        return Bid.objects.filter(
            bidder=self,
            tender__status='active'
        )
    
    def generate_totp_secret(self):
        """Generate and store a new base32 secret for TOTP."""
        try:
            import pyotp
        except Exception:
            return None
        secret = pyotp.random_base32()
        self.otp_secret = secret
        self.save(update_fields=['otp_secret'])
        return secret

    def get_totp_uri(self, issuer_name='BlockchainTender'):
        """Return provisioning URI for authenticator apps."""
        try:
            import pyotp
        except Exception:
            return None
        if not self.otp_secret:
            return None
        return pyotp.totp.TOTP(self.otp_secret).provisioning_uri(name=self.email or self.username, issuer_name=issuer_name)

