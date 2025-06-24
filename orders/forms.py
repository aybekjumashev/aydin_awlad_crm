# orders/forms.py - TUZATILGAN VERSIYA (O'lchov formasi uchun)

from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.contrib.auth import get_user_model
from .models import Order, OrderItem
from customers.models import Customer

User = get_user_model()


class OrderItemForm(forms.ModelForm):
    """
    Buyurtma elementi formasi - O'lchov uchun
    """
    class Meta:
        model = OrderItem
        fields = [
            'blind_type', 'material', 'installation_type', 'mechanism', 'cornice_type',
            'width', 'height', 'quantity', 'unit_price', 'room_name'
        ]
        widgets = {
            'blind_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'material': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'installation_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'mechanism': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cornice_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'required': True,
                'placeholder': '150'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'required': True,
                'placeholder': '180'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1',
                'required': True
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000',
                'required': True,
                'placeholder': '150000'
            }),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Yotoq xona'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')
        unit_price = cleaned_data.get('unit_price')
        
        if width and width < 10:
            raise forms.ValidationError('Jalyuzi eni kamida 10 sm bo\'lishi kerak')
        
        if height and height < 10:
            raise forms.ValidationError('Jalyuzi bo\'yi kamida 10 sm bo\'lishi kerak')
        
        if unit_price and unit_price < 0:
            raise forms.ValidationError('Narx musbat son bo\'lishi kerak')
        
        return cleaned_data


# ✅ TUZATILDI: Inline formset ishlatish
MeasurementFormSet = inlineformset_factory(
    Order,  # Parent model
    OrderItem,  # Child model
    form=OrderItemForm,
    extra=1,  # Qo'shimcha bo'sh form
    can_delete=True,  # O'chirish imkoniyati
    min_num=1,  # Minimal 1 ta item bo'lishi kerak
    validate_min=True,
    max_num=10  # Maksimal 10 ta item
)


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
        self.fields['customer'].queryset = Customer.objects.exclude(category='inactive')
        self.fields['customer'].empty_label = "Mijozni tanlang"


class MeasurementForm(forms.ModelForm):
    """
    O'lchov olish formasi (Order modelini o'zgartirish uchun)
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


class OrderUpdateForm(forms.ModelForm):
    """
    Buyurtmani yangilash formasi
    """
    class Meta:
        model = Order
        fields = [
            'customer', 'address', 'notes', 'measurement_date', 
            'assigned_measurer', 'assigned_manufacturer', 'assigned_installer'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'assigned_measurer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_installer': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Texnik xodimlarni filtrlash
        self.fields['assigned_measurer'].queryset = User.objects.filter(can_measure=True)
        self.fields['assigned_manufacturer'].queryset = User.objects.filter(can_manufacture=True)
        self.fields['assigned_installer'].queryset = User.objects.filter(can_install=True)
        
        # Bo'sh tanlov qo'shish
        self.fields['assigned_measurer'].empty_label = "O'lchov oluvchini tanlang"
        self.fields['assigned_manufacturer'].empty_label = "Ishlab chiquvchini tanlang"
        self.fields['assigned_installer'].empty_label = "O'rnatuvchini tanlang"


class OrderStatusUpdateForm(forms.ModelForm):
    """
    Buyurtma statusini o'zgartirish formasi
    """
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Foydalanuvchi huquqiga qarab status tanlovlarini cheklash
        if user and hasattr(user, 'is_technical') and user.is_technical:
            allowed_statuses = []
            if user.can_measure:
                allowed_statuses.extend(['measuring', 'processing'])
            if user.can_manufacture:
                allowed_statuses.extend(['processing', 'installing'])
            if user.can_install:
                allowed_statuses.extend(['installing', 'installed'])
            
            self.fields['status'].choices = [
                (key, value) for key, value in Order.STATUS_CHOICES 
                if key in allowed_statuses
            ]


class OrderFilterForm(forms.Form):
    """
    Buyurtmalarni filtrlash formasi
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Qidirish... (mijoz, telefon, buyurtma raqami)'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Barcha holatlar')] + Order.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label="Barcha mijozlar",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(role='technical'),
        required=False,
        empty_label="Barcha xodimlar",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AssignStaffForm(forms.ModelForm):
    """
    Xodimlarni tayinlash formasi
    """
    class Meta:
        model = Order
        fields = ['assigned_measurer', 'assigned_manufacturer', 'assigned_installer', 'measurement_date']
        widgets = {
            'assigned_measurer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_installer': forms.Select(attrs={'class': 'form-select'}),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['assigned_measurer'].queryset = User.objects.filter(can_measure=True, is_active=True)
        self.fields['assigned_manufacturer'].queryset = User.objects.filter(can_manufacture=True, is_active=True)
        self.fields['assigned_installer'].queryset = User.objects.filter(can_install=True, is_active=True)
        
        self.fields['assigned_measurer'].empty_label = "O'lchov oluvchini tanlang"
        self.fields['assigned_manufacturer'].empty_label = "Ishlab chiquvchini tanlang"
        self.fields['assigned_installer'].empty_label = "O'rnatuvchini tanlang"