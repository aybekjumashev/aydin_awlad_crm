# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import RegexValidator
from .models import User


class TechnicianForm(UserCreationForm):
    """
    Texnik xodim yaratish formasi
    """
    
    phone_validator = RegexValidator(
        regex=r'^\+998\d{9}$',
        message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'password1', 'password2', 'can_create_order', 'can_measure', 
            'can_manufacture', 'can_install', 'can_cancel_order'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Foydalanuvchi nomi...',
                'required': True
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ism...',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Familiya...',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998901234567'
            }),
            'can_create_order': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_measure': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_manufacture': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_install': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_cancel_order': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'username': 'Foydalanuvchi nomi',
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'email': 'Email',
            'phone': 'Telefon raqam',
            'password1': 'Parol',
            'password2': 'Parolni tasdiqlash',
            'can_create_order': 'Buyurtma yarata oladi',
            'can_measure': 'O\'lchov olish',
            'can_manufacture': 'Ishlab chiqarish',
            'can_install': 'O\'rnatish',
            'can_cancel_order': 'Buyurtmani bekor qila oladi',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].validators = [self.phone_validator]
        
        # Required fieldlar
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        
        # Password fieldlarni to'g'rilash
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Kamida 8 ta belgi...'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Parolni qayta kiriting...'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'technician'  # Avtomatik texnik xodim
        user.is_staff = False  # Texnik xodim admin panelga kira olmaydi
        
        if commit:
            user.save()
        return user
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Faqat harflar, raqamlar va _ belgisi
            if not username.replace('_', '').isalnum():
                raise forms.ValidationError('Foydalanuvchi nomi faqat harflar, raqamlar va _ belgisidan iborat bo\'lishi kerak')
            
            # Takrorlanishni tekshirish
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('Bu foydalanuvchi nomi allaqachon mavjud')
            
            return username.lower()
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Takrorlanishni tekshirish
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('Bu email allaqachon mavjud')
            return email.lower()
        return email


class TechnicianEditForm(UserChangeForm):
    """
    Texnik xodimni tahrirlash formasi
    """
    
    phone_validator = RegexValidator(
        regex=r'^\+998\d{9}$',
        message='Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak'
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'is_active',
            'can_create_order', 'can_measure', 'can_manufacture', 
            'can_install', 'can_cancel_order'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_create_order': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_measure': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_manufacture': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_install': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'can_cancel_order': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'email': 'Email',
            'phone': 'Telefon raqam',
            'is_active': 'Faol',
            'can_create_order': 'Buyurtma yarata oladi',
            'can_measure': 'O\'lchov olish',
            'can_manufacture': 'Ishlab chiqarish',
            'can_install': 'O\'rnatish',
            'can_cancel_order': 'Buyurtmani bekor qila oladi',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].validators = [self.phone_validator]
        
        # Password fieldini o'chirish (alohida form uchun)
        if 'password' in self.fields:
            del self.fields['password']
        
        # Required fieldlar
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # O'zi bundan mustasno takrorlanishni tekshirish
            existing_user = User.objects.filter(email=email)
            if self.instance.pk:
                existing_user = existing_user.exclude(pk=self.instance.pk)
            
            if existing_user.exists():
                raise forms.ValidationError('Bu email allaqachon mavjud')
            return email.lower()
        return email


class StaffPasswordResetForm(forms.Form):
    """
    Xodim parolini qayta tiklash formasi
    """
    new_password1 = forms.CharField(
        label='Yangi parol',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yangi parolni kiriting...'
        }),
        min_length=8,
        help_text='Kamida 8 ta belgi bo\'lishi kerak'
    )
    new_password2 = forms.CharField(
        label='Yangi parolni tasdiqlash',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yangi parolni qayta kiriting...'
        }),
        min_length=8
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Parollar bir xil emas!')
        
        return cleaned_data