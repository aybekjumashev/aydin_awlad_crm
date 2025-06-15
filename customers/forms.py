# customers/forms.py

from django import forms
from django.core.validators import RegexValidator
from .models import Customer


class CustomerForm(forms.ModelForm):
    """
    Mijoz yaratish/tahrirlash formasi
    """
    
    phone_validator = RegexValidator(
        regex=r'^\+998\d{9}$',
        message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
    )
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'address', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mijoz ismi...',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mijoz familiyasi...',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998901234567',
                'required': True,
                'value': '+998'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'To\'liq manzil...',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            }),
        }
        labels = {
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'phone': 'Telefon raqam',
            'address': 'Manzil',
            'notes': 'Izohlar',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].validators = [self.phone_validator]
        
        # Required field'larni belgilash
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True
        self.fields['notes'].required = False
    
    def clean_first_name(self):
        """Ismni validatsiya qilish"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            # Faqat harflar va probel
            if not first_name.replace(' ', '').isalpha():
                raise forms.ValidationError('Ism faqat harflardan iborat bo\'lishi kerak')
            return first_name.strip().title()
        return first_name
    
    def clean_last_name(self):
        """Familiyani validatsiya qilish"""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            # Faqat harflar va probel
            if not last_name.replace(' ', '').isalpha():
                raise forms.ValidationError('Familiya faqat harflardan iborat bo\'lishi kerak')
            return last_name.strip().title()
        return last_name
    
    def clean_phone(self):
        """Telefon raqamini validatsiya qilish"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Faqat raqamlar, + va probel
            phone = phone.replace(' ', '').replace('-', '')
            
            # +998 bilan boshlanishi kerak
            if not phone.startswith('+998'):
                raise forms.ValidationError('Telefon raqam +998 bilan boshlanishi kerak')
            
            # Uzunligi 13 ta belgi bo'lishi kerak
            if len(phone) != 13:
                raise forms.ValidationError('Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak')
            
            # Takrorlanishni tekshirish (o'zi bundan mustasno)
            existing_customer = Customer.objects.filter(phone=phone)
            if self.instance.pk:
                existing_customer = existing_customer.exclude(pk=self.instance.pk)
            
            if existing_customer.exists():
                raise forms.ValidationError('Bu telefon raqam bilan mijoz allaqachon mavjud')
            
            return phone
        return phone
    
    def clean_address(self):
        """Manzilni validatsiya qilish"""
        address = self.cleaned_data.get('address')
        if address:
            address = address.strip()
            if len(address) < 10:
                raise forms.ValidationError('Manzil kamida 10 ta belgidan iborat bo\'lishi kerak')
            return address
        return address


class CustomerSearchForm(forms.Form):
    """
    Mijozlarni qidiruv formasi
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ism, familiya, telefon yoki manzil bo\'yicha qidiring...',
        }),
        label='Qidiruv'
    )
    
    def clean_search(self):
        """Qidiruv so'zini tozalash"""
        search = self.cleaned_data.get('search')
        if search:
            return search.strip()
        return search