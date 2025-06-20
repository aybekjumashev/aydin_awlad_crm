# payments/forms.py - YANGI FAYL

from django import forms
from django.core.exceptions import ValidationError
from .models import Payment, PaymentSchedule
from orders.models import Order
from decimal import Decimal


class PaymentForm(forms.ModelForm):
    """
    To'lov qo'shish formasi
    """
    
    class Meta:
        model = Payment
        fields = [
            'payment_type', 'payment_method', 'amount', 
            'payment_date', 'reference_number', 'notes'
        ]
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank ma\'lumotnomasi, karta raqami oxiri...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            })
        }
        labels = {
            'payment_type': 'To\'lov turi',
            'payment_method': 'To\'lov usuli',
            'amount': 'Summa (so\'m)',
            'payment_date': 'To\'lov sanasi',
            'reference_number': 'Ma\'lumotnoma raqami',
            'notes': 'Izohlar'
        }
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        # Default qiymatlar
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['payment_date'].initial = timezone.now()
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if not amount or amount <= 0:
            raise ValidationError('To\'lov summasi 0 dan katta bo\'lishi kerak')
        
        # Agar buyurtma belgilangan bo'lsa, qarzdorlikdan oshmasligi kerak
        if self.order:
            remaining = self.order.remaining_amount
            payment_type = self.cleaned_data.get('payment_type')
            
            if payment_type != 'refund' and amount > remaining + Decimal('1000000'):
                # 1 million so'mgacha ortiqcha to'lovga ruxsat berish
                raise ValidationError(
                    f'To\'lov summasi qarzdorlikdan ({remaining:,.0f} so\'m) '
                    f'juda ko\'p oshmasligi kerak'
                )
        
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        reference_number = cleaned_data.get('reference_number')
        
        # Bank o'tkazmasi yoki karta to'lovi uchun ma'lumotnoma majburiy
        if payment_method in ['transfer', 'card', 'online'] and not reference_number:
            raise ValidationError({
                'reference_number': 'Bu to\'lov usuli uchun ma\'lumotnoma raqami majburiy'
            })
        
        return cleaned_data


class QuickPaymentForm(forms.Form):
    """
    Tezkor to'lov formasi - faqat asosiy maydonlar
    """
    
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Summa (so\'m)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        initial='cash',
        label='To\'lov usuli',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    notes = forms.CharField(
        required=False,
        label='Izoh',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Qo\'shimcha izoh...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        # Buyurtma qarzdorligini ko'rsatish
        if self.order:
            remaining = self.order.remaining_amount
            self.fields['amount'].help_text = f'Qarzdorlik: {remaining:,.0f} so\'m'
            if remaining > 0:
                self.fields['amount'].widget.attrs['value'] = f'{remaining:.2f}'


class PaymentScheduleForm(forms.ModelForm):
    """
    Muddatli to'lov rejasi formasi
    """
    
    class Meta:
        model = PaymentSchedule
        fields = ['installment_number', 'scheduled_amount', 'due_date', 'notes']
        widgets = {
            'installment_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'scheduled_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Izoh...'
            })
        }
        labels = {
            'installment_number': 'To\'lov tartib raqami',
            'scheduled_amount': 'Summa',
            'due_date': 'Muddati',
            'notes': 'Izoh'
        }


class PaymentFilterForm(forms.Form):
    """
    To'lovlarni filtrlash formasi
    """
    
    search = forms.CharField(
        max_length=100,
        required=False,
        label='Qidiruv',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buyurtma raqami, mijoz ismi...'
        })
    )
    
    payment_type = forms.ChoiceField(
        choices=[('', 'Barcha turlar')] + Payment.PAYMENT_TYPE_CHOICES,
        required=False,
        label='To\'lov turi',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    payment_method = forms.ChoiceField(
        choices=[('', 'Barcha usullar')] + Payment.PAYMENT_METHOD_CHOICES,
        required=False,
        label='To\'lov usuli',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Barcha statuslar')] + Payment.STATUS_CHOICES,
        required=False,
        label='Status',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        label='Sanadan',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Sanagacha',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    amount_from = forms.DecimalField(
        required=False,
        label='Summadan',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    
    amount_to = forms.DecimalField(
        required=False,
        label='Summagacha',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )


class RefundForm(forms.Form):
    """
    To'lovni qaytarish formasi
    """
    
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Qaytariladigan summa',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    
    reason = forms.CharField(
        label='Qaytarish sababi',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Qaytarish sababini yozing...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.payment = kwargs.pop('payment', None)
        super().__init__(*args, **kwargs)
        
        if self.payment:
            max_amount = self.payment.amount
            self.fields['amount'].widget.attrs['max'] = f'{max_amount:.2f}'
            self.fields['amount'].help_text = f'Maksimum: {max_amount:,.0f} so\'m'
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if self.payment and amount > self.payment.amount:
            raise ValidationError(
                f'Qaytariladigan summa to\'lov summasidan '
                f'({self.payment.amount:,.0f} so\'m) oshmasligi kerak'
            )
        
        return amount