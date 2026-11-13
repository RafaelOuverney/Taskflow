import django_filters
from django import forms
from .models import Task, Equipe


class TaskFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Buscar por título...'
        })
    )
    priority = django_filters.ChoiceFilter(
        choices=Task.PRIORITY_CHOICES,
        empty_label='Todas as prioridades',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    completed = django_filters.ChoiceFilter(
        choices=[
            ('', 'Todos os status'),
            ('true', 'Concluídas'),
            ('false', 'Pendentes'),
        ],
        method='filter_completed',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    class Meta:
        model = Task
        fields = ['title', 'priority', 'completed']

    def filter_completed(self, queryset, name, value):
        if value == 'true':
            return queryset.filter(completed=True)
        elif value == 'false':
            return queryset.filter(completed=False)
        return queryset


class EquipeFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(
        lookup_expr='icontains',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Filtrar por nome...'
        })
    )
    privacidade = django_filters.ChoiceFilter(
        choices=Equipe.PRIVACY_CHOICES,
        empty_label='Todas as privacidades',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    class Meta:
        model = Equipe
        fields = ['nome', 'privacidade']

