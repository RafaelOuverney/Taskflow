from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class GroupRequiredMixin(UserPassesTestMixin):
    group_required = None 

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.groups.filter(name__in=self.group_required).exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        
        messages.error(self.request, "Acesso negado! Você não tem privilégios de líder para acessar a Análise.")
        return redirect('dashboard')