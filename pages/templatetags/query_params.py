from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Substitui ou adiciona parâmetros de query string na URL atual mantendo os demais.
    Uso: <a href="?{% param_replace page=page_obj.next_page_number %}">
    """
    request = context.get('request')
    if not request:
        return ''
    d = request.GET.copy()
    for k, v in kwargs.items():
        if v is not None and v != '':
            d[k] = v
        elif k in d:
            del d[k]
    return d.urlencode()

