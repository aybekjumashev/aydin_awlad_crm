# orders/forms.py

from django import forms
from django.forms import inlineformset_factory
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Order, OrderItem
from customers.models import Customer
from accounts.models import User
from django.db import models


class OrderForm(forms.ModelForm):
    """
    Buyurtma yaratish/tahrirlash formasi - Yangilangan versiya
    """
    
    class Meta:
        model = Order
        fields = [
            'customer', 'status', 'address', 
            'latitude', 'longitude', 'location_accuracy',
            'measurement_date', 'measurement_notes',
            'production_date', 'production_notes',
            'installation_date', 'installation_notes',
            'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'O\'lchov manzili...',
                'required': True
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '41.3111',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '69.2401',
                'step': 'any'
            }),
            'location_accuracy': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'GPS aniqligi (metr)',
                'step': 'any'
            }),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'measurement_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'O\'lchov jarayoni haqida izohlar...'
            }),
            'production_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'production_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ishlab chiqarish jarayoni haqida...'
            }),
            'installation_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'installation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'O\'rnatish jarayoni haqida...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Umumiy izohlar...'
            }),
        }
        labels = {
            'customer': 'Mijoz',
            'status': 'Holat',
            'address': 'O\'lchov manzili',
            'latitude': 'Kenglik (Latitude)',
            'longitude': 'Uzunlik (Longitude)',
            'location_accuracy': 'GPS aniqligi (m)',
            'measurement_date': 'O\'lchov sanasi',
            'measurement_notes': 'O\'lchov izohlari',
            'production_date': 'Ishlab chiqarish sanasi',
            'production_notes': 'Ishlab chiqarish izohlari',
            'installation_date': 'O\'rnatish sanasi',
            'installation_notes': 'O\'rnatish izohlari',
            'notes': 'Umumiy izohlar',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mijozlarni alifbo tartibida saralash
        self.fields['customer'].queryset = Customer.objects.all().order_by('first_name', 'last_name')
        
        # Geo ma'lumotlari majburiy emas
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['location_accuracy'].required = False


class OrderItemForm(forms.ModelForm):
    """
    Buyurtma elementi formasi - Yangilangan versiya (kattalashtirilib)
    """
    
    class Meta:
        model = OrderItem
        fields = [
            'blind_type', 'width', 'height', 'material', 'installation_type',
            'mechanism', 'cornice_type', 'room_name', 'color', 'quantity',
            'unit_price_per_sqm', 'unit_price_total', 'notes'
        ]
        widgets = {
            'blind_type': forms.Select(attrs={
                'class': 'form-select form-select-lg',  # Katta o'lcham
                'required': True
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Eni (sm)',
                'step': '0.1',
                'min': '0.1',
                'required': True
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Bo\'yi (sm)',
                'step': '0.1',
                'min': '0.1',
                'required': True
            }),
            'material': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
            'installation_type': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
            'mechanism': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'cornice_type': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Xona nomi (masalan: Yotoq xona)...'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Rang (masalan: Oq, Qora)...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg text-center',
                'placeholder': '1',
                'min': '1',
                'value': '1',
                'required': True
            }),
            'unit_price_per_sqm': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'unit_price_total': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
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
    min_num=1,  # Kamida 1 ta jalyuzi bo'lishi kerak
    max_num=20,  # Maksimum 20 ta jalyuzi
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
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all().order_by('first_name', 'last_name'),
        required=False,
        label='Mijoz',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class MeasurementForm(forms.ModelForm):
    """
    O'lchov olish formasi (GPS ma'lumotlari bilan)
    """
    
    class Meta:
        model = Order
        fields = [
            'latitude', 'longitude', 'location_accuracy',
            'measurement_date', 'measurement_notes', 'measured_by'
        ]
        widgets = {
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '41.3111',
                'step': 'any',
                'readonly': True  # JavaScript orqali to'ldiriladi
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '69.2401',
                'step': 'any',
                'readonly': True  # JavaScript orqali to'ldiriladi
            }),
            'location_accuracy': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'GPS aniqligi',
                'readonly': True  # JavaScript orqali to'ldiriladi
            }),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'measurement_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'O\'lchov jarayoni haqida batafsil izoh...'
            }),
            'measured_by': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'latitude': 'Kenglik (Latitude)',
            'longitude': 'Uzunlik (Longitude)',
            'location_accuracy': 'GPS aniqligi (m)',
            'measurement_date': 'O\'lchov sanasi',
            'measurement_notes': 'O\'lchov izohlari',
            'measured_by': 'O\'lchov oluvchi',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat texnik xodimlar va adminlar ko'rinadi
        from django.db.models import Q
        self.fields['measured_by'].queryset = User.objects.filter(
            Q(role='technician') | Q(role='admin') | Q(role='manager')
        ).order_by('first_name', 'last_name')


class AreaCalculatorForm(forms.Form):
    """
    Maydon kalkulyatori formasi
    """
    
    width = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Eni (sm)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '0.00',
            'step': '0.1',
            'min': '0.01'
        })
    )
    
    height = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Bo\'yi (sm)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '0.00',
            'step': '0.1',
            'min': '0.01'
        })
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Donasi',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'min': '1',
            'value': '1'
        })
    )
    
    price_per_sqm = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
        required=False,
        label='Narx (m² uchun)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    
    def calculate_results(self):
        """
        Hisoblash natijalari
        """
        if self.is_valid():
            width = self.cleaned_data['width']
            height = self.cleaned_data['height']
            quantity = self.cleaned_data['quantity']
            price_per_sqm = self.cleaned_data.get('price_per_sqm', Decimal('0'))
            
            # Bir dona uchun maydon (m²)
            area_one = (width / 100) * (height / 100)
            
            # Umumiy maydon
            total_area = area_one * quantity
            
            # Umumiy narx
            total_price = total_area * price_per_sqm if price_per_sqm else Decimal('0')
            
            return {
                'area_one_sqm': round(area_one, 4),
                'total_area_sqm': round(total_area, 4),
                'total_price': round(total_price, 2),
                'price_per_unit': round(total_price / quantity, 2) if quantity > 0 and total_price > 0 else Decimal('0')
            }
        return None


class OrderForm(forms.ModelForm):
    """
    Buyurtma yaratish/tahrirlash formasi - Yangilangan versiya
    """
    
    class Meta:
        model = Order
        fields = [
            'customer', 'status', 'address', 
            'latitude', 'longitude', 'location_accuracy',
            'measurement_date', 'measurement_notes',
            'production_date', 'production_notes',
            'installation_date', 'installation_notes',
            'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'O\'lchov manzili...',
                'required': True
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '41.3111',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '69.2401',
                'step': 'any'
            }),
            'location_accuracy': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'GPS aniqligi (metr)',
                'step': 'any'
            }),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'measurement_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'O\'lchov jarayoni haqida izohlar...'
            }),
            'production_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'production_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ishlab chiqarish jarayoni haqida...'
            }),
            'installation_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'installation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'O\'rnatish jarayoni haqida...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Umumiy izohlar...'
            }),
        }
        labels = {
            'customer': 'Mijoz',
            'status': 'Holat',
            'address': 'O\'lchov manzili',
            'latitude': 'Kenglik (Latitude)',
            'longitude': 'Uzunlik (Longitude)',
            'location_accuracy': 'GPS aniqligi (m)',
            'measurement_date': 'O\'lchov sanasi',
            'measurement_notes': 'O\'lchov izohlari',
            'production_date': 'Ishlab chiqarish sanasi',
            'production_notes': 'Ishlab chiqarish izohlari',
            'installation_date': 'O\'rnatish sanasi',
            'installation_notes': 'O\'rnatish izohlari',
            'notes': 'Umumiy izohlar',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mijozlarni alifbo tartibida saralash
        self.fields['customer'].queryset = Customer.objects.all().order_by('first_name', 'last_name')
        
        # Geo ma'lumotlari majburiy emas
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['location_accuracy'].required = False


class OrderItemForm(forms.ModelForm):
    """
    Buyurtma elementi formasi - Yangilangan versiya (kattalashtirilib)
    """
    
    class Meta:
        model = OrderItem
        fields = [
            'blind_type', 'width', 'height', 'material', 'installation_type',
            'mechanism', 'cornice_type', 'room_name', 'color', 'quantity',
            'unit_price_per_sqm', 'unit_price_total', 'notes'
        ]
        widgets = {
            'blind_type': forms.Select(attrs={
                'class': 'form-select form-select-lg',  # Katta o'lcham
                'required': True
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Eni (sm)',
                'step': '0.1',
                'min': '0.1',
                'required': True
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Bo\'yi (sm)',
                'step': '0.1',
                'min': '0.1',
                'required': True
            }),
            'material': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
            'installation_type': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
            'mechanism': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'cornice_type': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'room_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Xona nomi (masalan: Yotoq xona)...'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Rang (masalan: Oq, Qora)...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg text-center',
                'placeholder': '1',
                'min': '1',
                'value': '1',
                'required': True
            }),
            'unit_price_per_sqm': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'unit_price_total': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
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
    min_num=1,  # Kamida 1 ta jalyuzi bo'lishi kerak
    max_num=20,  # Maksimum 20 ta jalyuzi
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
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all().order_by('first_name', 'last_name'),
        required=False,
        label='Mijoz',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class MeasurementForm(forms.ModelForm):
    """
    O'lchov olish formasi (GPS ma'lumotlari bilan)
    """
    
    class Meta:
        model = Order
        fields = [
            'latitude', 'longitude', 'location_accuracy',
            'measurement_date', 'measurement_notes', 'measured_by'
        ]
        widgets = {
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '41.3111',
                'step': 'any',
                'readonly': True  # JavaScript orqali to'ldiriladi
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '69.2401',
                'step': 'any',
                'readonly': True  # JavaScript orqali to'ldiriladi
            }),
            'location_accuracy': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'GPS aniqligi',
                'readonly': True  # JavaScript orqali to'ldiriladi
            }),
            'measurement_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'measurement_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'O\'lchov jarayoni haqida batafsil izoh...'
            }),
            'measured_by': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'latitude': 'Kenglik (Latitude)',
            'longitude': 'Uzunlik (Longitude)',
            'location_accuracy': 'GPS aniqligi (m)',
            'measurement_date': 'O\'lchov sanasi',
            'measurement_notes': 'O\'lchov izohlari',
            'measured_by': 'O\'lchov oluvchi',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat texnik xodimlar va adminlar ko'rinadi
        from accounts.models import User
        self.fields['measured_by'].queryset = User.objects.filter(
            models.Q(role='technician') | models.Q(role='admin') | models.Q(role='manager')
        ).order_by('first_name', 'last_name')


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
        ] + OrderItem.BLIND_TYPE_CHOICES,
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


class AreaCalculatorForm(forms.Form):
    """
    Maydon kalkulyatori formasi
    """
    
    width = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Eni (sm)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '0.00',
            'step': '0.1',
            'min': '0.01'
        })
    )
    
    height = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal('0.01'),
        label='Bo\'yi (sm)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '0.00',
            'step': '0.1',
            'min': '0.01'
        })
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Donasi',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'min': '1',
            'value': '1'
        })
    )
    
    price_per_sqm = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0'),
        required=False,
        label='Narx (m² uchun)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '0.00',
            'step': '0.01'
        })
    )
    
    def calculate_results(self):
        """
        Hisoblash natijalari
        """
        if self.is_valid():
            width = self.cleaned_data['width']
            height = self.cleaned_data['height']
            quantity = self.cleaned_data['quantity']
            price_per_sqm = self.cleaned_data.get('price_per_sqm', Decimal('0'))
            
            # Bir dona uchun maydon (m²)
            area_one = (width / 100) * (height / 100)
            
            # Umumiy maydon
            total_area = area_one * quantity
            
            # Umumiy narx
            total_price = total_area * price_per_sqm if price_per_sqm else Decimal('0')
            
            return {
                'area_one_sqm': round(area_one, 4),
                'total_area_sqm': round(total_area, 4),
                'total_price': round(total_price, 2),
                'price_per_unit': round(total_price / quantity, 2) if quantity > 0 and total_price > 0 else Decimal('0')
            }
        return None