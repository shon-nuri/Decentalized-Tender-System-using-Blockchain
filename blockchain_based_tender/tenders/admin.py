from django.contrib import admin
from .models import Tender, Bid

# --- 1. Bid Inline for Tender Admin ---

class BidInline(admin.TabularInline):
    """
    Allows Bid objects to be displayed and edited directly within the Tender's admin page.
    """
    model = Bid
    # Fields to display in the inline table
    fields = ('bidder', 'price', 'proposal', 'quality_score', 'timestamp')
    readonly_fields = ('bidder', 'timestamp')
    extra = 0 # Don't show extra blank forms

# --- 2. Tender Admin Configuration ---

@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Tender model.
    """
    # Fields to display in the list view
    list_display = ('title', 'creator', 'budget', 'deadline', 'status', 'is_expired')
    # Fields to allow searching on
    search_fields = ('title', 'creator__username', 'description')
    # Fields to allow filtering on
    list_filter = ('status', 'deadline', 'created_at')
    
    # Add the BidInline to the Tender detail page
    inlines = [BidInline] 
    
    # Make the creator readonly after creation
    def get_readonly_fields(self, request, obj=None):
        if obj: # obj is not None, so it's an edit
            return self.readonly_fields + ('creator',)
        return self.readonly_fields

# --- 3. Bid Admin Configuration ---

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Bid model.
    """
    # Fields to display in the list view
    list_display = ('tender', 'bidder', 'price', 'quality_score', 'timestamp')
    # Fields to allow searching on
    search_fields = ('tender__title', 'bidder__username', 'proposal')
    # Fields to allow filtering on
    list_filter = ('tender', 'bidder', 'timestamp')
    # Fields that should not be editable after creation
    readonly_fields = ('timestamp',)
    
    # Define the fields shown in the edit form, grouped by fieldset
    fieldsets = (
        (None, {
            'fields': ('tender', 'bidder', 'price')
        }),
        ('Предложение', {
            'fields': ('proposal', 'quality_score'),
        }),
        ('Метаданные', {
            'fields': ('timestamp',),
            'classes': ('collapse',), # Makes this section collapsible
        }),
    )


