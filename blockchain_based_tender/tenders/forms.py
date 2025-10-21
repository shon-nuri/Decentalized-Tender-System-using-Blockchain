from django import forms
from .models import Tender, Bid

class TenderForm(forms.ModelForm):
    # Set the deadline widget for better user experience
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Срок подачи заявок"
    )
    
    class Meta:
        model = Tender
        # Fields the owner is allowed to change
        fields = ['title', 'description', 'budget', 'deadline', 'status']
        labels = {
            'title': "Название тендера",
            'description': "Описание",
            'budget': "Бюджет (в валюте)",
            'status': "Статус",
        }


class BidForm(forms.ModelForm):
    price = forms.DecimalField(
        label="Ваша предлагаемая цена",
        max_digits=10, 
        decimal_places=2, 
        min_value=0.01
    )
    
    class Meta:
        model = Bid
        # Only allow users to submit price and proposal/quality
        fields = ['price', 'proposal', 'quality_score']
        labels = {
            'price': "Предлагаемая цена (должна быть ниже бюджета)",
            'proposal': "Ваше предложение и описание проекта",
            'quality_score': "Предварительная оценка качества (опционально, 0-100)",
        }