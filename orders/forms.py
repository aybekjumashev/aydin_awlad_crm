# orders/forms.py - TUZATILGAN VERSIYA

from django import forms
from django.forms import modelformset_factory
from django.contrib.auth import get_user_model
from .models import Order, OrderItem
from customers.models import Customer

User = get_user_model()


class SimpleOrderForm(forms.ModelForm):
    """
    Oddiy buyurtma yaratish formasi
    """
    class Meta:
        model = Order
        fields = ['customer', 'address', 'notes']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Jalyuzi o\'rnatilishi kerak bo\'lgan aniq manzil',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar (ixtiyoriy)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TUZATILDI: is_active o'rniga category ishlatamiz
        self.fields['customer'].queryset = Customer.objects.exclude(category='inactive')
        self.fields['customer'].empty_label = "Mijozni tanlang"


class OrderUpdateForm(forms.ModelForm):
    """
    Buyurtmani yangilash formasi
    """
    class Meta:
        model = Order
        fields = [
            'customer', 'address', 'notes', 'measurement_date', 
            'installation_date', 'assigned_measurer', 'assigned_manufacturer', 
            'assigned_installer'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'installation_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'assigned_measurer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_installer': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # TUZATILDI: is_active o'rniga category ishlatamiz
        self.fields['customer'].queryset = Customer.objects.exclude(category='inactive')
        
        # Texnik xodimlar ro'yxati
        technical_users = User.objects.filter(role='technical', is_active=True)
        
        # O'lchov oluvchilar
        self.fields['assigned_measurer'].queryset = technical_users.filter(can_measure=True)
        self.fields['assigned_measurer'].empty_label = "O'lchov oluvchini tanlang"
        
        # Ishlab chiqaruvchilar
        self.fields['assigned_manufacturer'].queryset = technical_users.filter(can_manufacture=True)
        self.fields['assigned_manufacturer'].empty_label = "Ishlab chiqaruvchini tanlang"
        
        # O'rnatuvchilar
        self.fields['assigned_installer'].queryset = technical_users.filter(can_install=True)
        self.fields['assigned_installer'].empty_label = "O'rnatuvchini tanlang"


# Choices'larni model bilan mos ravishda yangilaymiz
BLIND_TYPE_CHOICES = [
    ('horizontal', 'Gorizontal jalyuzi'),
    ('vertical', 'Vertikal jalyuzi'),
    ('roller', 'Rulon parda'),
    ('roman', 'Rim parda'),
    ('plisse', 'Plisse parda'),
    ('zebra', 'Zebra parda'),
    ('day_night', 'Kun-tun parda'),
]

MATERIAL_CHOICES = [
    ('aluminum', 'Alyuminiy'),
    ('pvc', 'PVC'),
    ('wood', 'Yog\'och'),
    ('fabric', 'Mato'),
    ('bamboo', 'Bambuk'),
    ('polyester', 'Polyester'),
    ('blackout', 'Blackout'),
]

INSTALLATION_TYPE_CHOICES = [
    ('ceiling', 'Shiftga'),
    ('wall', 'Devorga'),
    ('window_frame', 'Deraza romiga'),
    ('niche', 'Tokchaga'),
]

MECHANISM_CHOICES = [
    ('cord', 'Arqon'),
    ('chain', 'Zanjir'),
    ('motor', 'Elektr motor'),
    ('spring', 'Prujina'),
    ('manual', 'Qo\'lda'),
]

CORNICE_TYPE_CHOICES = [
    ('standard', 'Standart'),
    ('decorative', 'Dekorativ'),
    ('hidden', 'Yashirin'),
    ('none', 'Karniz yo\'q'),
]


class OrderItemForm(forms.ModelForm):
    """
    Buyurtma jalyuzilari formasi
    """
    
    class Meta:
        model = OrderItem
        fields = [
            'blind_type', 'width', 'height', 'material', 
            'installation_type', 'mechanism', 'cornice_type',
            'color', 'quantity', 'unit_price_per_sqm', 'room_name'
        ]
        widgets = {
            'blind_type': forms.Select(
                choices=BLIND_TYPE_CHOICES,
                attrs={'class': 'form-select', 'required': True}
            ),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'step': '0.1',
                'placeholder': 'Eni (sm)',
                'required': True
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'step': '0.1',
                'placeholder': 'Bo\'yi (sm)',
                'required': True
            }),
            'material': forms.Select(
                choices=MATERIAL_CHOICES,
                attrs={'class': 'form-select', 'required': True}
            ),
            'installation_type': forms.Select(
                choices=INSTALLATION_TYPE_CHOICES,
                attrs={'class': 'form-select', 'required': True}
            ),
            'mechanism': forms.Select(
                choices=MECHANISM_CHOICES,
                attrs={'class': 'form-select', 'required': True}
            ),
            'cornice_type': forms.Select(
                choices=CORNICE_TYPE_CHOICES,
                attrs={'class': 'form-select'}
            ),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rang yoki kodni kiriting'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1',
                'required': True
            }),
            'unit_price_per_sqm': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Kvadrat metr narxi (so\'m)'
            }),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Xona nomi (masalan: yotoq xona, mehmonxona)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')
        
        if width and width < 10:
            raise forms.ValidationError('Jalyuzi eni kamida 10 sm bo\'lishi kerak')
        
        if height and height < 10:
            raise forms.ValidationError('Jalyuzi bo\'yi kamida 10 sm bo\'lishi kerak')
        
        return cleaned_data


class MeasurementForm(forms.ModelForm):
    """
    O'lchov olish formasi
    """
    class Meta:
        model = Order
        fields = ['measurement_notes', 'address']
        widgets = {
            'measurement_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'O\'lchov jarayonida olingan ma\'lumotlar, qiyinchiliklar va eslatmalar...'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Aniq manzil'
            }),
        }


class OrderFilterForm(forms.Form):
    """
    Buyurtmalarni filtrlash formasi
    """
    STATUS_CHOICES = [('', 'Barcha statuslar')] + Order.STATUS_CHOICES
    
    search = forms.CharField(
        label='Qidiruv',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buyurtma raqami, mijoz ismi yoki telefon...'
        })
    )
    
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    customer = forms.ModelChoiceField(
        label='Mijoz',
        queryset=Customer.objects.exclude(category='inactive'),  # TUZATILDI
        required=False,
        empty_label='Barcha mijozlar',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        label='Sana (dan)',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        label='Sana (gacha)',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        label='Tayinlangan xodim',
        queryset=User.objects.filter(role='technical', is_active=True),
        required=False,
        empty_label='Barcha xodimlar',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AssignStaffForm(forms.ModelForm):
    """
    Xodimlarni tayinlash formasi
    """
    class Meta:
        model = Order
        fields = ['assigned_measurer', 'assigned_manufacturer', 'assigned_installer']
        widgets = {
            'assigned_measurer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_installer': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        technical_users = User.objects.filter(role='technical', is_active=True)
        
        # O'lchov oluvchilar
        self.fields['assigned_measurer'].queryset = technical_users.filter(can_measure=True)
        self.fields['assigned_measurer'].empty_label = "O'lchov oluvchini tanlang"
        
        # Ishlab chiqaruvchilar
        self.fields['assigned_manufacturer'].queryset = technical_users.filter(can_manufacture=True)
        self.fields['assigned_manufacturer'].empty_label = "Ishlab chiqaruvchini tanlang"
        
        # O'rnatuvchilar
        self.fields['assigned_installer'].queryset = technical_users.filter(can_install=True)
        self.fields['assigned_installer'].empty_label = "O'rnatuvchini tanlang"


class OrderStatusUpdateForm(forms.ModelForm):
    """
    Buyurtma statusini yangilash formasi
    """
    class Meta:
        model = Order
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Status o\'zgartirish sababi...'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Foydalanuvchi huquqlariga qarab status tanlovlarini cheklash
        if user and user.role == 'technical':
            # Texnik xodim faqat ma'lum statuslarni o'zgartira oladi
            allowed_statuses = ['measuring', 'processing', 'installing', 'installed']
            choices = [(k, v) for k, v in Order.STATUS_CHOICES if k in allowed_statuses]
            self.fields['status'].choices = choices


# MeasurementFormSet qo'shamiz
MeasurementFormSet = modelformset_factory(
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    max_num=10
)

# OrderStatusUpdateForm qo'shamiz
class OrderStatusUpdateForm(forms.ModelForm):
    """
    Buyurtma statusini yangilash formasi
    """
    class Meta:
        model = Order
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Status o\'zgartirish sababi...'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Foydalanuvchi huquqlariga qarab status tanlovlarini cheklash
        if user and user.role == 'technical':
            # Texnik xodim faqat ma'lum statuslarni o'zgartira oladi
            allowed_statuses = ['measuring', 'processing', 'installing', 'installed']
            choices = [(k, v) for k, v in Order.STATUS_CHOICES if k in allowed_statuses]
            self.fields['status'].choices = choices


# ModelFormSet yaratish
OrderItemFormSet = modelformset_factory(
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    max_num=10
)