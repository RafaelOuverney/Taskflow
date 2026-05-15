from django import forms
from django.contrib.auth.models import User
from .models import Equipe

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.Form):
    phone_number = forms.CharField(label='Phone Number', required=False)
    bio = forms.CharField(label='Bio', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    language = forms.ChoiceField(label='Language', choices=[('en', 'English (US)'), ('pt-br', 'Português (BR)')])
    timezone = forms.CharField(label='Timezone', initial='(GMT-03:00) America/Sao_Paulo', required=False)

class SecurityForm(forms.Form):
    current_password = forms.CharField(label='Current Password', widget=forms.PasswordInput)
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

class EquipeForm(forms.ModelForm):
    membros = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple, 
        required=False,
        label="Adicionar Membros (Selecione os usuários que farão parte da equipe)"
    )

    class Meta:
        model = Equipe
        fields = ['nome', 'descricao', 'privacidade', 'membros']