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


class Task(models.Model):
    """Modelo para armazenar tarefas do usuário"""
    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    completed = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def subtasks_count(self):
        return self.subtasks.count()
    
    @property
    def subtasks_completed(self):
        return self.subtasks.filter(completed=True).count()


class SubTask(models.Model):
    """Modelo para armazenar sub-tarefas de uma tarefa"""
    title = models.CharField(max_length=200)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['completed', 'created_at']
    
    def __str__(self):
        return self.title
    
class Equipe(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Público'),
        ('private', 'Privado'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name="Nome do Grupo")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    privacidade = models.CharField(
        max_length=10, 
        choices=PRIVACY_CHOICES, 
        default='private',
        verbose_name="Privacidade"
    )
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_equipes')
    membros = models.ManyToManyField(User, related_name='equipes', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.nome
