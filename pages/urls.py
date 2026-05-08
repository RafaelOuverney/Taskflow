from django.urls import path
from .views import (
    DashboardView, IndexView, LogoutView, RecuperacaoView, CadastroView,
    NotebookListView, NotebookCreateAPI, NotebookSaveAPI, NotebookDeleteAPI, NotebookGetListAPI,
    TasksListView, TaskCreateAPI, TaskUpdateAPI, TaskToggleAPI, TaskDeleteAPI,
    SubTaskCreateAPI, SubTaskToggleAPI, SubTaskDeleteAPI, TasksGetListAPI
)


urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('recuperacao/', RecuperacaoView.as_view(), name='recuperacao'),
    path('cadastro/', CadastroView.as_view(), name='cadastro'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    path('caderno/', NotebookListView.as_view(), name='notebook'),
    path('caderno/<int:notebook_id>/', NotebookListView.as_view(), name='notebook_detail'),
    
    path('api/notebook/create/', NotebookCreateAPI.as_view(), name='notebook_create_api'),
    path('api/notebook/save/', NotebookSaveAPI.as_view(), name='notebook_save_api'),
    path('api/notebook/delete/', NotebookDeleteAPI.as_view(), name='notebook_delete_api'),
    path('api/notebook/list/', NotebookGetListAPI.as_view(), name='notebook_list_api'),
    
    path('tarefas/', TasksListView.as_view(), name='tarefas'),
    
    path('api/task/create/', TaskCreateAPI.as_view(), name='task_create_api'),
    path('api/task/update/', TaskUpdateAPI.as_view(), name='task_update_api'),
    path('api/task/toggle/', TaskToggleAPI.as_view(), name='task_toggle_api'),
    path('api/task/delete/', TaskDeleteAPI.as_view(), name='task_delete_api'),
    path('api/task/list/', TasksGetListAPI.as_view(), name='task_list_api'),
    
    path('api/subtask/create/', SubTaskCreateAPI.as_view(), name='subtask_create_api'),
    path('api/subtask/toggle/', SubTaskToggleAPI.as_view(), name='subtask_toggle_api'),
    path('api/subtask/delete/', SubTaskDeleteAPI.as_view(), name='subtask_delete_api'),
]
