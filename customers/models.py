# customers/models.py

from django.db import models
from django.urls import reverse

class Customer(models.Model):
    """
    Mijozlar modeli
    """
    first_name = models.CharField(
        max_length=50,
        verbose_name='Ism'
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name='Familiya'
    )
    phone = models.CharField(
        max_length=15,
        verbose_name='Telefon raqam'
    )
    address = models.TextField(
        verbose_name='Manzil'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Izoh'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Qo\'shilgan sana'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='O\'zgartirilgan sana'
    )
    
    class Meta:
        verbose_name = 'Mijoz'
        verbose_name_plural = 'Mijozlar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_absolute_url(self):
        return reverse('customer_detail', kwargs={'pk': self.pk})
    
    def total_orders(self):
        """Mijozning umumiy buyurtmalari soni"""
        return self.orders.count()
    
    def completed_orders(self):
        """Yakunlangan buyurtmalar soni"""
        return self.orders.filter(status='installed').count()
    
    def total_spent(self):
        """Mijozning umumiy xarajatlari"""
        return sum([order.total_price() for order in self.orders.filter(status='installed')])
    
    def outstanding_balance(self):
        """Qarzdorlik miqdori"""
        total_debt = 0
        for order in self.orders.exclude(status='cancelled'):
            debt = order.remaining_balance()
            if debt > 0:
                total_debt += debt
        return total_debt
    
    def total_advance_paid(self):
        """Umumiy avans to'lovlari"""
        total_advance = 0
        for order in self.orders.exclude(status='cancelled'):
            total_advance += order.total_advance_paid()
        return total_advance