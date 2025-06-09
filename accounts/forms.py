# accounts/forms.py - mavjud faylga qo'shish

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class TechnicianForm(UserCreationForm):
    """
    Texnik xodim yaratish/tahrirlash formasi
    """
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'password1', 'password2',
                  'can_create_order', 'can_measure', 'can_manufacture', 'can_install', 'can_cancel_order']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Login nomi'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ism'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Familiya'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998901234567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
        }
        labels = {
            'username': 'Login nomi',
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'phone': 'Telefon raqam',
            'email': 'Email',
            'can_create_order': 'Buyurtma yarata oladi',
            'can_measure': 'O\'lchash huquqi',
            'can_manufacture': 'Ishlab chiqarish huquqi',
            'can_install': 'O\'rnatish huquqi',
            'can_cancel_order': 'Bekor qilish huquqi',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Password fieldlarini styling
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Parol'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Parolni tasdiqlang'
        })
        
        # Permission fieldlarini styling
        for field_name in ['can_create_order', 'can_measure', 'can_manufacture', 'can_install', 'can_cancel_order']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-check-input'
            })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'technician'  # Avtomatik texnik xodim sifatida belgilash
        user.is_staff = False  # Admin panelga kirish huquqi yo'q
        if commit:
            user.save()
        return user


class TechnicianEditForm(forms.ModelForm):
    """
    Texnik xodimni tahrirlash formasi (parolsiz)
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email', 'is_active',
                  'can_create_order', 'can_measure', 'can_manufacture', 'can_install', 'can_cancel_order']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ism'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Familiya'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998901234567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'phone': 'Telefon raqam',
            'email': 'Email',
            'is_active': 'Faol',
            'can_create_order': 'Buyurtma yarata oladi',
            'can_measure': 'O\'lchash huquqi',
            'can_manufacture': 'Ishlab chiqarish huquqi',
            'can_install': 'O\'rnatish huquqi',
            'can_cancel_order': 'Bekor qilish huquqi',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permission fieldlarini styling
        for field_name in ['can_create_order', 'can_measure', 'can_manufacture', 'can_install', 'can_cancel_order']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-check-input'
            })


class StaffPasswordResetForm(forms.Form):
    """
    Texnik xodim parolini yangilash formasi
    """
    new_password1 = forms.CharField(
        label='Yangi parol',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yangi parol'
        })
    )
    new_password2 = forms.CharField(
        label='Parolni tasdiqlang',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parolni qayta kiriting'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Parollar mos kelmaydi!')
            
            if len(password1) < 8:
                raise forms.ValidationError('Parol kamida 8 ta belgidan iborat bo\'lishi kerak!')
        
        return cleaned_data