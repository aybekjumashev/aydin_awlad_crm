# payments/forms.py

from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    """
    To'lov qo'shish/tahrirlash formasi
    """
    
    class Meta:
        model = Payment
        fields = [
            'payment_type', 'amount', 'payment_method', 
            'receipt_number', 'notes', 'is_confirmed'
        ]
        widgets = {
            'payment_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1000',
                'min': '1',
                'placeholder': '0'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'receipt_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kvitansiya yoki chek raqami (ixtiyoriy)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            }),
            'is_confirmed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'payment_type': 'To\'lov turi',
            'amount': 'To\'lov miqdori (so\'m)',
            'payment_method': 'To\'lov usuli',
            'receipt_number': 'Kvitansiya/Chek raqami',
            'notes': 'Izohlar',
            'is_confirmed': 'Tasdiqlangan',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agar yangi to'lov bo'lsa, avtomatik tasdiqlash
        if not self.instance.pk:
            self.fields['is_confirmed'].initial = True
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if amount and amount <= 0:
            raise forms.ValidationError('To\'lov miqdori 0 dan katta bo\'lishi kerak')
        
        # Maksimal miqdorni tekshirish (agar order mavjud bo'lsa)
        if hasattr(self, 'order'):
            remaining = self.order.remaining_balance()
            if amount > remaining:
                raise forms.ValidationError(
                    f'To\'lov miqdori qolgan summadan ko\'p bo\'lmasligi kerak: {remaining:,} so\'m'
                )
        
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        amount = cleaned_data.get('amount')
        
        # To'lov turi va miqdor mantiqiy tekshiruvi
        if payment_type and amount:
            if hasattr(self, 'order'):
                order = self.order
                
                # Agar avans to'lov bo'lsa va allaqachon avans mavjud bo'lsa
                if payment_type == 'advance' and order.advance_payments().exists():
                    if not self.instance.pk or self.instance.payment_type != 'advance':
                        self.add_error(
                            'payment_type', 
                            'Bu buyurtma uchun avans to\'lov allaqachon mavjud'
                        )
                
                # Agar yakuniy to'lov bo'lsa, qolgan summa bilan tekshirish
                if payment_type == 'final':
                    remaining = order.remaining_balance()
                    if self.instance.pk:
                        remaining += self.instance.amount  # Hozirgi to'lovni hisobga olish
                    
                    if amount != remaining:
                        self.add_error(
                            'amount',
                            f'Yakuniy to\'lov qolgan summaga teng bo\'lishi kerak: {remaining:,} so\'m'
                        )
        
        return cleaned_data