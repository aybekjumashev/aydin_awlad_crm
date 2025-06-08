# orders/forms.py

from django import forms
from .models import Order, OrderItem
from customers.models import Customer


class OrderForm(forms.ModelForm):
    """
    Buyurtma yaratish/tahrirlash formasi (soddalashtirilgan)
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
                'placeholder': 'O\'lchov va o\'rnatish uchun aniq manzil...',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            }),
        }
        labels = {
            'customer': 'Mijoz',
            'address': 'O\'lchov manzili',
            'notes': 'Izohlar',
        }
    
    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address or not address.strip():
            raise forms.ValidationError('O\'lchov manzili majburiy!')
        return address.strip()


class OrderItemForm(forms.ModelForm):
    """
    Buyurtma elementi (jalyuzi) formasi
    """
    
    class Meta:
        model = OrderItem
        fields = [
            'blind_type', 'width', 'height', 'material', 'installation_type',
            'mechanism_type', 'cornice_type', 'quantity', 'unit_price', 'room_name', 'notes'
        ]
        widgets = {
            'blind_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'sm'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'sm'
            }),
            'material': forms.Select(attrs={
                'class': 'form-select'
            }),
            'installation_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'mechanism_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mexanizm turi...'
            }),
            'cornice_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Karniz turi...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '1000',
                'min': '0',
                'placeholder': 'so\'m'
            }),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Yotoq xona, Mehmonxona...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Qo\'shimcha izohlar...'
            }),
        }
        labels = {
            'blind_type': 'Jalyuzi turi',
            'width': 'Eni (sm)',
            'height': 'Bo\'yi (sm)',
            'material': 'Material',
            'installation_type': 'O\'rnatish turi',
            'mechanism_type': 'Mexanizm turi',
            'cornice_type': 'Karniz turi',
            'quantity': 'Donasi',
            'unit_price': 'Birlik narxi (so\'m)',
            'room_name': 'Xona nomi',
            'notes': 'Izohlar',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        width = cleaned_data.get('width')
        height = cleaned_data.get('height')
        unit_price = cleaned_data.get('unit_price')
        
        # O'lchamlarni tekshirish
        if width and width <= 0:
            self.add_error('width', 'En 0 dan katta bo\'lishi kerak')
        
        if height and height <= 0:
            self.add_error('height', 'Bo\'y 0 dan katta bo\'lishi kerak')
        
        # Narxni tekshirish
        if unit_price and unit_price <= 0:
            self.add_error('unit_price', 'Narx 0 dan katta bo\'lishi kerak')
        
        return cleaned_data


class OrderStatusForm(forms.Form):
    """
    Buyurtma statusini yangilash formasi
    """
    status = forms.ChoiceField(
        choices=Order.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Yangi status'
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Status o\'zgartirish sababi yoki izohlar...'
        }),
        label='Izohlar',
        required=False
    )