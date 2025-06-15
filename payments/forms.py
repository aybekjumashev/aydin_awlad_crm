# payments/forms.py

from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Payment
from orders.models import Order


class PaymentForm(forms.ModelForm):
    """
    To'lov yaratish/tahrirlash formasi
    """
    
    class Meta:
        model = Payment
        fields = [
            'order', 'payment_type', 'amount', 'payment_method', 
            'receipt_number', 'notes'
        ]
        widgets = {
            'order': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
                'required': True
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kvitansiya yoki chek raqami...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            }),
        }
        labels = {
            'order': 'Buyurtma',
            'payment_type': 'To\'lov turi',
            'amount': 'To\'lov miqdori (so\'m)',
            'payment_method': 'To\'lov usuli',
            'receipt_number': 'Kvitansiya raqami',
            'notes': 'Izohlar',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Faqat bekor qilinmagan buyurtmalarni ko'rsatish
        self.fields['order'].queryset = Order.objects.exclude(
            status='cancelled'
        ).select_related('customer').order_by('-created_at')
        
        # Required field'larni belgilash
        self.fields['order'].required = True
        self.fields['payment_type'].required = True
        self.fields['amount'].required = True
        self.fields['payment_method'].required = True
        self.fields['receipt_number'].required = False
        self.fields['notes'].required = False
        
        # Amount validation
        self.fields['amount'].validators = [MinValueValidator(Decimal('0.01'))]
    
    def clean_amount(self):
        """To'lov miqdorini validatsiya qilish"""
        amount = self.cleaned_data.get('amount')
        order = self.cleaned_data.get('order')
        
        if amount and amount <= 0:
            raise forms.ValidationError('To\'lov miqdori 0 dan katta bo\'lishi kerak')
        
        if order and amount:
            # Buyurtma umumiy narxidan oshmasligi kerak
            total_price = order.total_price()
            if total_price > 0:
                total_paid = order.total_paid()
                
                # Agar bu tahrirlash bo'lsa, joriy to'lovni hisobga olmaslik
                if self.instance.pk:
                    total_paid -= self.instance.amount
                
                remaining = total_price - total_paid
                
                if amount > remaining:
                    raise forms.ValidationError(
                        f'To\'lov miqdori qoldiq summadan ({remaining:,.0f} so\'m) oshmasligi kerak'
                    )
        
        return amount
    
    def clean_receipt_number(self):
        """Kvitansiya raqamini validatsiya qilish"""
        receipt_number = self.cleaned_data.get('receipt_number')
        
        if receipt_number:
            # Takrorlanishni tekshirish (o'zi bundan mustasno)
            existing_payment = Payment.objects.filter(receipt_number=receipt_number)
            if self.instance.pk:
                existing_payment = existing_payment.exclude(pk=self.instance.pk)
            
            if existing_payment.exists():
                raise forms.ValidationError('Bu kvitansiya raqami allaqachon mavjud')
        
        return receipt_number
    
    def clean(self):
        """Umumiy form validatsiyasi"""
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        amount = cleaned_data.get('amount')
        order = cleaned_data.get('order')
        
        # Avans to'lov faqat buyurtma boshida
        if payment_type == 'advance' and order:
            existing_payments = order.payments.filter(is_confirmed=True)
            if self.instance.pk:
                existing_payments = existing_payments.exclude(pk=self.instance.pk)
            
            if existing_payments.exists():
                raise forms.ValidationError(
                    'Bu buyurtmada allaqachon to\'lovlar mavjud. Avans to\'lovni faqat birinchi to\'lov sifatida qo\'shish mumkin.'
                )
        
        # Yakuniy to'lov to'liq to'lanmagan buyurtmalarda
        if payment_type == 'final' and order and amount:
            total_price = order.total_price()
            total_paid = order.total_paid()
            
            if self.instance.pk:
                total_paid -= self.instance.amount
            
            remaining = total_price - total_paid
            
            if amount != remaining:
                raise forms.ValidationError(
                    f'Yakuniy to\'lov qoldiq summaga ({remaining:,.0f} so\'m) teng bo\'lishi kerak'
                )
        
        return cleaned_data


class PaymentSearchForm(forms.Form):
    """
    To'lovlarni qidiruv formasi
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buyurtma raqami, mijoz nomi yoki kvitansiya raqami...',
        }),
        label='Qidiruv'
    )
    
    payment_type = forms.ChoiceField(
        choices=[('', 'Barcha turlar')] + Payment.PAYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='To\'lov turi'
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'Barcha usullar')] + Payment.PAYMENT_METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='To\'lov usuli'
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='Boshlanish sanasi'
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='Tugash sanasi'
    )
    
    confirmed = forms.ChoiceField(
        choices=[
            ('', 'Barcha to\'lovlar'),
            ('yes', 'Tasdiqlangan'),
            ('no', 'Tasdiqlanmagan'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Tasdiqlash holati'
    )