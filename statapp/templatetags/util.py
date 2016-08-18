from django import template

register = template.Library()

@register.filter
def get_str(value):
    return str(value)
