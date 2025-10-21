from django.db import models
from django.conf import settings 
from django.utils import timezone
import json
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL

class Tender(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('closed', 'Закрыт'),
        ('awarded', 'Награжден'),
        ('cancelled', 'Отменен'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tenders', verbose_name="Создатель", null=True, blank=True)
    title = models.CharField(max_length=200, verbose_name="Название тендера", blank=True, null=True)
    description = models.TextField(verbose_name="Описание", blank=True, null=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Бюджет", blank=True, null=True)
    deadline = models.DateTimeField(verbose_name="Срок подачи заявок", blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Статус", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", blank=True, null=True)
    
    awarded_bid = models.ForeignKey('Bid', on_delete=models.SET_NULL, null=True, blank=True, related_name='tender_award', verbose_name="Выигравшая заявка")

    # --- Цепочка 1 (Локальная цепочка тендера) ---
    blockchain_data = models.TextField(default='[]', verbose_name="Данные локальной блокчейн-цепочки (Биды)", blank=True, null=True)
    
    # --- Цепочка 2 (Глобальная цепочка) ---
    # Хэш, связывающий этот тендер с блоком в Глобальной Цепочке
    global_chain_link_hash = models.CharField(max_length=64, blank=True, null=True, verbose_name="Якорный хэш Глобальной Цепочки")
    # ---------------------------------

    def __str__(self):
        return self.title

    def clean(self):
        if self.deadline <= timezone.now():
            raise ValidationError('Срок подачи заявок должен быть в будущем.')

    def is_expired(self):
        return self.deadline < timezone.now()

    # --- МЕТОДЫ ДЛЯ ЦЕПОЧКИ 1 (Локальная) ---
    def get_blockchain_instance(self):
        """Возвращает экземпляр локальной цепочки, загруженный из blockchain_data."""
        from blockchain.Chain import Blockchain
        
        try:
            chain_list = json.loads(self.blockchain_data)
        except json.JSONDecodeError:
            chain_list = []
        
        # Если данные сохранены, загружаем из них
        if chain_list:
             return Blockchain.load_from_list_of_dicts(chain_list)

        # Иначе, создаем новый экземпляр
        # Для нового экземпляра Chain.py автоматически добавит генезис-блок
        return Blockchain(genesis_data={'message': f'Tender {self.pk} Bids Chain initialized (Chain 1)'})

    def save_blockchain(self, blockchain_instance):
        """Сохраняет экземпляр локальной цепочки обратно в blockchain_data."""
        self.blockchain_data = json.dumps(blockchain_instance.to_list_of_dicts())
        self.save()

    def add_block_to_chain(self, data):
        """Загружает, добавляет блок и сохраняет локальную цепочку."""
        blockchain = self.get_blockchain_instance()
        blockchain.add_block(data)
        self.save_blockchain(blockchain)
        
    def get_local_chain_root_hash(self):
        """Возвращает хэш последнего блока локальной цепочки (для якорения)."""
        blockchain = self.get_blockchain_instance()
        # Возвращаем хэш последнего блока
        return blockchain.chain[-1].hash if blockchain.chain else '0'
    # ---------------------------------

# === NEW MODEL: Bid ===
class Bid(models.Model):
    tender = models.ForeignKey(
        Tender, 
        on_delete=models.CASCADE, 
        related_name='bids',
        verbose_name="Тендер"
    )

    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='placed_bids',
        verbose_name="Участник", 
        null=True,
        blank=True
    )
    # The price offered by the bidder (should generally be lower than the tender's budget)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Предлагаемая цена", blank=True, null=True)
    
    # Textual description of the proposed solution or quality metrics
    proposal = models.TextField(verbose_name="Предложение", blank=True)
    
    # Optional field for quality score (if we use quality-based conditions)
    # You might remove this if you only use price/time.
    quality_score = models.IntegerField(
        null=True, blank=True, 
        verbose_name="Оценка качества (0-100)"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата подачи", blank=True, null=True)

    class Meta:
        verbose_name = "Заявка (Бид)"
        verbose_name_plural = "Заявки (Биды)"
        # Ensure a user can only place one bid per tender (optional, but good practice)
        unique_together = ('tender', 'bidder')
        # We sort by price ascending (lowest bid first)
        ordering = ['price', '-timestamp']

    def __str__(self):
        return f"Bid of {self.price} by {self.bidder.username} for {self.tender.title}"