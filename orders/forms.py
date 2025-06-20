# orders/forms.py - TO'LIQ VERSIYA

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
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True)
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
        
        # Texnik xodimlarni filtrlash
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


class MeasurementForm(forms.ModelForm):
    """
    O'lchov olish formasi
    """
    class Meta:
        model = Order
        fields = ['measurement_date', 'notes']
        widgets = {
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'O\'lchov jarayonidagi izohlar...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['measurement_date'].required = False
        self.fields['notes'].required = False


class OrderItemForm(forms.ModelForm):
    """
    Jalyuzi (buyurtma elementi) formasi
    """
    class Meta:
        model = OrderItem
        fields = [
            'blind_type', 'width', 'height', 'material', 'color',
            'installation_type', 'mechanism', 'cornice_type', 
            'room_name', 'quantity', 'unit_price_per_sqm', 'unit_price_total'
        ]
        widgets = {
            'blind_type': forms.Select(attrs={'class': 'form-select'}),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'sm'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'sm'
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Material nomi'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rang'
            }),
            'installation_type': forms.Select(attrs={'class': 'form-select'}),
            'mechanism': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mexanizm turi'
            }),
            'cornice_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Karniz turi'
            }),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Xona nomi'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'unit_price_per_sqm': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '1 m² narxi'
            }),
            'unit_price_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Umumiy birlik narxi'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Majburiy maydonlar
        self.fields['blind_type'].required = True
        self.fields['width'].required = True
        self.fields['height'].required = True
        self.fields['quantity'].required = True


class OrderStatusForm(forms.ModelForm):
    """
    Buyurtma statusini o'zgartirish formasi
    """
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'})
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
        queryset=Customer.objects.all(),
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


# Formset yaratish
MeasurementFormSet = modelformset_factory(
    OrderItem,
    form=OrderItemForm,
    extra=1,
    can_delete=True,
    fields=[
        'blind_type', 'width', 'height', 'material', 'color',
        'installation_type', 'mechanism', 'cornice_type', 
        'room_name', 'quantity', 'unit_price_per_sqm', 'unit_price_total'
    ]
)


class QuickPaymentForm(forms.Form):
    """
    Tezkor to'lov formasi (buyurtma sahifasida)
    """
    amount = forms.DecimalField(
        label='To\'lov miqdori',
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'To\'lov miqdori'
        })
    )
    
    payment_method = forms.ChoiceField(
        label='To\'lov usuli',
        choices=[
            ('cash', 'Naqd'),
            ('card', 'Plastik karta'),
            ('transfer', 'Bank o\'tkazmasi'),
            ('other', 'Boshqa')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    notes = forms.CharField(
        label='Izoh',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'To\'lov haqida izoh...'
        })
    )

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        if self.order:
            # Qolgan to'lov miqdorini ko'rsatish
            remaining = self.order.total_amount - self.order.paid_amount
            if remaining > 0:
                self.fields['amount'].widget.attrs['max'] = str(remaining)
                self.fields['amount'].help_text = f"Qolgan to'lov: {remaining:,.0f} so'm"