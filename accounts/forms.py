# accounts/forms.py - YANGI FAYL
# Texnik xodimlar uchun formalar

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import User


class TechnicianForm(UserCreationForm):
    """
    Texnik xodim yaratish formasi
    """
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'specialist_type', 'birth_date', 'hire_date',
            'salary', 'address', 'emergency_contact', 'notes'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Foydalanuvchi nomi'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
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
            'specialist_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Oylik maosh (so\'m)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Yashash manzili'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Favqulodda holat uchun aloqa'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Parol maydonlarini o'zgartirish
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parolni takrorlang'
        })
        
        # Majburiy maydonlar
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['phone'].required = True
        self.fields['specialist_type'].required = True
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'technical'
        
        if commit:
            user.save()
        return user


class TechnicianEditForm(forms.ModelForm):
    """
    Texnik xodim tahrirlash formasi
    """
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'phone', 'specialist_type', 'birth_date', 'hire_date',
            'salary', 'address', 'emergency_contact', 'notes',
            'is_active', 'can_create_order', 'can_measure', 
            'can_manufacture', 'can_install', 'can_cancel_order',
            'can_manage_payments', 'can_view_all_orders'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'specialist_type': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_create_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_measure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manufacture': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_install': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_cancel_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_payments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_all_orders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StaffPasswordResetForm(forms.Form):
    """
    Xodim parolini yangilash formasi
    """
    new_password1 = forms.CharField(
        label='Yangi parol',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yangi parol'
        }),
        min_length=8
    )
    new_password2 = forms.CharField(
        label='Parolni takrorlang',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Yangi parolni takrorlang'
        }),
        min_length=8
    )
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Parollar mos kelmaydi!')
        
        return password2


class TechnicianPermissionForm(forms.ModelForm):
    """
    Texnik xodim huquqlarini boshqarish formasi
    """
    class Meta:
        model = User
        fields = [
            'can_create_order', 'can_measure', 'can_manufacture', 
            'can_install', 'can_cancel_order', 'can_manage_payments',
            'can_view_all_orders'
        ]
        widgets = {
            'can_create_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_measure': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manufacture': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_install': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_cancel_order': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_payments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_all_orders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserLoginForm(forms.Form):
    """
    Foydalanuvchi login formasi
    """
    username = forms.CharField(
        label='Foydalanuvchi nomi',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Foydalanuvchi nomi',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Parol',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol'
        })
    )
    remember_me = forms.BooleanField(
        label='Meni eslab qol',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class TechnicianFilterForm(forms.Form):
    """
    Texnik xodimlarni filtrlash formasi
    """
    SPECIALIST_CHOICES = [('', 'Barchasi')] + User.SPECIALIST_TYPE_CHOICES
    STATUS_CHOICES = [
        ('', 'Barchasi'),
        ('active', 'Faol'),
        ('inactive', 'Nofaol'),
    ]
    
    search = forms.CharField(
        label='Qidiruv',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ism, telefon yoki username bo\'yicha qidiring...'
        })
    )
    specialist_type = forms.ChoiceField(
        label='Mutaxassis turi',
        choices=SPECIALIST_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        label='Holat',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    hire_date_from = forms.DateField(
        label='Ishga qabul qilingan (dan)',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    hire_date_to = forms.DateField(
        label='Ishga qabul qilingan (gacha)',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class TaskFilterForm(forms.Form):
    """
    Vazifalarni filtrlash formasi
    """
    STATUS_CHOICES = [
        ('active', 'Faol vazifalar'),
        ('completed', 'Yakunlangan'),
        ('overdue', 'Kechikkan'),
        ('all', 'Barchasi'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('all', 'Barcha vazifalar'),
        ('measure', 'O\'lchov olish'),
        ('manufacture', 'Ishlab chiqarish'),
        ('install', 'O\'rnatish'),
    ]
    
    status = forms.ChoiceField(
        label='Holat',
        choices=STATUS_CHOICES,
        initial='active',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    task_type = forms.ChoiceField(
        label='Vazifa turi',
        choices=TASK_TYPE_CHOICES,
        initial='all',
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


class WorkReportForm(forms.Form):
    """
    Ish hisoboti formasi (kelajakda ishlatiladi)
    """
    work_date = forms.DateField(
        label='Ish kuni',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    start_time = forms.TimeField(
        label='Boshlanish vaqti',
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    end_time = forms.TimeField(
        label='Tugash vaqti',
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    work_description = forms.CharField(
        label='Ish tavsifi',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Bugun bajariladiagan ishlar haqida batafsil ma\'lumot...'
        })
    )
    issues_encountered = forms.CharField(
        label='Uchragan muammolar',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Agar muammolar uchragan bo\'lsa, bu yerda yozing...'
        })
    )
    materials_used = forms.CharField(
        label='Ishlatilgan materiallar',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ishlatilgan materiallar ro\'yxati...'
        })
    )


class QuickAssignForm(forms.Form):
    """
    Tezkor tayinlash formasi
    """
    def __init__(self, *args, **kwargs):
        order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        # O'lchov oluvchilar
        measurers = User.objects.filter(
            role='technical',
            can_measure=True,
            is_active=True
        )
        self.fields['assigned_measurer'] = forms.ModelChoiceField(
            queryset=measurers,
            required=False,
            empty_label='Tayinlanmagan',
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Ishlab chiqaruvchilar
        manufacturers = User.objects.filter(
            role='technical',
            can_manufacture=True,
            is_active=True
        )
        self.fields['assigned_manufacturer'] = forms.ModelChoiceField(
            queryset=manufacturers,
            required=False,
            empty_label='Tayinlanmagan',
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # O'rnatuvchilar
        installers = User.objects.filter(
            role='technical',
            can_install=True,
            is_active=True
        )
        self.fields['assigned_installer'] = forms.ModelChoiceField(
            queryset=installers,
            required=False,
            empty_label='Tayinlanmagan',
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        
        # Agar buyurtma mavjud bo'lsa, hozirgi tayinlanishlarni ko'rsatish
        if order:
            self.fields['assigned_measurer'].initial = order.assigned_measurer
            self.fields['assigned_manufacturer'].initial = order.assigned_manufacturer
            self.fields['assigned_installer'].initial = order.assigned_installer