# customers/forms.py - TO'G'IRLANGAN VERSIYA

from django import forms
from django.core.validators import RegexValidator
from .models import Customer, CustomerPhone, CustomerNote


class CustomerForm(forms.ModelForm):
    """
    Mijoz yaratish/tahrirlash formasi - Yangilangan
    """
    
    phone_validator = RegexValidator(
        regex=r'^\+998\d{9}$',
        message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
    )
    
    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'birth_date', 'category', 
            'phone', 'address', 'notes'
        ]
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
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Tug\'ilgan kun'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
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
            'birth_date': 'Tug\'ilgan kun',
            'category': 'Kategoriya',
            'phone': 'Telefon raqam',
            'address': 'Manzil',
            'notes': 'Izoh',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].validators.append(self.phone_validator)
        
        # Birth_date va category majburiy emas
        self.fields['birth_date'].required = False
        self.fields['notes'].required = False


class CustomerSearchForm(forms.Form):
    """
    Mijozlarni qidirish formasi - Yangilangan
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
    
    category = forms.ChoiceField(
        choices=[('', 'Barcha kategoriyalar')] + Customer.CATEGORY_CHOICES,
        required=False,
        label='Kategoriya',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    has_birthday_soon = forms.BooleanField(
        required=False,
        label='Tez orada tug\'ilgan kun',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Keyingi 30 kun ichida tug\'ilgan kuni bo\'lganlar'
    )


class CustomerPhoneForm(forms.ModelForm):
    """
    Mijoz telefon raqami formasi
    """
    
    class Meta:
        model = CustomerPhone
        fields = ['phone_number', 'phone_type', 'is_primary', 'notes']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998901234567',
                'required': True
            }),
            'phone_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Izoh...'
            }),
        }
        labels = {
            'phone_number': 'Telefon raqam',
            'phone_type': 'Telefon turi',
            'is_primary': 'Asosiy telefon',
            'notes': 'Izoh',
        }


class CustomerNoteForm(forms.ModelForm):
    """
    Mijoz eslatmasi formasi
    """
    
    class Meta:
        model = CustomerNote
        fields = ['note', 'is_important']
        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Eslatma matni...',
                'required': True
            }),
            'is_important': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'note': 'Eslatma',
            'is_important': 'Muhim eslatma',
        }


class PublicCustomerOrderForm(forms.Form):
    """
    Mijoz tomonidan buyurtma berish formasi (public sahifa uchun)
    """
    
    # Asosiy ma'lumotlar
    full_name = forms.CharField(
        max_length=100,
        label='To\'liq ism',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
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
            'class': 'form-control form-control-lg',
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
            'class': 'form-select form-select-lg',
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
            'placeholder': 'To\'liq manzil kiriting...',
            'required': True
        })
    )
    
    # Jalyuzi ma'lumotlari
    blind_type = forms.ChoiceField(
        choices=[
            ('horizontal', 'Gorizontal'),
            ('vertical', 'Vertikal'),
            ('roller', 'Rulon'),
            ('roman', 'Rim'),
        ],
        label='Jalyuzi turi',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        })
    )
    
    urgent = forms.BooleanField(
        required=False,
        label='Shoshilinch buyurtma',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Tezkor o\'lchov olish uchun'
    )