# customers/forms.py - ODDIY VA ISHLAYDIGAN VERSIYA

from django import forms
from django.core.validators import RegexValidator
from .models import Customer, CustomerPhone, CustomerNote


class CustomerForm(forms.ModelForm):
    """
    Mijoz yaratish/tahrirlash formasi - Oddiy va ishonchli versiya
    """
    
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
                'required': True
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
            'phone': 'Asosiy telefon raqam',
            'address': 'Manzil',
            'notes': 'Izoh',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Majburiy maydonlar
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone'].required = True
        self.fields['address'].required = True
        
        # Majburiy bo'lmagan maydonlar
        self.fields['birth_date'].required = False
        self.fields['notes'].required = False
        
        # Telefon validatori
        self.fields['phone'].validators = [
            RegexValidator(
                regex=r'^\+998\d{9}$',
                message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
            )
        ]
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError('Ism kiritish majburiy')
        if len(first_name) < 2:
            raise forms.ValidationError('Ism kamida 2 ta belgidan iborat bo\'lishi kerak')
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise forms.ValidationError('Familiya kiritish majburiy')
        if len(last_name) < 2:
            raise forms.ValidationError('Familiya kamida 2 ta belgidan iborat bo\'lishi kerak')
        return last_name
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError('Telefon raqam kiritish majburiy')
        
        # Telefon raqamni formatlash
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # +998 qo'shish
        if not phone.startswith('+998'):
            if phone.startswith('998'):
                phone = '+' + phone
            elif phone.startswith('8'):
                phone = '+99' + phone
            else:
                phone = '+998' + phone
        
        # Uzunlikni tekshirish
        if len(phone) != 13:
            raise forms.ValidationError('Telefon raqam +998901234567 formatida bo\'lishi kerak')
        
        # Raqamlarni tekshirish
        if not phone[4:].isdigit():
            raise forms.ValidationError('Telefon raqamda faqat raqamlar bo\'lishi kerak')
        
        # Bir xil telefon mavjudligini tekshirish
        existing_customer = Customer.objects.filter(phone=phone)
        if self.instance and self.instance.pk:
            existing_customer = existing_customer.exclude(pk=self.instance.pk)
        
        if existing_customer.exists():
            existing = existing_customer.first()
            raise forms.ValidationError(
                f'Bu telefon raqam {existing.get_full_name()} mijozida mavjud'
            )
        
        return phone
    
    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        if not address:
            raise forms.ValidationError('Manzil kiritish majburiy')
        if len(address) < 10:
            raise forms.ValidationError('Manzil kamida 10 ta belgidan iborat bo\'lishi kerak')
        return address


class CustomerPhoneForm(forms.ModelForm):
    """
    Mijoz qo'shimcha telefon raqami formasi
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone_number'].required = True
        self.fields['notes'].required = False
        
        # Telefon validatori
        self.fields['phone_number'].validators = [
            RegexValidator(
                regex=r'^\+998\d{9}$',
                message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
            )
        ]
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if not phone:
            raise forms.ValidationError('Telefon raqam kiritish majburiy')
        
        # Telefon raqamni formatlash
        phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        if not phone.startswith('+998'):
            if phone.startswith('998'):
                phone = '+' + phone
            elif phone.startswith('8'):
                phone = '+99' + phone
            else:
                phone = '+998' + phone
        
        # Uzunlikni tekshirish
        if len(phone) != 13:
            raise forms.ValidationError('Telefon raqam +998901234567 formatida bo\'lishi kerak')
        
        # Raqamlarni tekshirish
        if not phone[4:].isdigit():
            raise forms.ValidationError('Telefon raqamda faqat raqamlar bo\'lishi kerak')
        
        return phone


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
    
    def clean_note(self):
        note = self.cleaned_data.get('note', '').strip()
        if not note:
            raise forms.ValidationError('Eslatma matni kiritish majburiy')
        if len(note) < 5:
            raise forms.ValidationError('Eslatma kamida 5 ta belgidan iborat bo\'lishi kerak')
        return note


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
    
    category = forms.ChoiceField(
        choices=[('', 'Barcha kategoriyalar')] + Customer.CATEGORY_CHOICES,
        required=False,
        label='Kategoriya',
        widget=forms.Select(attrs={
            'class': 'form-select'
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
    
    notes = forms.CharField(
        label='Qo\'shimcha izoh',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Qo\'shimcha talablar yoki izohlar...'
        })
    )