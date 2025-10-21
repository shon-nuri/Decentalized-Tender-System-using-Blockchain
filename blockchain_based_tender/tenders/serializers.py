from rest_framework import serializers
from .models import Tender, Bid

class TenderSerializer(serializers.ModelSerializer):
    # Field to show the creator's username (read-only)
    creator_username = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Tender
        fields = [
            'url',
            'id', 
            'creator', 
            'creator_username', 
            'title', 
            'description', 
            'budget', 
            'start_date', 
            'deadline', 
            'status'
        ]
        # 'creator' is set by the view on creation, 'start_date' is auto-added
        read_only_fields = ('creator', 'start_date')

class BidSerializer(serializers.ModelSerializer):
    bidder_username = serializers.ReadOnlyField(source='bidder.username')

    class Meta:
        model = Bid
        fields = [
            'id',
            'tender',
            'bidder',
            'bidder_username',
            'price'
        ]
        read_only_fields = ('bidder')