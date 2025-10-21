# users/serializers.py
from rest_framework import serializers
from .models import Bidder

class BidderSerializer(serializers.ModelSerializer):
    won_tenders_count = serializers.SerializerMethodField()
    active_bids_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bidder
        fields = [
            'id', 'username', 'email', 'company_name', 'contact_number', 
            'bidder_role', 'address', 'tax_id', 'website', 'bio',
            'won_tenders_count', 'active_bids_count', 'date_joined'
        ]
        read_only_fields = ['date_joined', 'won_tenders_count', 'active_bids_count']
    
    def get_won_tenders_count(self, obj):
        return obj.get_won_tenders().count()
    
    def get_active_bids_count(self, obj):
        return obj.get_active_bids().count()

class BidderProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bidder
        fields = [
            'username', 'company_name', 'contact_number', 'address', 
            'tax_id', 'website', 'bio', 'avatar'
        ]

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return data