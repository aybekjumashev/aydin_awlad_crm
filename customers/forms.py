# customers/forms.py - TOZALANGAN VERSIYA

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
            'notes': 'Izoh',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].validators.append(self.phone_validator)


class CustomerSearchForm(forms.Form):
    """
    Mijozlarni qidirish formasi
    """
    
    search = forms.CharField(
        max_length=100,
        required=False,
        label='Qidiruv',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ism, telefon yoki manzil bo\'yicha qidiring...',
            'id': 'search-input'
        })
    )


class PublicCustomerOrderForm(forms.Form):
    """
    Mijoz tomonidan buyurtma berish formasi (public sahifa uchun)
    """
    
    # Asosiy ma'lumotlar
    full_name = forms.CharField(
        max_length=100,
        label='To\'liq ism',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'To\'liq ismingizni kiriting...',
            'required': True
        })
    )
    
    phone = forms.CharField(
        max_length=15,
        label='Telefon raqam',
        validators=[
            RegexValidator(
                regex=r'^\+998\d{9}$',
                message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+998901234567',
            'required': True,
            'value': '+998'
        })
    )
    
    address = forms.CharField(
        label='Manzil',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'O\'lchov olinishi kerak bo\'lgan aniq manzil...',
            'required': True
        })
    )
    
    # Jalyuzi ma'lumotlari
    blind_type = forms.ChoiceField(
        choices=[
            ('', 'Jalyuzi turini tanlang...'),
            ('horizontal', 'Gorizontal'),
            ('vertical', 'Vertikal'),
            ('roller', 'Rulon'),
            ('roman', 'Rim'),
            ('pleated', 'Plisse'),
            ('wooden', 'Yog\'och'),
            ('aluminum', 'Alyuminiy'),
        ],
        label='Jalyuzi turi',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    
    room_name = forms.CharField(
        max_length=100,
        label='Xona nomi',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masalan: Yotoq xona, Mehmonxona...'
        })
    )
    
    approximate_size = forms.CharField(
        label='Taxminiy o\'lcham',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masalan: 150x120 sm...'
        })
    )
    
    preferred_time = forms.CharField(
        label='Qulay vaqt',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'O\'lchov olish uchun qulay vaqt...'
        })
    )
    
    notes = forms.CharField(
        label='Qo\'shimcha izoh',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Qo\'shimcha talablar yoki izohlar...'
        })
    )


class QuickOrderForm(forms.Form):
    """
    Tezkor buyurtma berish formasi (mijoz tomonidan)
    """
    
    # Mijoz ma'lumotlari
    customer_name = forms.CharField(
        max_length=100,
        label='To\'liq ism',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ismingiz va familiyangizni kiriting...',
            'required': True
        })
    )
    
    customer_phone = forms.CharField(
        max_length=15,
        label='Telefon raqam',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '+998901234567',
            'required': True,
            'value': '+998'
        })
    )
    
    # Manzil
    address = forms.CharField(
        label='Manzil',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'To\'liq manzil (o\'lchov olish uchun)...',
            'required': True
        })
    )
    
    # Jalyuzi ma'lumotlari
    blind_type = forms.ChoiceField(
        choices=[
            ('', 'Jalyuzi turini tanlang...'),
            ('horizontal', 'Gorizontal'),
            ('vertical', 'Vertikal'),
            ('roller', 'Rulon'),
            ('roman', 'Rim'),
            ('pleated', 'Plisse'),
            ('wooden', 'Yog\'och'),
            ('aluminum', 'Alyuminiy'),
        ],
        label='Jalyuzi turi',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'required': True
        })
    )
    
    room_count = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        label='Xonalar soni',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'min': '1',
            'max': '20'
        })
    )
    
    approximate_size = forms.CharField(
        max_length=100,
        required=False,
        label='Taxminiy o\'lcham',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Masalan: 150x120 sm yoki katta xona...'
        })
    )
    
    preferred_contact_time = forms.CharField(
        max_length=100,
        required=False,
        label='Qulay aloqa vaqti',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Masalan: 9:00-18:00 yoki faqat kechqurun...'
        })
    )
    
    notes = forms.CharField(
        required=False,
        label='Qo\'shimcha ma\'lumot',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Maxsus talablar, rang afzalliklari va h.k...'
        })
    )