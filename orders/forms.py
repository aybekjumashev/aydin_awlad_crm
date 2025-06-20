# orders/forms.py - YANGILANGAN VERSIYA

from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from customers.models import Customer
from accounts.models import User


class SimpleOrderForm(forms.ModelForm):
    """
    Oddiy buyurtma yaratish formasi - Faqat asosiy ma'lumotlar
    """
    
    class Meta:
        model = Order
        fields = ['customer', 'address', 'notes']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'placeholder': 'Mijozni tanlang'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 3,
                'placeholder': 'O\'lchov olinishi kerak bo\'lgan aniq manzil...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Qo\'shimcha izohlar (ixtiyoriy)...'
            })
        }
        labels = {
            'customer': 'Mijoz',
            'address': 'O\'lchov manzili',
            'notes': 'Qo\'shimcha izohlar'
        }
        help_texts = {
            'address': 'Jalyuzi o\'rnatilishi va o\'lchov olinishi kerak bo\'lgan aniq manzil',
            'notes': 'Buyurtma haqida qo\'shimcha ma\'lumotlar'
        }


class OrderUpdateForm(forms.ModelForm):
    """
    Buyurtma tahrirlash formasi - Barcha asosiy maydonlar
    """
    
    class Meta:
        model = Order
        fields = [
            'customer', 'address', 'status', 'notes',
            'assigned_measurer', 'assigned_manufacturer', 'assigned_installer',
            'measurement_date', 'installation_date'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'assigned_measurer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_installer': forms.Select(attrs={'class': 'form-select'}),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'installation_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Faqat tegishli xodimlarni ko'rsatish
        self.fields['assigned_measurer'].queryset = User.objects.filter(
            role='technical', can_measure=True, is_active=True
        )
        self.fields['assigned_manufacturer'].queryset = User.objects.filter(
            role='technical', can_manufacture=True, is_active=True
        )
        self.fields['assigned_installer'].queryset = User.objects.filter(
            role='technical', can_install=True, is_active=True
        )


class OrderStatusForm(forms.ModelForm):
    """
    Buyurtma statusini o'zgartirish formasi
    """
    
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Foydalanuvchi huquqiga qarab status tanlovlarini cheklash
        if user and not user.can_cancel_order:
            # Bekor qilish huquqi yo'q bo'lsa, "cancelled" ni olib tashlash
            choices = [choice for choice in self.fields['status'].choices 
                      if choice[0] != 'cancelled']
            self.fields['status'].choices = choices


class OrderItemForm(forms.ModelForm):
    """
    Buyurtma elementi (jalyuzi) formasi
    """
    
    class Meta:
        model = OrderItem
        fields = [
            'blind_type', 'width', 'height', 'material', 'installation_type',
            'mechanism', 'cornice_type', 'room_name', 'color', 'quantity',
            'unit_price_per_sqm', 'unit_price_total', 'notes'
        ]
        widgets = {
            'blind_type': forms.Select(attrs={'class': 'form-select'}),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'material': forms.Select(attrs={'class': 'form-select'}),
            'installation_type': forms.Select(attrs={'class': 'form-select'}),
            'mechanism': forms.Select(attrs={'class': 'form-select'}),
            'cornice_type': forms.Select(attrs={'class': 'form-select'}),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masalan: Yotoq xona'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masalan: Oq, Jigarrang'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'unit_price_per_sqm': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'unit_price_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            }),
        }
        labels = {
            'blind_type': 'Jalyuzi turi',
            'width': 'Eni (sm)',
            'height': 'Bo\'yi (sm)',
            'material': 'Material',
            'installation_type': 'O\'rnatish turi',
            'mechanism': 'Mexanizm',
            'cornice_type': 'Karniz turi',
            'room_name': 'Xona nomi',
            'color': 'Rang',
            'quantity': 'Donasi',
            'unit_price_per_sqm': 'Birlik narxi (m² uchun)',
            'unit_price_total': 'Birlik narxi (so\'m)',
            'notes': 'Izoh',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ikkala narx maydoni ham majburiy emas - kamida bittasi to'ldirilishi kerak
        self.fields['unit_price_per_sqm'].required = False
        self.fields['unit_price_total'].required = False
    
    def clean(self):
        """
        Validatsiya: kamida bitta narx maydoni to'ldirilishi kerak
        """
        cleaned_data = super().clean()
        unit_price_per_sqm = cleaned_data.get('unit_price_per_sqm')
        unit_price_total = cleaned_data.get('unit_price_total')
        
        if not unit_price_per_sqm and not unit_price_total:
            raise forms.ValidationError(
                'Kamida bitta narx maydoni to\'ldirilishi kerak: '
                'yoki "m² uchun narx" yoki "umumiy narx"'
            )
        
        return cleaned_data


# Inline formset buyurtma elementlari uchun
OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,  # 1 ta bo'sh forma
    min_num=0,  # Oddiy buyurtmada jalyuzi majburiy emas
    max_num=20,  # Maksimum 20 ta jalyuzi
    can_delete=True,
    validate_min=False,  # O'lchov olish jarayonida qo'shiladi
    validate_max=True
)

# O'lchov olish uchun alohida formset (kamida 1 ta jalyuzi majburiy)
MeasurementFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=1,
    min_num=1,  # Kamida 1 ta jalyuzi majburiy
    max_num=20,
    can_delete=True,
    validate_min=True,
    validate_max=True
)


class OrderFilterForm(forms.Form):
    """
    Buyurtmalarni filtrlash formasi
    """
    
    search = forms.CharField(
        max_length=100,
        required=False,
        label='Qidiruv',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buyurtma raqami, mijoz ismi...',
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Barcha holatlar')] + Order.STATUS_CHOICES,
        required=False,
        label='Holat',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        label='Mijoz',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        label='Sanadan',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Sanagacha', 
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(role='technical'),
        required=False,
        label='Tayinlangan xodim',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class AssignStaffForm(forms.ModelForm):
    """
    Xodim tayinlash formasi
    """
    
    class Meta:
        model = Order
        fields = ['assigned_measurer', 'assigned_manufacturer', 'assigned_installer']
        widgets = {
            'assigned_measurer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'assigned_installer': forms.Select(attrs={'class': 'form-select'})
        }
        labels = {
            'assigned_measurer': 'O\'lchov oluvchi',
            'assigned_manufacturer': 'Ishlab chiquvchi',
            'assigned_installer': 'O\'rnatuvchi'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Faqat tegishli xodimlarni ko'rsatish
        self.fields['assigned_measurer'].queryset = User.objects.filter(
            role='technical', can_measure=True, is_active=True
        )
        self.fields['assigned_measurer'].empty_label = "Tayinlanmagan"
        
        self.fields['assigned_manufacturer'].queryset = User.objects.filter(
            role='technical', can_manufacture=True, is_active=True
        )
        self.fields['assigned_manufacturer'].empty_label = "Tayinlanmagan"
        
        self.fields['assigned_installer'].queryset = User.objects.filter(
            role='technical', can_install=True, is_active=True
        )
        self.fields['assigned_installer'].empty_label = "Tayinlanmagan"