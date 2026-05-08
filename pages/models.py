from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Notebook(models.Model):
    """Modelo para armazenar cadernos do usuário"""
    VISIBILITY_CHOICES = [
        ('private', 'Privado'),
        ('public', 'Público'),
    ]
    
    title = models.CharField(max_length=200, default='Novo Caderno')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notebooks')
    content = models.TextField(blank=True, default='')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='private')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title
