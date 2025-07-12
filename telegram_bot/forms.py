# telegram_bot/forms.py

from django import forms
from django.core.validators import RegexValidator
from customers.models import Customer
from orders.models import Order


class TelegramCustomerForm(forms.ModelForm):
    """
    Customer registration/update form for Telegram interface
    """
    
    phone = forms.CharField(
        label='Telefon raqam',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+998901234567',
            'pattern': r'^\+?998\d{9}'
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?998\d{9}',
                message='To\'g\'ri formatda telefon raqam kiriting: +998901234567'
            )
        ]
    )
    
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone', 'address', 'notes']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ismingizni kiriting',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Familiyangizni kiriting',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'To\'liq manzilni kiriting',
                'rows': 3,
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Qo\'shimcha ma\'lumot (ixtiyoriy)',
                'rows': 2
            }),
        }
        labels = {
            'first_name': 'Ism *',
            'last_name': 'Familiya *',
            'phone': 'Telefon raqam *',
            'address': 'Manzil *',
            'notes': 'Qo\'shimcha ma\'lumot'
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Clean phone format
            phone = phone.strip()
            if not phone.startswith('+'):
                if phone.startswith('998'):
                    phone = '+' + phone
                elif phone.startswith('0'):
                    phone = '+998' + phone[1:]
                else:
                    phone = '+998' + phone
        return phone


class TelegramOrderForm(forms.ModelForm):
    """
    Simplified order creation form for Telegram interface
    Faqat asosiy ma'lumotlar - manzil va izohlar
    """
    
    # O'lchov manzili
    measurement_address = forms.CharField(
        label='O\'lchov manzili',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'O\'lchov olinadigan to\'liq manzil (agar mijoz manzilidan farq qilsa)',
            'rows': 3
        }),
        required=False,
        help_text='Agar o\'lchov mijoz manzilida olinsa, bo\'sh qoldiring'
    )
    
    class Meta:
        model = Order
        fields = ['measurement_address', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Buyurtma haqida qo\'shimcha ma\'lumot, istaklar, talablar',
                'rows': 4
            }),
        }
        labels = {
            'measurement_address': 'O\'lchov manzili',
            'notes': 'Izohlar va talablar'
        }
    
    def __init__(self, *args, **kwargs):
        self.customer = kwargs.pop('customer', None)
        super().__init__(*args, **kwargs)
        
        # Agar customer mavjud bo'lsa, measurement_address ni customer address bilan to'ldirish
        if self.customer and not self.initial.get('measurement_address'):
            self.fields['measurement_address'].widget.attrs['placeholder'] = f"Standart: {self.customer.address}"


class QuickOrderForm(forms.Form):
    """
    Juda sodda buyurtma formi tez so'rovlar uchun
    """
    
    full_name = forms.CharField(
        label='To\'liq ism',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ism Familiya',
            'required': True
        })
    )
    
    phone = forms.CharField(
        label='Telefon raqam',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+998901234567',
            'required': True
        }),
        validators=[
            RegexValidator(
                regex=r'^\+?998\d{9}',
                message='To\'g\'ri formatda telefon raqam kiriting'
            )
        ]
    )
    
    address = forms.CharField(
        label='Manzil',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'To\'liq manzil',
            'rows': 2,
            'required': True
        })
    )
    
    measurement_address = forms.CharField(
        label='O\'lchov manzili',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'O\'lchov olinadigan manzil (agar farq qilsa)',
            'rows': 2
        }),
        required=False
    )
    
    description = forms.CharField(
        label='Tavsif va talablar',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Qanday jalyuzi kerak, qayerga, qanday o\'lcham (taxminiy), rang, qo\'shimcha talablar',
            'rows': 4
        }),
        help_text='Barcha ma\'lumotlarni bu yerga yozing - xodimlarimiz batafsil ma\'lumot olish uchun qo\'ng\'iroq qilishadi'
    )