import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse 
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Tender, Bid 
from .serializers import TenderSerializer, BidSerializer 
from .forms import TenderForm, BidForm 
from .permissions import IsCreatorOrReadOnly
from django.utils import timezone 
from rest_framework import serializers 
from datetime import datetime 
from django.core.exceptions import ValidationError
from django.contrib import messages 
from decimal import Decimal
# --- BLOCKCHAIN INTEGRATION IMPORT ---
from blockchain.Block import Block, serialize_model_data 
from blockchain.GlobalChain import add_tender_event_to_global_chain, get_global_chain_data
# ------------------------------------

class BlockChainJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle non-standard objects in the blockchain chain.
    """
    def default(self, obj):
        # Обработка объектов Block
        if isinstance(obj, Block):
            return obj.to_dict() 

        # Обработка объектов datetime
        if isinstance(obj, datetime) or isinstance(obj, timezone.datetime):
            return obj.isoformat()

        # Обработка Decimal объектов
        if isinstance(obj, Decimal):
            return float(obj)

        # Обработка объектов Tender (для сериализации в локальных цепочках)
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'Tender':
            return {
                'id': obj.id,
                'title': obj.title,
                'creator': obj.creator.username if obj.creator else None,
                'status': obj.status,
                'bid_count': obj.bids.count()
            }

        return json.JSONEncoder.default(self, obj)


# --- DRF ViewSets ---

class TenderViewSet(viewsets.ModelViewSet):
    """
    Provides full CRUD operations for Tender objects via API at /api/tenders/.
    """
    queryset = Tender.objects.all()
    serializer_class = TenderSerializer
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly] 

    def perform_create(self, serializer):
        
        if 'creator' in serializer.validated_data:
            serializer.validated_data.pop('creator')
            
        tender = serializer.save(creator=self.request.user)
        
        # 1. Записываем событие в ЛОКАЛЬНУЮ цепочку (Цепочка 1: Тендер/Биды)
        tender_data_local = serialize_model_data(tender, ['id', 'title', 'budget', 'deadline', 'creator'])
        tender.add_block_to_chain({'action': 'Tender Created (Local)', 'data': tender_data_local})
        
        # 2. Формируем данные для ГЛОБАЛЬНОЙ цепочки (Цепочка 2: Реестр Тендеров)
        tender_data_global = {
            'action': 'Tender Created (Global)',
            'tender_id': tender.pk,
            'title': tender.title,
            # ЯКОРЕНИЕ: Ссылаемся на хэш последнего блока локальной цепочки
            'local_chain_root_hash': tender.get_local_chain_root_hash()
        }
        
        # 3. Добавляем блок в ГЛОБАЛЬНУЮ цепочку и сохраняем ЯКОРНЫЙ ХЭШ
        global_link_hash = add_tender_event_to_global_chain(tender_data_global)
        tender.global_chain_link_hash = global_link_hash
        tender.save()
        
        print(f"Tender {tender.pk} created. Local Root: {tender.get_local_chain_root_hash()[:10]}, Global Link: {global_link_hash[:10]}")

    def perform_destroy(self, instance):
        """Override delete to add blockchain recording."""
        # Check if tender has bids
        if instance.bids.exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete tender with existing bids.")
        
        # Record deletion in blockchain before actual deletion
        tender_data_local = serialize_model_data(instance, ['id', 'title', 'budget', 'deadline', 'creator'])
        instance.add_block_to_chain({'action': 'Tender Deleted (Local)', 'data': tender_data_local})
        
        tender_data_global = {
            'action': 'Tender Deleted (Global)',
            'tender_id': instance.pk,
            'title': instance.title,
            'local_chain_root_hash': instance.get_local_chain_root_hash()
        }
        
        global_link_hash = add_tender_event_to_global_chain(tender_data_global)
        print(f"Tender {instance.pk} deleted via API. Global Link: {global_link_hash[:10]}")
        
        # Perform the actual deletion
        super().perform_destroy(instance)


class BidViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD operations for Bid objects. Users can only create bids.
    """
    queryset = Bid.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        return Bid.objects.all() 

    def perform_create(self, serializer):
        tender = serializer.validated_data.get('tender')
        if not tender or tender.status != 'active' or tender.is_expired():
            raise serializers.ValidationError("Cannot place a bid on an inactive or expired tender.")
            
        if 'bidder' in serializer.validated_data:
            serializer.validated_data.pop('bidder')
            
        if Bid.objects.filter(tender=tender, bidder=self.request.user).exists():
            raise serializers.ValidationError("You have already placed a bid on this tender.")

        new_bid = serializer.save(bidder=self.request.user)
        
        # --- БЛОКЧЕЙН ДЕЙСТВИЕ: ТОЛЬКО ЦЕПОЧКА 1 (Локальная) ---
        bid_data_local = serialize_model_data(new_bid, ['id', 'tender', 'bidder', 'price', 'proposal', 'timestamp'])
        tender.add_block_to_chain({'action': 'Bid Submitted', 'bid_data': bid_data_local})
        print(f"Bid {new_bid.pk} sealed as a block in Tender {tender.pk} local chain (Chain 1).")
        # -------------------------------------------------


# =========================================================
# === AUTOMATION FUNCTIONS: Auto-Close & Winner Decision ===
# =========================================================

def automatic_winner_selection(tender):
    """
    Automates the winner selection process and seals the award decision on both chains.
    """
    if tender.status != 'closed':
        return False
    
    best_bid = tender.bids.order_by('price').first()
    
    if best_bid:
        tender.awarded_bid = best_bid
        tender.status = 'awarded'
        tender.save()
        
        # 1. Записываем событие в ЛОКАЛЬНУЮ цепочку (Цепочка 1: Тендер/Биды)
        award_data_local = {
            'action': 'Tender Awarded (Local)',
            'winner_bid_id': best_bid.pk,
            'final_price': str(best_bid.price),
        }
        tender.add_block_to_chain(award_data_local)
        
        # 2. Формируем данные для ГЛОБАЛЬНОЙ цепочки (Цепочка 2: Реестр Тендеров)
        tender_data_global = {
            'action': 'Tender Awarded (Global)',
            'tender_id': tender.pk,
            'winner': best_bid.bidder.username,
            'final_price': str(best_bid.price),
            # ЯКОРЕНИЕ: Ссылаемся на хэш последнего блока локальной цепочки
            'local_chain_root_hash': tender.get_local_chain_root_hash() 
        }
        
        # 3. Добавляем блок в ГЛОБАЛЬНУЮ цепочку и обновляем ЯКОРНЫЙ ХЭШ
        global_link_hash = add_tender_event_to_global_chain(tender_data_global)
        tender.global_chain_link_hash = global_link_hash
        tender.save()
        
        print(f"Tender {tender.pk} awarded. Local Root: {tender.get_local_chain_root_hash()[:10]}, Global Link: {global_link_hash[:10]}")
        return True
    
    return True


def auto_process_tenders():
    """Checks all active tenders, closes expired ones, and selects winners."""
    
    expired_tenders = Tender.objects.filter(status='active', deadline__lt=timezone.now())
    for tender in expired_tenders:
        tender.status = 'closed'
        tender.save()
        
        # 1. Локальная запись
        tender.add_block_to_chain({'action': 'Tender Closed (Local)', 'reason': 'Deadline Expired'})
        
        # 2. Глобальная запись
        tender_data_global = {
            'action': 'Tender Closed (Global)',
            'tender_id': tender.pk,
            'local_chain_root_hash': tender.get_local_chain_root_hash() 
        }
        global_link_hash = add_tender_event_to_global_chain(tender_data_global)
        tender.global_chain_link_hash = global_link_hash
        tender.save()
        
        print(f"Tender {tender.pk} closed.")
    
    newly_closed_tenders = Tender.objects.filter(status='closed')
    for tender in newly_closed_tenders:
        # Убедимся, что все закрытые тендеры имеют победителей (и якоря)
        automatic_winner_selection(tender)

# =========================================================
# === TEMPLATE VIEWS ===
# =========================================================

@login_required
def tender_list(request):
    """Lists all tenders after running the auto-process functions."""
    auto_process_tenders() 
    tenders = Tender.objects.filter(status__in=['active', 'closed', 'awarded']).order_by('-deadline')
    return render(request, 'tenders/tender_list.html', {'tenders': tenders})


# === TENDER CREATE VIEW ===
@login_required
def tender_create(request):
    """Handles the creation of a new Tender and seals it on both blockchains."""
    if request.method == 'POST':
        form = TenderForm(request.POST)
        if form.is_valid():
            tender = form.save(commit=False)
            tender.creator = request.user 
            tender.save()
            
            # --- БЛОКЧЕЙН ДЕЙСТВИЕ: Запускаем ту же логику, что и в DRF
            tender_data_local = serialize_model_data(tender, ['id', 'title', 'budget', 'deadline', 'creator'])
            tender.add_block_to_chain({'action': 'Tender Created (Local)', 'data': tender_data_local})
            
            tender_data_global = {
                'action': 'Tender Created (Global)',
                'tender_id': tender.pk,
                'title': tender.title,
                'local_chain_root_hash': tender.get_local_chain_root_hash()
            }
            
            global_link_hash = add_tender_event_to_global_chain(tender_data_global)
            tender.global_chain_link_hash = global_link_hash
            tender.save()
            
            print(f"Tender {tender.pk} created via Form. Global Link: {global_link_hash[:10]}")
            
            return redirect('tender_detail', pk=tender.pk)
    else:
        form = TenderForm() 
        
    return render(request, 'tenders/tender_create.html', {'form': form})


@login_required
def tender_detail(request, pk):
    """Shows the detail of one tender, handles editing by creator, and bidding by others."""
    tender = get_object_or_404(Tender, pk=pk)
    
    auto_process_tenders() 
    tender = get_object_or_404(Tender, pk=pk) 
    
    is_creator = (request.user == tender.creator)
    
    # --- TENDER EDITING (CREATOR) ---
    tender_form = TenderForm(instance=tender)
    
    if is_creator and tender.status == 'active': 
        if request.method == 'POST' and 'tender_edit_submit' in request.POST:
            tender_form = TenderForm(request.POST, instance=tender)
            if tender_form.is_valid():
                tender_form.save()
                
                # 1. Локальная запись
                tender_data_local = serialize_model_data(tender, ['id', 'title', 'budget', 'deadline', 'creator', 'status'])
                tender.add_block_to_chain({'action': 'Tender Updated (Local)', 'data': tender_data_local})
                
                # 2. Глобальная запись
                tender_data_global = {
                    'action': 'Tender Updated (Global)',
                    'tender_id': tender.pk,
                    'title': tender.title,
                    'local_chain_root_hash': tender.get_local_chain_root_hash()
                }
                global_link_hash = add_tender_event_to_global_chain(tender_data_global)
                tender.global_chain_link_hash = global_link_hash
                tender.save()
                
                print(f"Tender {tender.pk} updated. Global Link: {global_link_hash[:10]}")
                
                return redirect('tender_detail', pk=tender.pk)
        else:
            tender_form = TenderForm(instance=tender) 
    else:
        tender_form = TenderForm(instance=tender) 


    # --- BIDDING LOGIC (NON-CREATOR) ---
    bid_form = None
    bid_placed = Bid.objects.filter(tender=tender, bidder=request.user).exists()
    
    if tender.status == 'active' and not is_creator:
        if request.method == 'POST' and 'bid_submit' in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                new_bid = bid_form.save(commit=False)
                new_bid.tender = tender
                new_bid.bidder = request.user 
                new_bid.save()
                
                # --- БЛОКЧЕЙН ДЕЙСТВИЕ: ТОЛЬКО ЛОКАЛЬНАЯ ЦЕПОЧКА (Цепочка 1) ---
                bid_data_local = serialize_model_data(new_bid, ['id', 'tender', 'bidder', 'price', 'proposal', 'timestamp'])
                tender.add_block_to_chain({'action': 'Bid Submitted', 'bid_data': bid_data_local})
                print(f"Bid {new_bid.pk} sealed in Tender {tender.pk} local chain.")
                # -------------------------------------------------
                
                return redirect('tender_detail', pk=tender.pk)
        else:
            bid_form = BidForm() 
    
    
    if is_creator or tender.status != 'active':
        bids = Bid.objects.filter(tender=tender).order_by('price')
    else:
        bids = Bid.objects.filter(tender=tender).order_by('timestamp') 
    
    winner_bid = None
    if tender.status == 'awarded' and hasattr(tender, 'awarded_bid'):
        winner_bid = tender.awarded_bid
        
    return render(request, 'tenders/tender_detail.html', {
        'tender': tender,
        'tender_form': tender_form,
        'bids': bids,
        'bid_form': bid_form,
        'is_creator': is_creator,
        'bid_placed': bid_placed,
        'winner_bid': winner_bid, 
    })

@login_required
def tender_delete(request, pk):
    """Allows the creator to delete their tender."""
    tender = get_object_or_404(Tender, pk=pk)
    
    # Check if the current user is the creator
    if request.user != tender.creator:
        return HttpResponseForbidden("You are not allowed to delete this tender.")
    
    # Check if tender can be deleted (only allow deletion if no bids placed)
    if tender.bids.exists():
        messages.error(request, "Cannot delete tender with existing bids.")
        return redirect('tender_detail', pk=tender.pk)
    
    if request.method == 'POST':
        # --- БЛОКЧЕЙН ДЕЙСТВИЕ: Record deletion in both chains ---
        
        # 1. Локальная запись
        tender.add_block_to_chain({'action': 'Tender Deleted (Local)', 'reason': 'Creator deleted tender'})
        
        # 2. Глобальная запись
        tender_data_global = {
            'action': 'Tender Deleted (Global)',
            'tender_id': tender.pk,
            'title': tender.title,
            'local_chain_root_hash': tender.get_local_chain_root_hash()
        }
        global_link_hash = add_tender_event_to_global_chain(tender_data_global)
        
        print(f"Tender {tender.pk} deleted. Global Link: {global_link_hash[:10]}")
        
        # Delete the tender
        tender.delete()
        messages.success(request, "Tender deleted successfully.")
        return redirect('tender_list')
    
    # If GET request, show confirmation page
    return render(request, 'tenders/tender_confirm_delete.html', {'tender': tender})

def blockchain_view(request):
    """
    Отображает страницу визуализатора блокчейна. 
    Показывает ГЛОБАЛЬНУЮ цепочку (Цепочка 2) и ЛОКАЛЬНУЮ цепочку (Цепочка 1)
    самого свежего тендера.
    """
    try:
        tender = Tender.objects.latest('created_at')
        # Локальная цепочка
        local_blockchain_instance = tender.get_blockchain_instance()
        local_chain_data = local_blockchain_instance.chain
        local_chain_title = f"Local Bids Chain (Chain 1) for Tender #{tender.pk} - {tender.title}"
    except Tender.DoesNotExist:
        local_chain_data = []
        local_chain_title = "Local Bids Chain (Chain 1) - No Tenders Found"
        tender = None
        
    # Глобальная цепочка
    global_chain_data = get_global_chain_data()
    
    context = {
        'global_chain_json': json.dumps(global_chain_data, cls=BlockChainJSONEncoder, indent=4),
        'local_chain_json': json.dumps(local_chain_data, cls=BlockChainJSONEncoder, indent=4),
        'tender': tender,
        'local_chain_title': local_chain_title,
        'global_chain_title': "Global Tender Registry (Chain 2) - All Tenders"
    }
    
    return render(request, 'tenders/blockchain_visualizer.html', context)

def debug_blockchain_data(tender):
    """Debug function to see what's actually in the blockchain"""
    blockchain = tender.get_blockchain_instance()
    print(f"\n=== DEBUG Tender {tender.id} - {tender.title} ===")
    print(f"Total blocks: {len(blockchain.chain)}")
    for i, block in enumerate(blockchain.chain):
        print(f"Block {i}: {block.data}")
    print("=== END DEBUG ===\n")


def blockchain_view(request):
    """
    Отображает страницу визуализатора блокчейна. 
    """
    # Глобальная цепочка (все тендеры)
    global_chain_data = get_global_chain_data()
    
    # Get tenders that should have meaningful local chains
    meaningful_tenders = Tender.objects.filter(
        status__in=['active', 'closed', 'awarded']
    ).exclude(blockchain_data='[]').order_by('-created_at')
    
    local_chains = []
    for tender in meaningful_tenders:
        # Debug the blockchain data
        debug_blockchain_data(tender)
        
        local_blockchain_instance = tender.get_blockchain_instance()
        
        # Filter only meaningful blocks (remove system messages)
        meaningful_blocks = []
        for block in local_blockchain_instance.chain:
            data = block.data
            # Skip genesis blocks and system initialization messages
            if (isinstance(data, dict) and 
                data.get('action') in ['Bid Submitted', 'Tender Awarded', 'Tender Created']):
                meaningful_blocks.append(block)
            elif isinstance(data, str) and 'Genesis' not in data and 'initialized' not in data:
                meaningful_blocks.append(block)
        
        if meaningful_blocks:
            local_chains.append({
                'tender': tender,
                'chain_data': meaningful_blocks,
                'title': f"Tender #{tender.pk} - {tender.title}",
                'bid_count': tender.bids.count(),
                'status': tender.status
            })
    
    context = {
        'global_chain_json': json.dumps(global_chain_data, cls=BlockChainJSONEncoder, indent=4),
        'local_chains_json': json.dumps(local_chains, cls=BlockChainJSONEncoder, indent=4),
        'global_chain_title': "Global Tender Registry (Chain 2) - All Tenders",
        'local_chains_count': len(local_chains)
    }
    
    return render(request, 'tenders/blockchain_visualizer.html', context)
