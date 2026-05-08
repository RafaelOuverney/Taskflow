from django.contrib import admin
from .models import Notebook, Task, SubTask

@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'visibility', 'created_at', 'updated_at')
    list_filter = ('visibility', 'created_at')
    search_fields = ('title', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'owner', 'visibility')
        }),
        ('Conteúdo', {
            'fields': ('content',),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1
    fields = ('title', 'completed')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'priority', 'completed', 'created_at')
    list_filter = ('priority', 'completed', 'created_at')
    search_fields = ('title', 'owner__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SubTaskInline]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'owner', 'priority', 'completed')
        }),
        ('Descrição', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Detalhes', {
            'fields': ('due_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'completed', 'created_at')
    list_filter = ('completed', 'created_at')
    search_fields = ('title', 'task__title')
    readonly_fields = ('created_at', 'updated_at')

