from django.contrib.auth.mixins import UserPassesTestMixin


class GroupRequiredMixin(UserPassesTestMixin):
    group_required = None 

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.groups.filter(name__in=self.group_required).exists()