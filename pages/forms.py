from django import forms
from django.contrib.auth.models import User
from .models import Equipe


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primeiro nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seuemail@exemplo.com'}),
        }


class ProfileUpdateForm(forms.Form):
    phone_number = forms.CharField(label='Telefone', required=False, widget=forms.TextInput(attrs={'class': 'form-control mask-phone', 'placeholder': '(00) 00000-0000'}))
    bio = forms.CharField(label='Biografia', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Conte um pouco sobre você...'}), required=False)
    language = forms.ChoiceField(label='Idioma', choices=[('pt-br', 'Português (BR)'), ('en', 'English (US)')], widget=forms.Select(attrs={'class': 'form-select'}))
    timezone = forms.CharField(label='Fuso Horário', initial='(GMT-03:00) America/Sao_Paulo', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class SecurityForm(forms.Form):
    current_password = forms.CharField(label='Senha Atual', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha atual'}))
    new_password = forms.CharField(label='Nova Senha', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo de 8 caracteres'}))
    confirm_password = forms.CharField(label='Confirmar Nova Senha', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita a nova senha'}))


class EquipeForm(forms.ModelForm):
    nome = forms.CharField(
        label="Nome da Equipe",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ex: Squad Frontend, Operações, Design System...'
        })
    )
    descricao = forms.CharField(
        label="Descrição da Equipe",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva os objetivos, papéis e escopo desta equipe...'
        })
    )
    privacidade = forms.ChoiceField(
        label="Privacidade do Grupo",
        choices=Equipe.PRIVACY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    membros = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'member-checkbox'}),
        required=False,
        label="Membros da Equipe"
    )

    class Meta:
        model = Equipe
        fields = ['nome', 'descricao', 'privacidade', 'membros']
