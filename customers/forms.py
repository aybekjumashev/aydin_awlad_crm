# customers/forms.py

from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    """
    Mijoz qo'shish/tahrirlash formasi
    """
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'address', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ism'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Familiya'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998 90 123 45 67'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'To\'liq manzil'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar (ixtiyoriy)'
            }),
        }
        labels = {
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'phone': 'Telefon raqam',
            'address': 'Manzil',
            'notes': 'Izohlar',
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Telefon raqam formatini tekshirish
            import re
            phone_pattern = r'^\+?998\d{9}$|^\d{9}$'
            phone_cleaned = re.sub(r'[^\d+]', '', phone)
            
            if not re.match(phone_pattern, phone_cleaned):
                raise forms.ValidationError('Telefon raqam noto\'g\'ri formatda. Masalan: +998901234567')
            
            return phone_cleaned
        return phone