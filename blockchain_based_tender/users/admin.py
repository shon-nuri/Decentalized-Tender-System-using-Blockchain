from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Bidder
from .forms import BidderCreationForm, BidderChangeForm

class BidderAdmin(UserAdmin):
    add_form = BidderCreationForm
    form = BidderChangeForm
    model = Bidder
    list_display = ['username', 'email', 'company_name', 'contact_number', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('company_name',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('company_name',)}),
    )
admin.site.register(Bidder, BidderAdmin)