import re

from django import forms

from .models import InventoryItem, User


class UserProvisionForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150, label='Sign-in ID')
    employee_code = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=User.Role.choices)
    department = forms.CharField(max_length=80)
    phone = forms.CharField(max_length=30, required=False, label='Extension')
    password = forms.CharField(min_length=8, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, actor=None, **kwargs):
        self.actor = actor
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = User.Role.ADMIN

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not re.match(r'^[A-Za-z0-9._-]{3,150}$', username):
            raise forms.ValidationError('Use at least 3 letters or numbers. Dots, hyphens and underscores are allowed.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('That ID is already in use.')
        return username

    def clean_employee_code(self):
        code = self.cleaned_data.get('employee_code', '').strip().upper()
        if code and User.objects.filter(employee_code__iexact=code).exists():
            raise forms.ValidationError('That employee code is already in use.')
        return code

    def clean_first_name(self):
        return self.cleaned_data['first_name'].strip()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip()

    def clean_department(self):
        return self.cleaned_data['department'].strip()

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            department=data['department'],
            phone=data.get('phone', '').strip(),
            employee_code=data.get('employee_code') or '',
            created_by=self.actor,
        )
        user.set_password(data['password'])
        user.save()
        return user


class PasswordForm(forms.Form):
    password = forms.CharField(min_length=8, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('password') != cleaned.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned


class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['sku', 'name', 'description', 'unit', 'quantity', 'min_quantity', 'location']

    def clean_sku(self):
        return self.cleaned_data['sku'].strip().upper()

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def clean_location(self):
        return self.cleaned_data['location'].strip()
