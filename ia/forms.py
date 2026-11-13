from django import forms
from .models import IAConfig, UserTokenQuota


class IAConfigForm(forms.ModelForm):
    class Meta:
        model = IAConfig
        fields = [
            'provider', 'model_name', 'api_key', 'endpoint_url', 
            'temperature', 'max_tokens', 'system_prompt', 'ativo'
        ]
        widgets = {
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: gemini-2.5-flash'}),
            'api_key': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Chave de API secreta', 'render_value': True}),
            'endpoint_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://api.exemplo.com/v1'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '2'}),
            'max_tokens': forms.NumberInput(attrs={'class': 'form-control', 'step': '128', 'min': '256'}),
            'system_prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserQuotaUpdateForm(forms.ModelForm):
    class Meta:
        model = UserTokenQuota
        fields = ['monthly_limit']
        widgets = {
            'monthly_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '1000', 'step': '5000'})
        }

